"""Turns the user's interview configuration into clear, structured
instructions that can be handed to an AI model.

Kept separate from ai_evaluator.py so this context-building logic is
reusable -- today by the evaluation prompt, later by an AI-generated
follow-up step (see _decide_follow_up() in app.py) -- without duplicating
it in two places. This module builds text only; it makes no network calls
and knows nothing about OpenRouter or HTTP.

Style keys match app.py's INTERVIEWER_STYLES exactly: "Professional",
"Friendly", "Strict", "Challenging", "Technical".

"Formal" was the old name for "Professional" (renamed so no internal or
user-facing value is called "Formal" anymore). _LEGACY_STYLE_ALIASES
maps it back to "Professional" so an old session/config that still has
"Formal" saved keeps producing a sensible description instead of falling
through to the generic fallback -- new setup submissions can only ever
produce "Professional", since that's what's in app.py's INTERVIEWER_STYLES.
"""

INTERVIEWER_STYLES = {
    "Professional": {
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
            "Warm and conversational",
            "Encouraging",
            "Helps the candidate feel comfortable",
            "Frames weaknesses constructively",
        ],
    },
    "Strict": {
        "label": "Strict",
        "traits": [
            "Direct and demanding",
            "Expects specific answers",
            "Minimal unnecessary praise",
            "Clearly challenges weak responses",
        ],
    },
    "Challenging": {
        "label": "Challenging",
        "traits": [
            "Pushes the candidate to think deeper",
            "Challenges assumptions",
            "Asks probing questions",
            "Encourages detailed reasoning",
        ],
    },
    "Technical": {
        "label": "Technical",
        "traits": [
            "Precise and technically focused",
            "Emphasizes correctness and depth",
            "Uses appropriate technical terminology",
            "Suitable for technical and role-specific interviews",
        ],
    },
}

# Old value -> current value, for sessions/configs saved before the rename.
_LEGACY_STYLE_ALIASES = {"Formal": "Professional"}


def describe_interviewer_style(style):
    """Return a short behavioral description for the given interviewer style."""
    style = _LEGACY_STYLE_ALIASES.get(style, style)
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
