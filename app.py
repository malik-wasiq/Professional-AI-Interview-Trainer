import random

from flask import Flask, redirect, render_template, request, session, url_for

from ai_evaluator import evaluate_answer

app = Flask(__name__)
# Needed by Flask to sign the session cookie. Fine for local development;
# replace with a real secret (e.g. from an environment variable) before
# ever deploying this publicly.
app.secret_key = "dev-secret-key"

# Predefined interview questions, organized by interview type.
# Each type has questions for each difficulty level. "Role-Specific" and
# "Mixed" are handled separately -- see ROLE_SPECIFIC_TEMPLATES and the
# Mixed-pool logic in setup() below.
INTERVIEW_QUESTIONS = {
    "HR / Behavioral": {
        "Beginner": [
            "Tell me about yourself.",
            "Why are you interested in this role?",
            "What are your greatest strengths and weaknesses?",
        ],
        "Intermediate": [
            "Describe a time you handled a conflict with a coworker.",
            "How do you handle stress or tight deadlines?",
            "Why should we hire you over other candidates?",
        ],
        "Advanced": [
            "Tell me about a time you disagreed with your manager. How did you handle it?",
            "Describe a time you had to give difficult feedback to a peer.",
            "How would you handle being asked to take on responsibilities outside your job description?",
        ],
    },
    "Technical": {
        "Beginner": [
            "What tools or technologies are you most comfortable working with?",
            "Walk me through how you would approach learning a new skill required for this role.",
            "How do you stay up to date with developments in your field?",
        ],
        "Intermediate": [
            "Describe a technical problem you solved recently and how you approached it.",
            "How do you prioritize tasks when working on multiple technical problems at once?",
            "What's your process for troubleshooting an issue you haven't seen before?",
        ],
        "Advanced": [
            "Describe the most complex project you've worked on and your specific contribution.",
            "How would you evaluate whether to build a solution in-house or use an existing tool?",
            "Tell me about a time a technical decision you made didn't work out. What did you learn?",
        ],
    },
    "Situational": {
        "Beginner": [
            "How would you handle a task with unclear instructions?",
            "What would you do if you disagreed with a decision made by your team?",
            "How would you prioritize your work if given multiple urgent tasks at once?",
        ],
        "Intermediate": [
            "A project you're working on is falling behind schedule. What steps would you take?",
            "How would you handle a situation where a teammate isn't pulling their weight?",
            "What would you do if you made a mistake that affected the whole team?",
        ],
        "Advanced": [
            "You're asked to deliver a project with limited resources and a tight deadline. How do you approach it?",
            "How would you handle a situation where you had to push back on a request from senior leadership?",
            "Describe how you would manage a high-pressure situation with conflicting stakeholder priorities.",
        ],
    },
}

# Used only for the "Role-Specific" interview type -- {role} is filled in
# with the job role chosen on the setup form.
ROLE_SPECIFIC_TEMPLATES = {
    "Beginner": "What interests you most about the {role} role, and what makes you a good fit?",
    "Intermediate": "What do you think are the most important skills for the {role} role, and how have you demonstrated them?",
    "Advanced": "Describe a challenging project you'd expect to handle in the {role} role, and how you'd approach it.",
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

# The interview type dropdown includes two types ("Role-Specific" and
# "Mixed") that aren't literal keys in INTERVIEW_QUESTIONS -- they're
# generated in setup() instead. List order here is the display order.
INTERVIEW_TYPES = ["HR / Behavioral", "Technical", "Situational", "Role-Specific", "Mixed"]
DIFFICULTIES = ["Beginner", "Intermediate", "Advanced"]
EXPERIENCE_LEVELS = ["Entry-Level", "Mid-Level", "Senior"]
LANGUAGES = ["English", "Urdu", "Spanish"]
INTERVIEWER_STYLES = ["Friendly", "Formal", "Strict"]

# Add new roles here to extend the dropdown -- no other code changes needed.
JOB_ROLES = [
    "Software Engineer",
    "Python Developer",
    "Web Developer",
    "Data Analyst",
    "Customer Support",
    "Sales",
    "Marketing",
    "Project Manager",
    "Business Analyst",
    "General / Other",
]

# How many questions make up one interview session.
TOTAL_QUESTIONS_PER_INTERVIEW = 5


def _pick_question(interview_type, difficulty, job_role, already_asked):
    """Pick a question for the given config, avoiding repeats where possible.

    Role-Specific always returns the same templated question for a given
    role+difficulty -- there's only one, so repeats are unavoidable there.
    """
    if interview_type == "Role-Specific":
        return ROLE_SPECIFIC_TEMPLATES[difficulty].format(role=job_role)

    if interview_type == "Mixed":
        pool = (
            INTERVIEW_QUESTIONS["HR / Behavioral"][difficulty]
            + INTERVIEW_QUESTIONS["Technical"][difficulty]
            + INTERVIEW_QUESTIONS["Situational"][difficulty]
        )
    else:
        pool = INTERVIEW_QUESTIONS[interview_type][difficulty]

    unused = [q for q in pool if q not in already_asked]
    return random.choice(unused) if unused else random.choice(pool)


def _decide_follow_up(config, question, answer):
    """Decide whether to ask a follow-up question instead of moving on.

    Stub for now -- always returns None (no follow-up), since generating an
    intelligent follow-up requires an AI call, which this step doesn't make.
    This is the hook point for a future AI-generated follow-up: when wired
    up, it would call the OpenRouter integration (like evaluate_answer)
    and return a follow-up question string instead of None.
    """
    return None


@app.route("/")
def index():
    """Home page with an overview of the app."""
    return render_template("index.html")


@app.route("/setup", methods=["GET", "POST"])
def setup():
    """Collect the interview configuration, then pick a random question."""
    if request.method == "POST":
        job_role = request.form.get("job_role")
        interview_type = request.form.get("interview_type")
        difficulty = request.form.get("difficulty")
        experience_level = request.form.get("experience_level")
        language = request.form.get("language")
        interviewer_style = request.form.get("interviewer_style")
        custom_instructions = request.form.get("custom_instructions", "").strip()
        job_description = request.form.get("job_description", "").strip()

        errors = []
        if job_role not in JOB_ROLES:
            errors.append("Please choose a valid job role.")
        if interview_type not in INTERVIEW_TYPES:
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
                job_roles=JOB_ROLES,
                interview_types=INTERVIEW_TYPES,
                difficulties=DIFFICULTIES,
                experience_levels=EXPERIENCE_LEVELS,
                languages=LANGUAGES,
                styles=INTERVIEWER_STYLES,
                errors=errors,
                form=request.form,
            )

        question = _pick_question(interview_type, difficulty, job_role, already_asked=set())

        # Store the config and a fresh interview session, replacing anything
        # left over from a previous interview -- this is what makes
        # restarting from Setup clear the old session.
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
        session["interview"] = {
            "current_question": question,
            "question_number": 1,
            "total_questions": TOTAL_QUESTIONS_PER_INTERVIEW,
            "questions_asked": [question],
            "answers_submitted": [],
            "history": [],
        }
        session.pop("final_evaluation", None)

        return redirect(url_for("interview"))

    return render_template(
        "interview_setup.html",
        job_roles=JOB_ROLES,
        interview_types=INTERVIEW_TYPES,
        difficulties=DIFFICULTIES,
        experience_levels=EXPERIENCE_LEVELS,
        languages=LANGUAGES,
        styles=INTERVIEWER_STYLES,
    )


@app.route("/interview", methods=["GET", "POST"])
def interview():
    """Show the current question and collect the user's answer.

    Each answer is recorded, then either a follow-up or the next question
    is shown (see _decide_follow_up), until total_questions is reached --
    at which point the interview is complete and /results takes over.
    """
    if "interview" not in session or "config" not in session:
        # No interview in progress -- send them to set one up first.
        return redirect(url_for("setup"))

    config = session["config"]
    state = session["interview"]

    if request.method == "POST":
        answer = request.form.get("answer", "").strip()

        if not answer:
            return render_template(
                "interview.html",
                config=config,
                interview=state,
                error="Please write an answer before submitting.",
            )

        question = state["current_question"]
        state["answers_submitted"].append(answer)
        state["history"].append({
            "question_number": state["question_number"],
            "question": question,
            "answer": answer,
        })

        if state["question_number"] >= state["total_questions"]:
            # Last question answered -- score it and finish the interview.
            evaluation = evaluate_answer(config, question, answer)
            session["final_evaluation"] = evaluation
            session["interview"] = state
            session.modified = True
            return redirect(url_for("results"))

        follow_up = _decide_follow_up(config, question, answer)
        next_question = follow_up or _pick_question(
            config["interview_type"], config["difficulty"], config["job_role"],
            already_asked=set(state["questions_asked"]),
        )

        state["question_number"] += 1
        state["current_question"] = next_question
        state["questions_asked"].append(next_question)
        session["interview"] = state
        session.modified = True

        return redirect(url_for("interview"))

    return render_template(
        "interview.html",
        config=config,
        interview=state,
    )


@app.route("/results")
def results():
    """Show the full interview history and the AI-generated final evaluation."""
    if "final_evaluation" not in session:
        return redirect(url_for("setup"))

    return render_template(
        "results.html",
        config=session["config"],
        interview=session["interview"],
        evaluation=session["final_evaluation"],
    )


if __name__ == "__main__":
    app.run(debug=True)
