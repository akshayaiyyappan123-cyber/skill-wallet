import os
import json
import re
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.generativeai as genai


# ============================================================
# BASIC CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

# Get Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Gemini model
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.0-flash"
)

# Create FastAPI application
app = FastAPI(
    title="EduGenie",
    description="Google Gemini Powered Learning Assistant",
    version="1.0.0"
)


# ============================================================
# FRONTEND CONFIGURATION
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


# ============================================================
# GEMINI CONFIGURATION
# ============================================================

model = None

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

    model = genai.GenerativeModel(
        GEMINI_MODEL
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def check_gemini():
    """
    Check whether Gemini API is configured.
    """

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "Gemini API key is missing. "
            "Please create a .env file and add "
            "GEMINI_API_KEY=your_api_key"
        )


def ask_gemini(prompt: str) -> str:
    """
    Send a prompt to Gemini and return the response.
    """

    check_gemini()

    response = model.generate_content(prompt)

    answer = getattr(response, "text", None)

    if not answer:
        raise RuntimeError(
            "Gemini did not return a response."
        )

    return answer.strip()


def clean_json_response(text: str) -> str:
    """
    Remove Markdown code fences from Gemini JSON output.
    """

    text = text.strip()

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```\s*",
        "",
        text
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    return text.strip()


# ============================================================
# HOME PAGE
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request
        }
    )


# ============================================================
# Q&A MODULE
# ============================================================

@app.post("/qa")
async def question_answer(payload: dict):

    question = str(
        payload.get("text", "")
    ).strip()

    if not question:

        return JSONResponse(
            {
                "error": "Please enter a question."
            },
            status_code=400
        )

    prompt = f"""
You are EduGenie, an educational AI assistant.

Answer the student's question accurately.

Use:
- Simple English
- Clear explanation
- Short paragraphs
- Beginner-friendly language

Question:

{question}
"""

    try:

        answer = ask_gemini(prompt)

        return {
            "result": answer
        }

    except Exception as error:

        return JSONResponse(
            {
                "error": str(error)
            },
            status_code=500
        )


# ============================================================
# EXPLANATION MODULE
# ============================================================

@app.post("/explain")
async def explain_topic(payload: dict):

    topic = str(
        payload.get("text", "")
    ).strip()

    if not topic:

        return JSONResponse(
            {
                "error": "Please enter a topic."
            },
            status_code=400
        )

    prompt = f"""
You are EduGenie.

Explain the following topic in very simple language
for a beginner student.

Requirements:

1. Give a simple definition.
2. Explain the important points.
3. Use bullet points where useful.
4. Give a simple example.
5. Avoid complicated technical words.

Topic:

{topic}
"""

    try:

        answer = ask_gemini(prompt)

        return {
            "result": answer
        }

    except Exception as error:

        return JSONResponse(
            {
                "error": str(error)
            },
            status_code=500
        )


# ============================================================
# QUIZ MODULE
# ============================================================

@app.post("/quiz")
async def generate_quiz(payload: dict):

    text = str(
        payload.get("text", "")
    ).strip()

    if not text:

        return JSONResponse(
            {
                "error": "Please enter a topic or passage."
            },
            status_code=400
        )

    prompt = f"""
You are EduGenie.

Create exactly 3 multiple-choice questions
from the educational text below.

Each question must contain:
- One question
- Exactly 4 options
- One correct answer
- A short explanation

Return ONLY valid JSON.

Do not use Markdown.

Use exactly this format:

[
  {{
    "question": "Question here",
    "options": [
      "Option A",
      "Option B",
      "Option C",
      "Option D"
    ],
    "answer": "Option A",
    "explanation": "Short explanation"
  }}
]

Important rules:

- Create exactly 3 questions.
- Every question must have exactly 4 options.
- The answer must exactly match one option.
- Questions must be based on the supplied text.

Educational text:

{text}
"""

    try:

        raw_response = ask_gemini(prompt)

        cleaned_response = clean_json_response(
            raw_response
        )

        quiz = json.loads(
            cleaned_response
        )

        if not isinstance(quiz, list):

            raise ValueError(
                "Quiz response is not a list."
            )

        if len(quiz) != 3:

            raise ValueError(
                "Gemini did not generate exactly 3 questions."
            )

        for question in quiz:

            if not isinstance(
                question,
                dict
            ):

                raise ValueError(
                    "Invalid quiz question."
                )

            required_fields = [
                "question",
                "options",
                "answer",
                "explanation"
            ]

            for field in required_fields:

                if field not in question:

                    raise ValueError(
                        f"Missing field: {field}"
                    )

            if len(question["options"]) != 4:

                raise ValueError(
                    "Each question must have 4 options."
                )

            if (
                question["answer"]
                not in question["options"]
            ):

                raise ValueError(
                    "Correct answer does not match an option."
                )

        return {
            "quiz": quiz
        }

    except Exception as error:

        return JSONResponse(
            {
                "error": str(error)
            },
            status_code=500
        )


# ============================================================
# SUMMARY MODULE
# ============================================================

@app.post("/summarize")
async def summarize_text(payload: dict):

    text = str(
        payload.get("text", "")
    ).strip()

    if not text:

        return JSONResponse(
            {
                "error": "Please enter text to summarize."
            },
            status_code=400
        )

    prompt = f"""
You are EduGenie.

Summarize the following educational text.

Requirements:

- Keep the main ideas.
- Keep important facts.
- Remove unnecessary repetition.
- Use simple English.
- Make it useful for quick revision.
- Do not add information that is not present.

Text:

{text}
"""

    try:

        answer = ask_gemini(prompt)

        return {
            "result": answer
        }

    except Exception as error:

        return JSONResponse(
            {
                "error": str(error)
            },
            status_code=500
        )


# ============================================================
# LEARNING PATH MODULE
# ============================================================

@app.post("/learn/recommendations")
async def learning_path(payload: dict):

    topic = str(
        payload.get("text", "")
    ).strip()

    if not topic:

        return JSONResponse(
            {
                "error": "Please enter a topic."
            },
            status_code=400
        )

    prompt = f"""
You are EduGenie, a personalized learning assistant.

Create a learning path for the following topic:

{topic}

Organize the learning path into:

1. Beginner level
2. Intermediate level
3. Advanced level

For every level provide:

- Topics to learn
- Simple practice activities
- Suggested resource types
- What the student should be able to do after learning

Keep the plan practical and easy for a student to follow.
"""

    try:

        answer = ask_gemini(prompt)

        return {
            "result": answer
        }

    except Exception as error:

        return JSONResponse(
            {
                "error": str(error)
            },
            status_code=500
        )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health_check():

    return {
        "status": "running",
        "gemini_configured": bool(
            GEMINI_API_KEY
        ),
        "model": GEMINI_MODEL
    }


# ============================================================
# RUNNING MESSAGE
# ============================================================

@app.get("/api")
async def api_information():

    return {
        "project": "EduGenie",
        "message": "EduGenie API is running.",
        "endpoints": [
            "/qa",
            "/explain",
            "/quiz",
            "/summarize",
            "/learn/recommendations"
        ]
    }