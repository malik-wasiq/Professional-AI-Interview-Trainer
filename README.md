# 🎯 Professional AI Interview Trainer

A Flask-based web application that helps job applicants and professionals practice professional job interviews. Users configure an interview session (job role, interview type, experience level, difficulty, language, and interviewer style), work through a 5-question mock interview, and receive a scored evaluation at the end.

Both the interview questions and the final evaluation can be AI-generated via [OpenRouter](https://openrouter.ai/) — see [AI Question Generation](#ai-question-generation) and [AI Evaluation](#ai-evaluation) below. Both are fully optional: with no API key configured, the app runs end to end using a static question bank and a placeholder evaluation instead.

## Features

- **🎤 Configurable Interview Setup** — Choose a job role (10 presets, e.g. Software Engineer, Data Analyst, Sales, Project Manager), an interview type (HR / Behavioral, Technical, Situational, Role-Specific, Mixed), experience level, difficulty (Easy, Medium, Hard, Expert), language, and interviewer style (Professional, Friendly, Strict, Challenging, Technical), plus optional job description and custom instructions.
- **🔄 Multi-Question Interview Sessions** — Each interview is a 5-question session, not a single prompt. A progress bar tracks how far through the session you are, and every question and answer is recorded for the final results.
- **🤖 AI Question Generation with Static Fallback** — Questions can be generated live by an OpenRouter model tailored to your setup, with a two-key 429 rate-limit failover and an automatic drop to a static question bank if AI generation isn't configured or fails (see [AI Question Generation](#ai-question-generation)).
- **📝 Results & Evaluation** — After the final question, the app shows your full question/answer history and a scored evaluation (see [AI Evaluation](#ai-evaluation)).
- **🎨 Clean, Responsive UI** — Custom HTML/CSS/vanilla JS interface (no frontend framework) with light/dark themes, entrance and progress/score-bar animations (respecting `prefers-reduced-motion`), accessible focus states, and a mobile-first responsive layout.

## AI Question Generation

Each interview question can be generated via [OpenRouter](https://openrouter.ai/), called directly over HTTP with the `requests` library — no vendor SDK:

- If `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` are set, each question is generated live from your interview setup (job role, type, difficulty, experience level, language, interviewer style, custom instructions, job description) and checked against questions already asked in the session to avoid repeats.
- If that request comes back rate-limited (HTTP 429) and `OPENROUTER_API_KEY_2` is also set, the same request is retried once with the second key.
- If AI generation isn't configured, both keys are exhausted, or the response can't be trusted, the app falls back to a static question bank (5 questions per interview type per difficulty, or per-role templates for Role-Specific) — the interview always has a next question either way.

## AI Evaluation

Answer evaluation is implemented via [OpenRouter](https://openrouter.ai/), called directly over HTTP with the `requests` library — no vendor SDK. It requires **your own** OpenRouter API key:

- If `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` are set (e.g. in a local `.env` file), the final answer of each interview is sent to the configured model for a real, scored evaluation.
- If they are **not** set, or the request fails for any reason, the app automatically falls back to a clearly labeled placeholder evaluation instead of erroring out — the interview flow always completes either way.

No API key is required to run or try the app; it's only required to get real AI-generated questions and scoring instead of the static/placeholder defaults.

## Technology Stack

- [Python](https://www.python.org/)
- [Flask](https://flask.palletsprojects.com/) — web framework and routing
- [Jinja2](https://jinja.palletsprojects.com/) — server-side HTML templating (ships with Flask)
- HTML, CSS, and vanilla JavaScript for the frontend — no React, Tailwind, Bootstrap, or other frontend framework
- [OpenRouter](https://openrouter.ai/) — AI question generation and evaluation backend, called via `requests`; configured through environment variables, requires a user-supplied API key (see [AI Question Generation](#ai-question-generation) and [AI Evaluation](#ai-evaluation))
- [python-dotenv](https://pypi.org/project/python-dotenv/) — loads environment variables from a local `.env` file if present
- [Gunicorn](https://gunicorn.org/) — production WSGI server (see [Production Deployment](#production-deployment))

## Installation

### Prerequisites

- Python 3.9+
- pip

### 1. Clone the repository

```bash
git clone https://github.com/malik-wasiq/Professional-AI-Interview-Trainer.git
cd Professional-AI-Interview-Trainer
```

### 2. Create and activate a virtual environment

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

| Variable | Required? | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | **Required** | Signs the Flask session cookie. The app raises an error at startup if this is missing — generate one with `python -c "import secrets; print(secrets.token_urlsafe(32))"` and use a different value per environment (never reuse a local dev key in production). |
| `OPENROUTER_API_KEY` | Optional | Enables AI-generated questions and AI-scored evaluation. Without it, the app runs fully using the static question bank and placeholder evaluation. |
| `OPENROUTER_API_KEY_2` | Optional | Second OpenRouter key used as an automatic failover if the first key is rate-limited (HTTP 429). |
| `OPENROUTER_MODEL` | Optional (required alongside `OPENROUTER_API_KEY` to enable AI features) | The OpenRouter model id to call for question generation and evaluation. |
| `FLASK_DEBUG` | Optional | Set to `true` only for local development to enable Flask's debugger/reloader. Leave unset (defaults to off) in production. |

### 5. Run the app

```bash
python app.py
```

The app will open at `http://127.0.0.1:5000/`.

## Production Deployment

The app ships with a `Procfile` (`web: gunicorn app:app`) and [Gunicorn](https://gunicorn.org/) in `requirements.txt`, so it's ready for any Procfile-based host (e.g. Render, Railway, Heroku-style platforms):

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `gunicorn app:app`
- **Environment variables:** set `SECRET_KEY` (a fresh value, separate from any local dev key), and optionally `OPENROUTER_API_KEY`, `OPENROUTER_API_KEY_2`, `OPENROUTER_MODEL` directly on the host — never commit them.
- **Leave `FLASK_DEBUG` unset.** Gunicorn never runs the app's `if __name__ == "__main__":` block (where local-only debug mode is gated), so Flask's debugger/reloader can't be enabled in this path regardless.

## Project Structure

```text
Professional-AI-Interview-Trainer/
├── app.py                       # Flask app: routes, session/interview state, setup options
├── ai_evaluator.py              # OpenRouter-based answer evaluation, with placeholder fallback
├── question_generator.py        # OpenRouter-based question generation, with static bank fallback
├── interview_context.py         # Builds the shared AI prompt context from the interview config
├── test_question_generator.py   # Automated tests for question generation and the full interview flow
├── templates/                   # Jinja2 HTML templates
│   ├── base.html                #   Shared layout (nav, footer)
│   ├── index.html               #   Home page
│   ├── interview_setup.html     #   Interview configuration form
│   ├── interview.html           #   Question/answer screen
│   └── results.html             #   Interview history + final evaluation
├── static/
│   ├── style.css                # All custom styling
│   └── script.js                # Small vanilla-JS enhancements (validation, progress, etc.)
├── requirements.txt              # Python dependencies (Flask, requests, python-dotenv, gunicorn)
├── Procfile                      # Production start command (gunicorn app:app)
├── .env.example                  # Template for local environment configuration
├── .gitignore
└── README.md
```

## Screenshots

_Screenshots coming soon._

<!--
Add screenshots here once available, e.g.:
![Home](screenshots/home.png)
![Interview](screenshots/interview.png)
![Results](screenshots/results.png)
-->

## Current Limitations

- AI-generated questions and evaluation require the user to supply their own OpenRouter API key; without one, questions come from the static bank and scoring is a fixed placeholder rather than AI-generated feedback.
- No database — interview state lives only in the browser session and is not saved after it ends.
- No authentication, voice input, resume upload, or PDF export.

## Future Improvements

- Wire up AI-generated follow-up questions during the interview (the architecture already has a hook point for this — see `_decide_follow_up` in `app.py`).
- Persist interview history/scores across sessions.
- Expand the static fallback question bank further.
- Revisit the unused customer-scenario and email-template data still present in `app.py` for a possible future practice module.

## Author

**Malik Muhammad Wasiq**
GitHub: [@malik-wasiq](https://github.com/malik-wasiq)
