"""Calls the Claude API to evaluate an interview answer.

Kept separate from app.py so the Flask routes stay simple. evaluate_answer()
never raises -- if the API key is missing, the API call fails, or the
response can't be parsed, it returns a fallback evaluation instead so the
app keeps working.
"""
import json
import os

import anthropic

MODEL = "claude-opus-5"

# Shown to the user whenever we can't get a real AI evaluation.
FALLBACK_EVALUATION = {
    "scores": {
        "Communication": 7,
        "Clarity": 7,
        "Confidence": 7,
        "Professionalism": 7,
    },
    "overall_score": 7,
    "suggestions": [
        "Use specific examples to support your points.",
        "Keep sentences clear and to the point.",
        "Practice a calm, confident tone.",
    ],
    "is_fallback": True,
    "fallback_reason": None,
}


def _fallback(reason):
    return {**FALLBACK_EVALUATION, "fallback_reason": reason}


SYSTEM_PROMPT = """You are an experienced interview coach evaluating a candidate's \
answer to an interview question. Respond in the requested Language if one is given, \
otherwise respond in English. Match your tone to the Interviewer Style provided.

Reply with ONLY a JSON object (no markdown fences, no extra text) in exactly this shape:
{
  "scores": {
    "Communication": <integer 1-10>,
    "Clarity": <integer 1-10>,
    "Confidence": <integer 1-10>,
    "Professionalism": <integer 1-10>
  },
  "overall_score": <integer 1-10>,
  "suggestions": ["<short improvement tip>", "<short improvement tip>", "<short improvement tip>"]
}"""


def _build_prompt(config, question, answer):
    lines = [
        f"Job Role: {config.get('job_role') or 'Not specified'}",
        f"Experience Level: {config.get('experience_level') or 'Not specified'}",
        f"Interview Type: {config.get('interview_type') or 'Not specified'}",
        f"Difficulty: {config.get('difficulty') or 'Not specified'}",
        f"Language: {config.get('language') or 'English'}",
        f"Interviewer Style: {config.get('interviewer_style') or 'Not specified'}",
    ]
    if config.get("job_description"):
        lines.append(f"Job Description: {config['job_description']}")
    if config.get("custom_instructions"):
        lines.append(f"Custom Instructions: {config['custom_instructions']}")

    lines.append(f"\nInterview Question: {question}")
    lines.append(f"\nCandidate's Answer: {answer}")
    return "\n".join(lines)


def evaluate_answer(config, question, answer):
    """Return an evaluation dict for the given answer.

    Shape: {"scores": {...}, "overall_score": int, "suggestions": [...],
    "is_fallback": bool, "fallback_reason": str | None}
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return _fallback("AI evaluation is not configured (missing API key). Showing a placeholder evaluation instead.")

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            output_config={"effort": "low"},
            messages=[{"role": "user", "content": _build_prompt(config, question, answer)}],
        )
    except anthropic.RateLimitError:
        return _fallback("The AI service is busy right now. Showing a placeholder evaluation instead.")
    except anthropic.APIStatusError:
        return _fallback("The AI service returned an error. Showing a placeholder evaluation instead.")
    except anthropic.APIConnectionError:
        return _fallback("Could not reach the AI service. Showing a placeholder evaluation instead.")
    except Exception:
        return _fallback("Something went wrong generating your evaluation. Showing a placeholder evaluation instead.")

    text = "".join(block.text for block in response.content if block.type == "text").strip()

    # The model sometimes wraps JSON in a code fence despite instructions -- strip it.
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        result = json.loads(text)
        scores = {str(k): int(v) for k, v in result["scores"].items()}
        overall_score = int(result["overall_score"])
        suggestions = [str(s) for s in result["suggestions"]]
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return _fallback("Received an unexpected response from the AI. Showing a placeholder evaluation instead.")

    return {
        "scores": scores,
        "overall_score": overall_score,
        "suggestions": suggestions,
        "is_fallback": False,
        "fallback_reason": None,
    }
