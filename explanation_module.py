def explain_topic(topic: str) -> str:
    """
    Build a simple explanation prompt.
    """

    return f"""
Explain the following topic
in simple language for a beginner.

Topic:

{topic}

Include:
- Definition
- Important points
- Simple example
"""