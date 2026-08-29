import random

from flask import Flask, redirect, render_template, request, session, url_for

from ai_evaluator import evaluate_answer

app = Flask(__name__)
# Needed by Flask to sign the session cookie. Fine for local development;
# replace with a real secret (e.g. from an environment variable) before
# ever deploying this publicly.
app.secret_key = "dev-secret-key"

# Predefined interview questions, organized by category.
# Each category has questions for each difficulty level.
INTERVIEW_QUESTIONS = {
    "HR": {
        "Beginner": [
            "Tell me about yourself.",
            "Why do you want to work in a call center?",
            "What are your strengths and weaknesses?",
        ],
        "Intermediate": [
            "Describe a time you handled a conflict with a coworker.",
            "How do you handle stress during a busy shift?",
            "Why should we hire you over other candidates?",
        ],
        "Advanced": [
            "Tell me about a time you disagreed with your manager. How did you handle it?",
            "How would you handle being asked to work overtime with no notice?",
            "Describe a situation where you had to give difficult feedback to a peer.",
        ],
    },
    "Customer Service": {
        "Beginner": [
            "How would you greet a customer calling for the first time?",
            "What does good customer service mean to you?",
            "How do you stay polite when a customer is rude?",
        ],
        "Intermediate": [
            "A customer is unhappy with a delayed order. How do you respond?",
            "How would you handle a customer who keeps interrupting you?",
            "Describe how you would de-escalate an angry customer.",
        ],
        "Advanced": [
            "A customer threatens to cancel their service unless given a refund you can't approve. How do you handle it?",
            "How would you manage a customer who has been transferred multiple times and is frustrated?",
            "Describe a time you turned a negative customer experience into a positive one.",
        ],
    },
    "Sales": {
        "Beginner": [
            "How would you introduce a new product to a customer?",
            "What makes a good salesperson?",
            "How do you handle a customer who says 'I'm not interested'?",
        ],
        "Intermediate": [
            "How would you upsell a product without sounding pushy?",
            "Describe how you would handle a customer comparing you to a competitor.",
            "What would you do if a customer wanted a discount you couldn't give?",
        ],
        "Advanced": [
            "How would you close a sale with a customer who has been hesitant for weeks?",
            "Describe a time you lost a sale. What would you do differently now?",
            "How would you handle a high-value client threatening to switch to a competitor?",
        ],
    },
    "Technical Support": {
        "Beginner": [
            "How would you explain a technical issue to a non-technical customer?",
            "What steps would you take when a customer says their device won't turn on?",
            "How do you stay calm when you don't know the answer right away?",
        ],
        "Intermediate": [
            "A customer's internet keeps disconnecting. How would you troubleshoot this over the phone?",
            "How would you handle a customer who doesn't follow your instructions correctly?",
            "Describe how you would explain a software update to a frustrated user.",
        ],
        "Advanced": [
            "A customer's issue requires escalation, but they refuse to be transferred. How do you handle it?",
            "Describe how you would manage a technical outage affecting many customers at once.",
            "How would you handle a customer who claims your previous advice made the problem worse?",
        ],
    },
}

# Kept from the previous version for a future feature. Not wired into any
# route yet -- do not delete until a Customer Scenarios page is (re)built.
CUSTOMER_SCENARIOS = {
    "Angry Customer": "A customer is shouting on the call because their issue hasn't been fixed after multiple attempts. They feel ignored and want to speak to a manager immediately.",
    "Refund Request": "A customer is requesting a full refund for a product they say did not meet their expectations. They are firm and want the refund processed today.",
    "Late Delivery": "A customer's package was supposed to arrive three days ago but still hasn't shown up. They have an important event coming up and are anxious about not receiving it in time.",
    "Wrong Product Received": "A customer received the wrong product and is very upset. They are demanding an immediate replacement and want compensation.",
    "Technical Support": "A customer's device stopped working after a recent software update. They have already tried restarting it and are frustrated that basic troubleshooting hasn't helped.",
}

# Kept from the previous version for a future feature. Not wired into any
# route yet -- do not delete until an Email Generator page is (re)built.
EMAIL_TEMPLATES = {
    "Apology Email": """Subject: Our Apologies for the Inconvenience

Dear [Customer Name],

I want to sincerely apologize for the inconvenience you experienced with [issue/order]. This is not the level of service we strive to provide, and I understand your frustration.

We have looked into what happened and are taking steps to make sure it does not happen again. [Add specific details about the resolution here.]

Thank you for your patience and for bringing this to our attention. Please let me know if there is anything else I can do to help.

Best regards,
[Your Name]
[Company Name]""",

    "Follow-up Email": """Subject: Following Up on Your Recent Request

Dear [Customer Name],

I hope you're doing well. I'm following up regarding [topic/request] from [date] to check if everything is resolved on your end.

If you still have questions or need further assistance, please don't hesitate to reach out. I'm happy to help in any way I can.

Looking forward to hearing from you.

Best regards,
[Your Name]
[Company Name]""",

    "Refund Approval": """Subject: Your Refund Has Been Approved

Dear [Customer Name],

Good news! Your refund request for [order/product] has been reviewed and approved.

You should see the amount of [refund amount] credited back to your original payment method within [X] business days.

We appreciate your patience throughout this process, and please let us know if you have any further questions.

Best regards,
[Your Name]
[Company Name]""",

    "Customer Reply": """Subject: Re: [Original Subject]

Dear [Customer Name],

Thank you for reaching out to us. I appreciate you taking the time to share your concerns about [issue/topic].

[Add your specific response or solution here.]

If you need any further assistance, feel free to reply to this email or contact us anytime.

Best regards,
[Your Name]
[Company Name]""",
}

CATEGORIES = list(INTERVIEW_QUESTIONS.keys())
DIFFICULTIES = ["Beginner", "Intermediate", "Advanced"]
EXPERIENCE_LEVELS = ["Entry-Level", "Mid-Level", "Senior"]
LANGUAGES = ["English", "Urdu", "Spanish"]
INTERVIEWER_STYLES = ["Friendly", "Formal", "Strict"]


@app.route("/")
def index():
    """Home page with an overview of the app."""
    return render_template("index.html")


@app.route("/setup", methods=["GET", "POST"])
def setup():
    """Collect the interview configuration, then pick a random question."""
    if request.method == "POST":
        job_role = request.form.get("job_role", "").strip()
        interview_type = request.form.get("interview_type")
        difficulty = request.form.get("difficulty")
        experience_level = request.form.get("experience_level")
        language = request.form.get("language")
        interviewer_style = request.form.get("interviewer_style")
        custom_instructions = request.form.get("custom_instructions", "").strip()
        job_description = request.form.get("job_description", "").strip()

        errors = []
        if not job_role:
            errors.append("Please enter the job role you're practicing for.")
        if interview_type not in INTERVIEW_QUESTIONS:
            errors.append("Please choose a valid interview type.")
        if difficulty not in DIFFICULTIES:
            errors.append("Please choose a valid difficulty.")
        if experience_level not in EXPERIENCE_LEVELS:
            errors.append("Please choose a valid experience level.")
        if language not in LANGUAGES:
            errors.append("Please choose a valid language.")
        if interviewer_style not in INTERVIEWER_STYLES:
            errors.append("Please choose a valid interviewer style.")

        if errors:
            return render_template(
                "interview_setup.html",
                interview_types=CATEGORIES,
                difficulties=DIFFICULTIES,
                experience_levels=EXPERIENCE_LEVELS,
                languages=LANGUAGES,
                styles=INTERVIEWER_STYLES,
                errors=errors,
                form=request.form,
            )

        question = random.choice(INTERVIEW_QUESTIONS[interview_type][difficulty])

        # Store the config and question in the session so the next two pages
        # (/interview and /results) can use them without passing them in the URL.
        session["config"] = {
            "job_role": job_role,
            "interview_type": interview_type,
            "difficulty": difficulty,
            "experience_level": experience_level,
            "language": language,
            "interviewer_style": interviewer_style,
            "custom_instructions": custom_instructions,
            "job_description": job_description,
        }
        session["question"] = question
        session.pop("answer", None)
        session.pop("evaluation", None)

        return redirect(url_for("interview"))

    return render_template(
        "interview_setup.html",
        interview_types=CATEGORIES,
        difficulties=DIFFICULTIES,
        experience_levels=EXPERIENCE_LEVELS,
        languages=LANGUAGES,
        styles=INTERVIEWER_STYLES,
    )


@app.route("/interview", methods=["GET", "POST"])
def interview():
    """Show the generated question and collect the user's answer."""
    if "question" not in session or "config" not in session:
        # No question has been generated yet -- send them to set one up first.
        return redirect(url_for("setup"))

    if request.method == "POST":
        answer = request.form.get("answer", "").strip()

        if not answer:
            return render_template(
                "interview.html",
                config=session["config"],
                question=session["question"],
                error="Please write an answer before submitting.",
            )

        evaluation = evaluate_answer(session["config"], session["question"], answer)

        session["answer"] = answer
        session["evaluation"] = evaluation
        return redirect(url_for("results"))

    return render_template(
        "interview.html",
        config=session["config"],
        question=session["question"],
    )


@app.route("/results")
def results():
    """Show the AI-generated evaluation of the submitted answer."""
    if "evaluation" not in session:
        return redirect(url_for("setup"))

    return render_template(
        "results.html",
        config=session["config"],
        question=session["question"],
        answer=session["answer"],
        evaluation=session["evaluation"],
    )


if __name__ == "__main__":
    app.run(debug=True)
