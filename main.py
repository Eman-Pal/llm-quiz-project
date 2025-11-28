print("********** RENDER IS RUNNING THIS FILE **********")

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
import time
import os

# --- OpenAI (safe import) ---
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
except:
    client = None

# --- App ---
app = FastAPI()

MY_SECRET = "my-quiz-secret-8712"

# ----- REQUEST BODY MODEL (THIS FIXES YOUR SWAGGER BOX) -----

class QuizRequest(BaseModel):
    email: str
    secret: str
    url: str


# ----- ROOT -----

@app.get("/")
def root():
    routes = [route.path for route in app.routes if hasattr(route, "path")]
    return {
        "message": "Routes currently loaded",
        "routes": routes
    }


# ----- QUIZ INFO -----

@app.get("/quiz")
def quiz_info():
    return {"message": "Quiz endpoint is alive. Use POST to submit."}


# ----- FALLBACK ANSWER (WHEN GPT IS NOT AVAILABLE) -----

def fallback_answer(page_text: str):
    if "anything you want" in page_text:
        return "anything you want"

    if "sum" in page_text.lower():
        import re
        numbers = re.findall(r"\d+", page_text)
        if numbers:
            return str(sum(map(int, numbers)))

    return "anything you want"


# ----- GET ANSWER -----

def get_answer(page_text):

    if client is not None:
        try:
            prompt = f"""
You are solving a quiz.

Here is the page content:

{page_text[:4000]}

Return ONLY the exact answer value for the required "answer" field.
No explanation.
"""

            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You solve quizzes"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print("OpenAI failed, using fallback:", e)

    return fallback_answer(page_text)


# ----- SOLVE ONE QUIZ -----

def solve_one_quiz(email, secret, quiz_url):

    page = requests.get(quiz_url)
    page_text = page.text

    origin = "/".join(quiz_url.split("/")[:3])
    submit_url = origin + "/submit"

    answer = get_answer(page_text)

    payload = {
        "email": email,
        "secret": secret,
        "url": quiz_url,
        "answer": answer
    }

    response = requests.post(submit_url, json=payload)
    return response.json(), answer


# ✅✅✅ THIS IS THE CORRECT QUIZ ROUTE ✅✅✅

@app.post("/quiz")
async def quiz(data: QuizRequest):

    if data.secret != MY_SECRET:
        return JSONResponse(status_code=403, content={"error": "Invalid secret"})

    email = data.email
    secret = data.secret
    current_url = data.url

    start_time = time.time()
    history = []

    while current_url and (time.time() - start_time) < 180:

        result, answer_used = solve_one_quiz(email, secret, current_url)

        history.append({
            "url": current_url,
            "answer_used": answer_used,
            "result": result
        })

        if result.get("url"):
            current_url = result.get("url")
        else:
            break

    return {
        "status": "finished",
        "attempts": history
    }

