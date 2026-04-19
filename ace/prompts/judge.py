"""
Hallucination Judge prompt for ACE system.
"""

JUDGE_PROMPT = """You are a hallucination detection judge for a reasoning playbook.

A Reflector agent has analyzed a question and produced the following insight to potentially be added to a strategy playbook.

Your job is to determine whether this insight is factually grounded in the source question and context, or whether it contains hallucinated claims not supported by the evidence.

**Source Question:**
{}

**Source Context:**
{}

**Reflector's Reasoning:**
{}

**Proposed Key Insight to add to playbook:**
{}

**Correct Approach suggested by Reflector:**
{}

Does the proposed key insight contain claims that are NOT supported by the source question and context above? An insight is hallucinated if it introduces facts, formulas, strategies, or steps that cannot be derived from or verified against the source material.

Answer with only one word:
- YES if the insight contains hallucination or unsupported claims
- NO if the insight is factually grounded in the source material

Answer:"""