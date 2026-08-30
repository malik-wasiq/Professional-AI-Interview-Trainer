"""Tests for OpenRouter-backed question generation and its fallback behavior.

No real network calls are made -- every requests.post() call is mocked.
Uses unittest (stdlib) rather than pytest so no new dependency is needed.
"""
import io
import contextlib
import unittest
from unittest import mock

import requests

import question_generator as qg


SAMPLE_CONFIG = {
    "job_role": "Software Engineer",
    "interview_type": "Technical",
    "difficulty": "Medium",
    "experience_level": "Mid-Level",
    "language": "English",
    "interviewer_style": "Professional",
    "custom_instructions": "",
    "job_description": "",
}

FAKE_API_KEY = "sk-or-v1-super-secret-test-key-should-never-leak"
FAKE_API_KEY_2 = "sk-or-v1-second-super-secret-test-key-should-never-leak"


def _mock_response(status_code=200, json_data=None, ok=None):
    response = mock.Mock()
    response.status_code = status_code
    response.ok = ok if ok is not None else 200 <= status_code < 400
    if json_data is not None:
        response.json.return_value = json_data
    return response


class GenerateAIQuestionTests(unittest.TestCase):
    """Covers _generate_ai_question() / generate_question() directly."""

    def test_missing_api_key_falls_back_to_static(self):
        with mock.patch.dict("os.environ", {}, clear=True), \
             mock.patch.object(qg, "MODEL", "some-model"), \
             mock.patch.object(qg, "requests") as mocked_requests:
            question = qg.generate_question(SAMPLE_CONFIG, history=[])
            mocked_requests.post.assert_not_called()
        self.assertTrue(_is_from_static_bank(question, SAMPLE_CONFIG))

    def test_missing_model_falls_back_to_static(self):
        with mock.patch.dict("os.environ", {"OPENROUTER_API_KEY": FAKE_API_KEY}), \
             mock.patch.object(qg, "MODEL", None), \
             mock.patch.object(qg, "requests") as mocked_requests:
            question = qg.generate_question(SAMPLE_CONFIG, history=[])
            mocked_requests.post.assert_not_called()
        self.assertTrue(_is_from_static_bank(question, SAMPLE_CONFIG))

    def test_successful_response_returns_ai_question(self):
        ai_text = "Describe a time you optimized a slow database query."
        response = _mock_response(200, {"choices": [{"message": {"content": ai_text}}]})
        with _configured_env(), mock.patch.object(qg.requests, "post", return_value=response) as post:
            question = qg.generate_question(SAMPLE_CONFIG, history=[])
        post.assert_called_once()
        self.assertEqual(question, ai_text)

    def test_empty_ai_response_falls_back(self):
        response = _mock_response(200, {"choices": [{"message": {"content": "   "}}]})
        with _configured_env(), mock.patch.object(qg.requests, "post", return_value=response):
            question = qg.generate_question(SAMPLE_CONFIG, history=[])
        self.assertTrue(_is_from_static_bank(question, SAMPLE_CONFIG))

    def test_malformed_response_falls_back(self):
        # Missing the expected "choices" key entirely.
        response = _mock_response(200, {"unexpected": "shape"})
        with _configured_env(), mock.patch.object(qg.requests, "post", return_value=response):
            question = qg.generate_question(SAMPLE_CONFIG, history=[])
        self.assertTrue(_is_from_static_bank(question, SAMPLE_CONFIG))

    def test_duplicate_ai_question_falls_back(self):
        already_asked = "Tell me about a time you optimized a query."
        response = _mock_response(
            200, {"choices": [{"message": {"content": already_asked}}]}
        )
        with _configured_env(), mock.patch.object(qg.requests, "post", return_value=response):
            question = qg.generate_question(SAMPLE_CONFIG, history=[already_asked])
        self.assertTrue(_is_from_static_bank(question, SAMPLE_CONFIG))
        self.assertNotEqual(question, already_asked)

    def test_http_429_falls_back(self):
        response = _mock_response(429)
        with _configured_env(), mock.patch.object(qg.requests, "post", return_value=response):
            question = qg.generate_question(SAMPLE_CONFIG, history=[])
        self.assertTrue(_is_from_static_bank(question, SAMPLE_CONFIG))

    def test_http_500_falls_back(self):
        response = _mock_response(500)
        with _configured_env(), mock.patch.object(qg.requests, "post", return_value=response):
            question = qg.generate_question(SAMPLE_CONFIG, history=[])
        self.assertTrue(_is_from_static_bank(question, SAMPLE_CONFIG))

    def test_timeout_falls_back(self):
        with _configured_env(), mock.patch.object(
            qg.requests, "post", side_effect=requests.exceptions.Timeout("timed out")
        ):
            question = qg.generate_question(SAMPLE_CONFIG, history=[])
        self.assertTrue(_is_from_static_bank(question, SAMPLE_CONFIG))

    def test_connection_error_falls_back(self):
        with _configured_env(), mock.patch.object(
            qg.requests, "post", side_effect=requests.exceptions.ConnectionError("no route")
        ):
            question = qg.generate_question(SAMPLE_CONFIG, history=[])
        self.assertTrue(_is_from_static_bank(question, SAMPLE_CONFIG))

    def test_no_ai_call_still_avoids_repeats_in_static_bank(self):
        # Existing static selection behavior must be unaffected.
        with mock.patch.dict("os.environ", {}, clear=True), mock.patch.object(qg, "MODEL", None):
            history = []
            for _ in range(5):
                q = qg.generate_question(SAMPLE_CONFIG, history=history)
                self.assertNotIn(q, history)
                history.append(q)

    def test_api_key_never_appears_in_output_or_exceptions(self):
        """Force a failure path and make sure the key never leaks anywhere."""
        captured_out = io.StringIO()
        captured_err = io.StringIO()

        def _raise(*args, **kwargs):
            raise requests.exceptions.ConnectionError("connection refused")

        with _configured_env(), mock.patch.object(qg.requests, "post", side_effect=_raise), \
             contextlib.redirect_stdout(captured_out), contextlib.redirect_stderr(captured_err):
            try:
                question = qg.generate_question(SAMPLE_CONFIG, history=[])
            except Exception as exc:  # generate_question must never raise
                self.fail(f"generate_question raised unexpectedly: {exc!r}")

        self.assertTrue(_is_from_static_bank(question, SAMPLE_CONFIG))
        combined_output = captured_out.getvalue() + captured_err.getvalue()
        self.assertNotIn(FAKE_API_KEY, combined_output)


class SecondKeyRetryTests(unittest.TestCase):
    """Covers the OPENROUTER_API_KEY_2 retry-on-429 behavior."""

    def test_success_on_first_key_never_touches_second_key(self):
        ai_text = "What's a time you improved an existing process?"
        response = _mock_response(200, {"choices": [{"message": {"content": ai_text}}]})
        with _configured_env(), \
             mock.patch.dict("os.environ", {"OPENROUTER_API_KEY_2": FAKE_API_KEY_2}), \
             mock.patch.object(qg.requests, "post", return_value=response) as post:
            question = qg.generate_question(SAMPLE_CONFIG, history=[])
        self.assertEqual(post.call_count, 1)
        self.assertEqual(question, ai_text)

    def test_429_on_first_key_retries_with_second_key_and_succeeds(self):
        ai_text = "Describe your approach to debugging a flaky test."
        first_response = _mock_response(429)
        second_response = _mock_response(200, {"choices": [{"message": {"content": ai_text}}]})

        with _configured_env(), \
             mock.patch.dict("os.environ", {"OPENROUTER_API_KEY_2": FAKE_API_KEY_2}), \
             mock.patch.object(qg.requests, "post", side_effect=[first_response, second_response]) as post:
            question = qg.generate_question(SAMPLE_CONFIG, history=[])

        self.assertEqual(post.call_count, 2)
        self.assertEqual(question, ai_text)
        # The retry must use the second key's Authorization header, not the first's.
        second_call_headers = post.call_args_list[1].kwargs["headers"]
        self.assertIn(FAKE_API_KEY_2, second_call_headers["Authorization"])

    def test_429_on_first_key_with_no_second_key_configured_falls_back(self):
        response = _mock_response(429)
        with _configured_env(), \
             mock.patch.dict("os.environ", {}, clear=False), \
             mock.patch.object(qg.requests, "post", return_value=response) as post:
            # Make sure no leftover OPENROUTER_API_KEY_2 is set from the environment.
            import os as _os
            _os.environ.pop("OPENROUTER_API_KEY_2", None)
            question = qg.generate_question(SAMPLE_CONFIG, history=[])
        self.assertEqual(post.call_count, 1)
        self.assertTrue(_is_from_static_bank(question, SAMPLE_CONFIG))

    def test_429_on_both_keys_falls_back(self):
        first_response = _mock_response(429)
        second_response = _mock_response(429)
        with _configured_env(), \
             mock.patch.dict("os.environ", {"OPENROUTER_API_KEY_2": FAKE_API_KEY_2}), \
             mock.patch.object(qg.requests, "post", side_effect=[first_response, second_response]) as post:
            question = qg.generate_question(SAMPLE_CONFIG, history=[])
        self.assertEqual(post.call_count, 2)
        self.assertTrue(_is_from_static_bank(question, SAMPLE_CONFIG))


def _configured_env():
    return _EnvAndModel(FAKE_API_KEY, "test/model-1")


class _EnvAndModel:
    """Context manager that sets both the env var and the module-level MODEL.

    MODEL is read once at import time in question_generator.py, so patching
    only os.environ isn't enough -- tests need to patch the module attribute
    too to simulate a configured model.
    """

    def __init__(self, api_key, model_name):
        self._api_key = api_key
        self._model_name = model_name
        self._env_patch = None
        self._model_patch = None

    def __enter__(self):
        self._env_patch = mock.patch.dict("os.environ", {"OPENROUTER_API_KEY": self._api_key})
        self._model_patch = mock.patch.object(qg, "MODEL", self._model_name)
        self._env_patch.__enter__()
        self._model_patch.__enter__()
        return self

    def __exit__(self, *exc_info):
        self._model_patch.__exit__(*exc_info)
        self._env_patch.__exit__(*exc_info)


def _is_from_static_bank(question, config):
    pool = qg._pick_from_static_bank(
        config["interview_type"], config["difficulty"], config["job_role"], already_asked=[]
    )
    # _pick_from_static_bank returns a single random pick; instead check
    # membership against the full pool directly.
    if config["interview_type"] == "Role-Specific":
        full_pool = [t.format(role=config["job_role"]) for t in qg.ROLE_SPECIFIC_TEMPLATES[config["difficulty"]]]
    elif config["interview_type"] == "Mixed":
        full_pool = (
            qg.INTERVIEW_QUESTIONS["HR / Behavioral"][config["difficulty"]]
            + qg.INTERVIEW_QUESTIONS["Technical"][config["difficulty"]]
            + qg.INTERVIEW_QUESTIONS["Situational"][config["difficulty"]]
        )
    else:
        full_pool = qg.INTERVIEW_QUESTIONS[config["interview_type"]][config["difficulty"]]
    return question in full_pool


class FullInterviewFlowTests(unittest.TestCase):
    """End-to-end Flask flow, confirming the app still works with and without an AI key."""

    def setUp(self):
        import app as app_module
        self.app_module = app_module
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()

    def _complete_interview(self):
        setup_response = self.client.post(
            "/setup",
            data={
                "job_role": "Software Engineer",
                "interview_type": "Technical",
                "difficulty": "Easy",
                "experience_level": "Entry-Level",
                "language": "English",
                "interviewer_style": "Professional",
                "custom_instructions": "",
                "job_description": "",
            },
            follow_redirects=True,
        )
        self.assertEqual(setup_response.status_code, 200)

        for _ in range(5):
            response = self.client.post(
                "/interview", data={"answer": "This is my answer."}, follow_redirects=True
            )
            self.assertEqual(response.status_code, 200)

        return response

    def test_five_question_flow_reaches_results_without_api_key(self):
        with mock.patch.dict("os.environ", {}, clear=True), \
             mock.patch.object(qg, "MODEL", None):
            final_response = self._complete_interview()
        self.assertIn(b"Results", final_response.data)

    def test_five_question_flow_reaches_results_with_mocked_ai(self):
        ai_texts = [f"AI-generated question number {i}?" for i in range(1, 6)]
        response = _mock_response(200, {"choices": [{"message": {"content": ai_texts[0]}}]})

        call_count = {"n": 0}

        def _post(*args, **kwargs):
            idx = min(call_count["n"], len(ai_texts) - 1)
            call_count["n"] += 1
            return _mock_response(200, {"choices": [{"message": {"content": ai_texts[idx]}}]})

        with _configured_env(), mock.patch.object(qg.requests, "post", side_effect=_post):
            final_response = self._complete_interview()
        self.assertIn(b"Results", final_response.data)


if __name__ == "__main__":
    unittest.main()
