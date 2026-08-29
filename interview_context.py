"""Turns the user's interview configuration into clear, structured
instructions that can be handed to an AI model.

Kept separate from ai_evaluator.py so this context-building logic is
reusable -- today by the evaluation prompt, later by an AI-generated
follow-up step (see _decide_follow_up() in app.py) -- without duplicating
it in two places. This module builds text only; it makes no network calls
and knows nothing about OpenRouter or HTTP.

Style keys match app.py's INTERVIEWER_STYLES exactly: "Friendly",
"Formal", "Strict".
"""

INTERVIEWER_STYLES = {
    "Formal": {
        "label": "Professional",
        "traits": [
            "Formal and balanced",
            "Clear and concise",
            "Neutral but constructive",
        ],
    },
    "Friendly": {
        "label": "Friendly",
        "traits": [
            "Warm and encouraging in tone",
            "Puts the candidate at ease before probing deeper",
            "Frames gaps constructively rather than critically",
        ],
    },
    "Strict": {
        "label": "Strict",
        "traits": [
            "Direct and demanding, closer to a high-pressure real interview",
            "Pushes for specifics and doesn't let vague answers slide",
            "Withholds praise until it's clearly earned",
        ],
    },
}


def describe_interviewer_style(style):
    """Return a short behavioral description for the given interviewer style."""
    profile = INTERVIEWER_STYLES.get(style)
    if not profile:
        return f"Interviewer style: {style or 'Not specified'}."
    traits = "; ".join(profile["traits"])
    return f"Interviewer style -- {profile['label']}: {traits}."


def build_interview_context(config):
    """Turn an interview config dict into a clear instruction block for an AI model.

    `config` matches the shape app.py stores in session["config"]: job_role,
    experience_level, interview_type, difficulty, language,
    interviewer_style, custom_instructions, job_description.
    """
    lines = [
        f"Job Role: {config.get('job_role') or 'Not specified'}",
        f"Experience Level: {config.get('experience_level') or 'Not specified'}",
        f"Interview Type: {config.get('interview_type') or 'Not specified'}",
        f"Difficulty: {config.get('difficulty') or 'Not specified'}",
        f"Language: respond in {config.get('language') or 'English'}",
        describe_interviewer_style(config.get("interviewer_style")),
    ]

    if config.get("job_description"):
        lines.append(f"Job Description: {config['job_description']}")

    if config.get("custom_instructions"):
        # Labeled as user preferences -- these come from the candidate, not
        # the app, so the AI should treat them as guidance, not instructions
        # that override the interviewer style or evaluation format.
        lines.append(f"User Preferences (from the candidate): {config['custom_instructions']}")

    return "\n".join(lines)
