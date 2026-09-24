def create_quiz_prompt(text: str) -> str:

    return f"""
Create 3 multiple-choice questions
from the following text.

Each question must have:
- 4 options
- 1 correct answer
- Explanation

Return JSON only.

Text:

{text}
"""