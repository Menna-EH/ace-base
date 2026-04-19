"""
Hallucination Judge agent for ACE system.
Acts as a gate between Reflector and Curator.
Inspired by G-Eval style evaluation.
"""

import json
from typing import Dict, Any, Tuple, Optional
from ..prompts.judge import JUDGE_PROMPT
from llm import timed_llm_call


class HallucinationJudge:
    """
    Judge agent that checks if reflector insights are
    grounded in the source question and context before
    allowing them to enter the playbook via the Curator.
    """

    def __init__(self, api_client, api_provider, model: str, max_tokens: int = 50):
        self.api_client = api_client
        self.api_provider = api_provider
        self.model = model
        self.max_tokens = max_tokens
        self.blocked_count = 0
        self.passed_count = 0

    def judge(
        self,
        question: str,
        context: str,
        reflection_content: str,
        call_id: str = "judge",
        log_dir: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Judge whether a reflection contains hallucinated insights.

        Returns:
            Tuple of (should_pass, reason)
            - should_pass=True  → grounded, pass to Curator
            - should_pass=False → hallucinated, block it
        """

        # Extract fields from reflection JSON
        key_insight = "(not found)"
        correct_approach = "(not found)"
        reasoning = "(not found)"

        try:
            reflection_json = json.loads(reflection_content)
            key_insight = reflection_json.get("key_insight", "(not found)")
            correct_approach = reflection_json.get("correct_approach", "(not found)")
            reasoning = reflection_json.get("reasoning", "(not found)")
        except (json.JSONDecodeError, AttributeError):
            key_insight = reflection_content[:500]

        # If no meaningful insight found, let it pass
        if key_insight == "(not found)" or len(key_insight.strip()) < 10:
            self.passed_count += 1
            return True, "No insight to judge"

        prompt = JUDGE_PROMPT.format(
            question,
            context[:2000],
            reasoning[:1000],
            key_insight,
            correct_approach
        )

        try:
            response, _ = timed_llm_call(
                self.api_client,
                self.api_provider,
                self.model,
                prompt,
                role="judge",
                call_id=call_id,
                max_tokens=self.max_tokens,
                log_dir=log_dir
            )

            response_clean = response.strip().upper()

            if "YES" in response_clean:
                self.blocked_count += 1
                print(f"🚫 [JUDGE] Hallucination detected — blocking insight from playbook")
                print(f"   Blocked insight: {key_insight[:100]}...")
                return False, f"Hallucination detected"
            else:
                self.passed_count += 1
                print(f"✅ [JUDGE] Insight grounded — passing to Curator")
                return True, "Grounded"

        except Exception as e:
            # Fail open — if judge errors, let it pass
            print(f"⚠️ [JUDGE] Error during judging, failing open: {e}")
            self.passed_count += 1
            return True, f"Judge error: {e}"

    def get_stats(self) -> Dict[str, Any]:
        total = self.blocked_count + self.passed_count
        return {
            "total_judged": total,
            "blocked": self.blocked_count,
            "passed": self.passed_count,
            "block_rate": self.blocked_count / total if total > 0 else 0
        }