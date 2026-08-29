# 🎯 Professional AI Interview Trainer

A Flask-based web application that helps job applicants and professionals practice professional job interviews. Users configure an interview session (job role, interview type, experience level, difficulty, language, and interviewer style), work through a multi-question mock interview, and receive an evaluation at the end.

The interview session and question system are fully implemented today. AI-powered evaluation is being built out on top of an OpenRouter integration — see [AI Evaluation](#ai-evaluation) below for exactly what that means right now.

## Features

- **🎤 Configurable Interview Setup** — Choose a job role (10 presets, e.g. Software Engineer, Data Analyst, Sales, Project Manager), an interview type (HR / Behavioral, Technical, Situational, Role-Specific, Mixed), experience level, difficulty, language, and interviewer style, plus optional job description and custom instructions.
- **🔄 Multi-Question Interview Sessions** — Each interview is a 5-question session, not a single prompt. A progress bar tracks how far through the session you are, and every question and answer is recorded for the final results.
- **🗂️ Question Bank** — HR / Behavioral, Technical, and Situational each have 5 unique questions per difficulty level (Easy, Medium, Hard, Expert). Role-Specific generates questions from 5 templates per difficulty, filled in with your chosen job role. Mixed draws from a pooled mix of the other three types. A 5-question session doesn't repeat a question where the bank allows it.
- **📝 Results & Evaluation** — After the final question, the app shows your full question/answer history and a scored evaluation (see AI Evaluation below).
- **🎨 Clean, Responsive UI** — Custom HTML/CSS/vanilla JS interface (no frontend framework) with a progress bar, score bars, accessible focus states, and mobile-friendly layout.

## AI Evaluation

Answer evaluation is implemented via [OpenRouter](https://openrouter.ai/), called directly over HTTP with the `requests` library — no vendor SDK. It requires **your own** OpenRouter API key:

- If `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` are set (e.g. in a local `.env` file), the final answer of each interview is sent to the configured model for a real, scored evaluation.
- If they are **not** set, or the request fails for any reason, the app automatically falls back to a clearly labeled placeholder evaluation instead of erroring out — the interview flow always completes either way.

No API key is required to run or try the app; it's only required to get real AI-generated scoring instead of the placeholder.

## Technology Stack

- [Python](https://www.python.org/)
- [Flask](https://flask.palletsprojects.com/) — web framework and routing
- [Jinja2](https://jinja.palletsprojects.com/) — server-side HTML templating (ships with Flask)
- HTML, CSS, and vanilla JavaScript for the frontend — no React, Tailwind, Bootstrap, or other frontend framework
- [OpenRouter](https://openrouter.ai/) — AI evaluation backend, called via `requests`; configured through environment variables, requires a user-supplied API key (see [AI Evaluation](#ai-evaluation))
- [python-dotenv](https://pypi.org/project/python-dotenv/) — loads `OPENROUTER_API_KEY` / `OPENROUTER_MODEL` from a local `.env` file if present

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

### 4. (Optional) Configure AI evaluation

Copy `.env.example` to `.env` and fill in your own OpenRouter credentials:

```bash
cp .env.example .env
```

```text
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=your_chosen_model_here
```

This step is optional — without it, the app still runs and completes interviews using the placeholder evaluation described above.

### 5. Run the app

```bash
python app.py
```

The app will open at `http://127.0.0.1:5000/`.

## Project Structure

```text
Professional-AI-Interview-Trainer/
├── app.py                       # Flask app: routes, session/interview state, question bank
├── ai_evaluator.py              # OpenRouter-based answer evaluation, with placeholder fallback
├── templates/                   # Jinja2 HTML templates
│   ├── base.html                #   Shared layout (nav, footer)
│   ├── index.html               #   Home page
│   ├── interview_setup.html     #   Interview configuration form
│   ├── interview.html           #   Question/answer screen
│   └── results.html             #   Interview history + final evaluation
├── static/
│   ├── style.css                # All custom styling
│   └── script.js                # Small vanilla-JS enhancements (validation, progress, etc.)
├── requirements.txt              # Python dependencies
├── .env.example                  # Template for local OpenRouter configuration
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

- AI evaluation requires the user to supply their own OpenRouter API key; without one, scoring is a fixed placeholder rather than AI-generated feedback.
- No database — interview state lives only in the browser session and is not saved after it ends.
- No authentication, voice input, resume upload, or PDF export.

## Future Improvements

- Wire up AI-generated follow-up questions during the interview (the architecture already has a hook point for this).
- Persist interview history/scores across sessions.
- Expand the question bank further and consider AI-generated questions.
- Revisit the unused customer-scenario and email-template data still present in `app.py` for a possible future practice module.

## Author

**Malik Muhammad Wasiq**
GitHub: [@malik-wasiq](https://github.com/malik-wasiq)
