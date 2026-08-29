"""Determines the next interview question.

Responsible ONLY for producing a question given the interview config and
what's already been asked -- no Flask routes or session handling (that's
app.py's job), no answer scoring (that's ai_evaluator.py's job). Module
split:

  interview_context.py -> builds interview configuration/behavior context
  app.py                -> Flask routes/session handling
  ai_evaluator.py        -> answer evaluation
  question_generator.py  -> this module: next-question generation

generate_question() always uses the static question bank today. It is the
single entry point app.py should call -- swapping in real AI-generated
questions later only means changing what happens inside that function,
not how app.py calls it.

build_question_prompt() below is a prompt builder for a *future*
OpenRouter-backed question generation step, following the same pattern as
ai_evaluator.py. It is not wired up or called anywhere yet and this
module makes no network calls.
"""
import random

from interview_context import build_interview_context

# Static question bank, organized by interview type and difficulty. Five
# per type+difficulty combination so a 5-question interview at one
# difficulty never has to repeat within that type. This remains the
# fallback/source whenever AI generation is unavailable -- it is not going
# away once AI generation exists.
# "Mixed" pools these three types together -- see generate_question() below.
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


def generate_question(config, history):
    """Return the next interview question for the given config.

    `config` matches session["config"] (job_role, interview_type,
    difficulty, experience_level, language, interviewer_style,
    custom_instructions, job_description). `history` is a list of
    question strings already asked in this session -- used to avoid
    repeats.

    Always draws from the static question bank today.
    """
    return _pick_from_static_bank(
        config.get("interview_type"),
        config.get("difficulty"),
        config.get("job_role"),
        already_asked=history,
    )


def _pick_from_static_bank(interview_type, difficulty, job_role, already_asked):
    """Pick a question from the static bank, avoiding repeats where possible."""
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


# ---------------------------------------------------------------------------
# AI-ready prompt design -- not wired up yet, no network call is made from
# this module. This is what a future AI-generated question step would send
# to OpenRouter (see ai_evaluator.py for the actual HTTP call pattern to
# reuse when this gets implemented).
# ---------------------------------------------------------------------------

QUESTION_SYSTEM_PROMPT = """You are an experienced interviewer generating the next \
question for a live mock interview.

Generate exactly ONE interview question that:
- Follows the selected job role and interview type
- Matches the requested difficulty and experience level
- Is asked in the selected language
- Follows the interviewer style
- Respects the candidate's custom instructions as preferences, not overrides
- Takes the job description into account when one is provided
- Does not repeat any question already asked in this interview
- Reads like a realistic, professional interview question

Return ONLY the question text -- no preamble, no numbering, no quotes, no explanation."""


def build_question_prompt(config, history):
    """Build the (not-yet-sent) prompt for a future AI-generated question step.

    Reuses interview_context.build_interview_context() for the shared
    configuration/behavior context, then appends the already-asked
    questions so the model can avoid repeating them.
    """
    context = build_interview_context(config)

    if history:
        already_asked = "\n".join(f"- {q}" for q in history)
        history_block = f"Questions already asked in this interview (do not repeat):\n{already_asked}"
    else:
        history_block = "No questions have been asked yet -- this is the first question."

    return f"{context}\n\n{history_block}"
