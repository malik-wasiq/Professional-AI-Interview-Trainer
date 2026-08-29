import random

from flask import Flask, redirect, render_template, request, session, url_for

from ai_evaluator import evaluate_answer

app = Flask(__name__)
# Needed by Flask to sign the session cookie. Fine for local development;
# replace with a real secret (e.g. from an environment variable) before
# ever deploying this publicly.
app.secret_key = "dev-secret-key"

# Predefined interview questions, organized by interview type and
# difficulty. Five per type+difficulty combination so a 5-question
# interview at one difficulty never has to repeat within that type.
# "Mixed" pools these three types together -- see _pick_question() below.
# "Role-Specific" has its own bank in ROLE_SPECIFIC_TEMPLATES.
INTERVIEW_QUESTIONS = {
    "HR / Behavioral": {
        "Easy": [
            "Tell me about yourself.",
            "Why are you interested in this role?",
            "What are your greatest strengths and weaknesses?",
            "What motivates you at work?",
            "How do you handle receiving feedback?",
        ],
        "Medium": [
            "Describe a time you handled a conflict with a coworker.",
            "How do you handle stress or tight deadlines?",
            "Why should we hire you over other candidates?",
            "Tell me about a time you had to work with someone whose working style was very different from yours.",
            "Describe a goal you set for yourself and how you achieved it.",
        ],
        "Hard": [
            "Tell me about a time you disagreed with your manager. How did you handle it?",
            "Describe a time you had to give difficult feedback to a peer.",
            "How would you handle being asked to take on responsibilities outside your job description?",
            "Describe a time you failed at something important. What did you learn?",
            "Tell me about a time you had to influence someone without direct authority over them.",
        ],
        "Expert": [
            "Describe a time you had to make an unpopular decision that affected your team. How did you handle the fallout?",
            "Tell me about a time you identified a systemic problem in how your team or organization worked, and what you did about it.",
            "How would you handle leading a team through a period of significant organizational change?",
            "Describe the most difficult ethical decision you've faced at work and how you approached it.",
            "Tell me about a time you had to balance competing priorities from multiple stakeholders with conflicting goals.",
        ],
    },
    "Technical": {
        "Easy": [
            "What tools or technologies are you most comfortable working with?",
            "Walk me through how you would approach learning a new skill required for this role.",
            "How do you stay up to date with developments in your field?",
            "What does your typical workflow look like when starting a new task?",
            "How do you decide what to work on first when you have multiple small tasks?",
        ],
        "Medium": [
            "Describe a technical problem you solved recently and how you approached it.",
            "How do you prioritize tasks when working on multiple technical problems at once?",
            "What's your process for troubleshooting an issue you haven't seen before?",
            "How do you make sure your work meets quality standards before it's considered done?",
            "Describe a time you had to learn a new tool or technology quickly to complete a task.",
        ],
        "Hard": [
            "Describe the most complex project you've worked on and your specific contribution.",
            "How would you evaluate whether to build a solution in-house or use an existing tool?",
            "Tell me about a time a technical decision you made didn't work out. What did you learn?",
            "How do you approach reviewing someone else's work and giving constructive feedback?",
            "Describe a situation where you had to balance speed and quality under a tight deadline.",
        ],
        "Expert": [
            "How would you design a process or system to scale as demands grow significantly over time?",
            "Describe a time you had to make a major technical or strategic decision with incomplete information.",
            "How would you approach mentoring a struggling team member while still meeting your own deliverables?",
            "Tell me about a time you had to advocate for a technical or process change that others were resistant to.",
            "Describe how you would evaluate and manage risk on a high-stakes project.",
        ],
    },
    "Situational": {
        "Easy": [
            "How would you handle a task with unclear instructions?",
            "What would you do if you disagreed with a decision made by your team?",
            "How would you prioritize your work if given multiple urgent tasks at once?",
            "What would you do if you noticed a mistake in your own completed work?",
            "How would you respond if a coworker asked for help while you were busy with your own deadline?",
        ],
        "Medium": [
            "A project you're working on is falling behind schedule. What steps would you take?",
            "How would you handle a situation where a teammate isn't pulling their weight?",
            "What would you do if you made a mistake that affected the whole team?",
            "How would you handle receiving conflicting instructions from two different managers?",
            "What would you do if you were assigned a task outside your area of expertise?",
        ],
        "Hard": [
            "You're asked to deliver a project with limited resources and a tight deadline. How do you approach it?",
            "How would you handle a situation where you had to push back on a request from senior leadership?",
            "Describe how you would manage a high-pressure situation with conflicting stakeholder priorities.",
            "How would you handle discovering that a completed project had a significant flaw after it was delivered?",
            "What would you do if you had to deliver bad news to a client or stakeholder?",
        ],
        "Expert": [
            "How would you handle a situation where achieving a business goal required a decision you were personally uncomfortable with?",
            "Describe how you would manage a crisis that affects multiple teams and has no clear owner.",
            "How would you approach a situation where your team's success depended on a decision made by another department you had no control over?",
            "What would you do if you discovered a serious problem that, if reported, would delay a major deliverable but if left unreported could have major consequences?",
            "How would you handle a situation where you had to rebuild trust with a team or stakeholder after a major failure?",
        ],
    },
}

# Used only for the "Role-Specific" interview type -- {role} is filled in
# with the job role chosen on the setup form. Five templates per
# difficulty, same as the other banks, so a Role-Specific session doesn't
# repeat the same question every round.
ROLE_SPECIFIC_TEMPLATES = {
    "Easy": [
        "What interests you most about the {role} role, and what makes you a good fit?",
        "What skills do you think are most important for someone in a {role} position?",
        "Why did you choose to pursue work as a {role}?",
        "What does a typical day look like for someone in the {role} role, in your understanding?",
        "What part of {role} work do you find most rewarding?",
    ],
    "Medium": [
        "What do you think are the most important skills for the {role} role, and how have you demonstrated them?",
        "Describe a project or task typical of the {role} role that you're proud of.",
        "How do you keep your skills relevant for the {role} role as things change over time?",
        "What tools or methods do you rely on most in {role} work?",
        "How would you explain the value of the {role} role to someone outside the field?",
    ],
    "Hard": [
        "Describe a challenging project you'd expect to handle in the {role} role, and how you'd approach it.",
        "What's the biggest mistake someone new to the {role} role might make, and how would you avoid it?",
        "How would you handle a situation where the expectations of the {role} role conflicted with a tight deadline?",
        "What would you do if you were asked to take on {role} work outside your current expertise?",
        "How do you measure success in the {role} role?",
    ],
    "Expert": [
        "How would you evaluate and improve the way {role} work is done across an entire team or organization?",
        "Describe how you would mentor someone new to the {role} role while managing your own workload.",
        "What long-term trends do you think will most affect the {role} role, and how would you prepare for them?",
        "How would you handle a major setback on a high-stakes project central to the {role} role?",
        "How would you balance innovation with reliability when making decisions in the {role} role?",
    ],
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
DIFFICULTIES = ["Easy", "Medium", "Hard", "Expert"]
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
    """Pick a question for the given config, avoiding repeats where possible."""
    if interview_type == "Role-Specific":
        pool = [t.format(role=job_role) for t in ROLE_SPECIFIC_TEMPLATES[difficulty]]
    elif interview_type == "Mixed":
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
