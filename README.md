# 📞 AI Call Center Training Assistant

A Streamlit-based training dashboard that helps call center agents and job applicants practice the core skills of the role — answering interview questions, responding to customer situations, and writing professional emails — all in one place.

## What It Does

The app is organized into a sidebar-navigated dashboard with a home overview and four practice modules. Each module presents a task (a question, a scenario, or an email type), lets the user work through it, and returns structured feedback or output so the user can practice and self-review.

## Features

- **🏠 Home Dashboard** — Overview page with live counts of question categories, difficulty levels, customer scenarios, and email templates, plus quick-launch cards into each module.
- **🎤 Interview Practice** — Select a category (HR, Customer Service, Sales, Technical Support) and a difficulty level (Beginner, Intermediate, Advanced), then generate a random interview question to practice answering.
- **📝 Answer Evaluation** — Write an interview answer in a text box and receive a scored evaluation (Communication, Grammar, Confidence, Professionalism, Overall) along with improvement suggestions.
- **💬 Customer Scenarios** — Choose a customer situation (e.g. Angry Customer, Refund Request, Late Delivery, Wrong Product Received, Technical Support), generate the scenario text, write a response, and receive a scored evaluation (Customer Handling, Professionalism, Empathy, Problem Solving, Overall) with suggestions.
- **✉️ Email Generator** — Choose an email type (Apology Email, Follow-up Email, Refund Approval, Customer Reply) and generate an editable template with placeholders ready to fill in.
- **🎨 Custom Dashboard UI** — Gradient background, glassmorphism cards, and styled sidebar navigation, built entirely with custom CSS on top of Streamlit.

> **Note:** Answer Evaluation and Customer Scenarios currently return fixed sample scores and suggestions as placeholders — scoring is not yet powered by an AI model.

## Technologies Used

- [Python](https://www.python.org/)
- [Streamlit](https://streamlit.io/) — web app framework
- Custom CSS (injected via `st.markdown`) for the UI theme

## Installation

### Prerequisites

- Python 3.9+
- pip

### 1. Clone the repository

```bash
git clone https://github.com/malik-wasiq/AI-CallCenter-Training-Assistant.git
cd AI-CallCenter-Training-Assistant
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

### 4. Run the app

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

## Project Structure

```text
AI-CallCenter-Training-Assistant/
├── app.py             # Main Streamlit app — all pages, data, and UI logic
├── requirements.txt   # Python dependencies
├── .gitignore
└── README.md
```

## Screenshots

_Screenshots coming soon._

<!--
Add screenshots here once available, e.g.:
![Home Dashboard](screenshots/home.png)
![Interview Practice](screenshots/interview-practice.png)
-->

## Future Improvements

- Replace placeholder scoring in Answer Evaluation and Customer Scenarios with real AI-generated feedback.
- Add more interview questions, customer scenarios, and email templates.
- Persist user practice history/scores across sessions.
- Add authentication for multi-user tracking.

## Author

**Malik Muhammad Wasiq**
GitHub: [@malik-wasiq](https://github.com/malik-wasiq)
