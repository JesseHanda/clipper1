from types import SimpleNamespace

import anthropic
import httpx2
import pytest
from pydantic import BaseModel

from clipper import llm


class Answer(BaseModel):
    text: str


def _response(parsed=None, stop_reason="end_turn"):
    return SimpleNamespace(
        parsed_output=parsed, stop_reason=stop_reason, model="m", _request_id="req_1"
    )


class FakeClient:
    """Mimics client.beta.messages.parse, returning/raising queued results in order."""

    def __init__(self, *results):
        self.results = list(results)
        self.calls = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(parse=self._parse))

    def _parse(self, **kwargs):
        self.calls.append(kwargs)
        r = self.results.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def _status_error(cls, code):
    req = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    return cls("boom", response=httpx2.Response(code, request=req), body=None)


def test_returns_parsed_model_and_sends_expected_params():
    client = FakeClient(_response(Answer(text="hi")))
    out = llm.ask_json("sys", "prompt", Answer, client=client)
    assert out == Answer(text="hi")
    call = client.calls[0]
    assert call["output_format"] is Answer
    assert call["fallbacks"] == "default"
    assert llm.FALLBACK_BETA in call["betas"]
    assert call["system"] == "sys"


def test_retries_once_when_output_invalid():
    client = FakeClient(_response(None), _response(Answer(text="ok")))
    assert llm.ask_json("s", "p", Answer, client=client).text == "ok"
    assert len(client.calls) == 2


def test_raises_after_all_attempts_invalid():
    client = FakeClient(_response(None), _response(None))
    with pytest.raises(llm.LLMError, match="schema"):
        llm.ask_json("s", "p", Answer, client=client)


def test_refusal_raises_without_retry():
    client = FakeClient(_response(stop_reason="refusal"))
    with pytest.raises(llm.LLMError, match="refusal"):
        llm.ask_json("s", "p", Answer, client=client)
    assert len(client.calls) == 1


def test_max_tokens_raises():
    client = FakeClient(_response(stop_reason="max_tokens"))
    with pytest.raises(llm.LLMError, match="cut off"):
        llm.ask_json("s", "p", Answer, client=client)


def test_rate_limit_is_retried():
    client = FakeClient(_status_error(anthropic.RateLimitError, 429), _response(Answer(text="ok")))
    assert llm.ask_json("s", "p", Answer, client=client).text == "ok"


def test_bad_request_is_not_retried():
    client = FakeClient(_status_error(anthropic.BadRequestError, 400))
    with pytest.raises(llm.LLMError, match="rejected"):
        llm.ask_json("s", "p", Answer, client=client)
    assert len(client.calls) == 1
