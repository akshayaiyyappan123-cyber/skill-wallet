def answer_question(question: str) -> str:
    """
    Build a prompt for the Q&A module.
    """

    return f"""
You are an educational assistant.

Answer the following question
in simple and clear language.

Question:

{question}
"""