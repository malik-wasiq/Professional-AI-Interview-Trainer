# 📞 AI Call Center Training Assistant

A Streamlit dashboard for practicing call center skills — interview questions, answer evaluation, customer scenarios, and email templates — built as a portfolio project.

## Features

- **🎤 Interview Practice** — Random interview questions across four categories (HR, Customer Service, Sales, Technical Support) and three difficulty levels (Beginner, Intermediate, Advanced).
- **📝 Answer Evaluation** — Write an interview answer and get a scored evaluation (communication, grammar, confidence, professionalism) plus improvement suggestions.
- **💬 Customer Scenarios** — Pick a realistic customer situation (angry customer, refund request, late delivery, etc.), generate the scenario, write your response, and get feedback.
- **✉️ Email Generator** — Ready-to-use professional email templates (e.g. apology, follow-up) with placeholders you can fill in.

> **Note:** Answer Evaluation and Customer Scenarios currently show fixed sample scores/suggestions as placeholders — no AI model is wired in yet.

## Tech Stack

- [Streamlit](https://streamlit.io/) — Python

## Setup Instructions

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
```
AI-CallCenter-Training-Assistant/
├── app.py             # Main Streamlit app (all pages and logic)
├── requirements.txt   # Python dependencies
└── .gitignore
```

## Status

Portfolio project — v1.0.
