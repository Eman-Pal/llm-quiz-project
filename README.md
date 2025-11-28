# LLM Analysis Quiz Solver

This is an automated API system that:

- Accepts a quiz URL
- Validates a secret key
- Reads and processes the quiz page
- Submits an answer
- Automatically follows new quiz URLs

## Endpoint

POST /quiz

Example payload:
{
  "email": "your_email",
  "secret": "my-quiz-secret-8712",
  "url": "quiz_url"
}

## Features

- Handles multiple linked quizzes
- Uses LLM if available
- Falls back to rule-based logic if not
- Runs within 3-minute limit

## Tech Stack

- Python
- FastAPI
- Requests
- OpenAI (optional)

