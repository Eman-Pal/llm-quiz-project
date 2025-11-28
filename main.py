from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import time
import os

# Try to import OpenAI safely
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
except:
    client = None

app = FastAPI()

MY_SECRET = "my-quiz-secret-8712"

@app.get("/")
def root():
    routes = []
    for route in app.routes:
        if hasattr(route, "path"):
            routes.append(route.path)
    return {
        "message": "Routes currently loaded",
        "routes": routes
    }

@app.get("/quiz")
def quiz_info():
    return {"message": "Quiz endpoint is alive. Use POST to submit."}

def fallback_answer(page_text: str):
    """
    Used when OpenAI is not available.
    Tries to guess answer from page.
    """
    if "anything you want" in page_text:
        return "anything you want"

    if "sum" in page_text.lower():
        # crude attempt to detect numbers
        import re
        numbers = re.findall(r"\d+", page_text)
        if numbers:
            return str(sum(map(int, numbers)))

    # Default fallback
    return "anything you want"


def get_answer(page_text):
    """
    Try OpenAI first. If it fails, use fallback.
    """

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

    # Use fallback
    return fallback_answer(page_text)


def solve_one_quiz(email, secret, quiz_url):
    page = requests.get(quiz_url)
    page_text = page.text

    # Detect origin
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


@app.post("/quiz")
async def quiz(request: Request):

    try:
        data = await request.json()
    except:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    if data.get("secret") != MY_SECRET:
        return JSONResponse(status_code=403, content={"error": "Invalid secret"})

    email = data["email"]
    secret = data["secret"]
    current_url = data["url"]

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

