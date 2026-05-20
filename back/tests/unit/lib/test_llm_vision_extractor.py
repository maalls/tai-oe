from pathlib import Path

import pytest

from src.lib.llm_vision_extractor import extract_from_pdf_with_vision


class FakeVisionResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def model_dump(self) -> dict:
        return self._payload


class FakeCompletions:
    def __init__(self, payload: dict, fail_once: bool = False):
        self.payload = payload
        self.fail_once = fail_once
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail_once and len(self.calls) == 1 and kwargs.get("response_format"):
            raise RuntimeError("response_format not supported")
        return FakeVisionResponse(self.payload)


class FakeChat:
    def __init__(self, completions: FakeCompletions):
        self.completions = completions


class FakeClientWrapper:
    def __init__(self, completions: FakeCompletions):
        self.chat = FakeChat(completions)


class FakeLLMClient:
    def __init__(self, payload: dict, fail_once: bool = False):
        completions = FakeCompletions(payload=payload, fail_once=fail_once)
        self.client = FakeClientWrapper(completions)
        self.model = "fake-vision-model"


class FakeLLMClientWithExtractor(FakeLLMClient):
    def get_content_text(self, data: dict):
        return data["choices"][0]["message"]["content"]


@pytest.fixture
def fake_pdf(tmp_path: Path) -> Path:
    file_path = tmp_path / "input.pdf"
    file_path.write_bytes(b"%PDF-1.4\n%fake")
    return file_path


def test_extract_from_pdf_with_vision_requires_vision_client(fake_pdf: Path) -> None:
    with pytest.raises(RuntimeError, match="does not support vision"):
        extract_from_pdf_with_vision(
            fake_pdf,
            object(),
            system_prompt="system",
            user_prompt="user",
        )


def test_extract_from_pdf_with_vision_parses_json_response(monkeypatch, fake_pdf: Path) -> None:
    monkeypatch.setattr(
        "src.lib.llm_vision_extractor._render_pdf_to_image_data_urls",
        lambda *_args, **_kwargs: ["data:image/jpeg;base64,abc"],
    )

    payload = {
        "choices": [
            {
                "message": {
                    "content": '{"families": [{"family_code": "A1", "discount": 10}]}'
                }
            }
        ]
    }
    llm_client = FakeLLMClientWithExtractor(payload=payload)

    result = extract_from_pdf_with_vision(
        fake_pdf,
        llm_client,
        system_prompt="system",
        user_prompt="extract this",
    )

    assert result["families"][0]["family_code"] == "A1"


def test_extract_from_pdf_with_vision_retries_without_response_format(monkeypatch, fake_pdf: Path) -> None:
    monkeypatch.setattr(
        "src.lib.llm_vision_extractor._render_pdf_to_image_data_urls",
        lambda *_args, **_kwargs: ["data:image/jpeg;base64,abc"],
    )

    payload = {
        "choices": [
            {
                "message": {
                    "content": '{"families": []}'
                }
            }
        ]
    }
    llm_client = FakeLLMClient(payload=payload, fail_once=True)

    result = extract_from_pdf_with_vision(
        fake_pdf,
        llm_client,
        system_prompt="system",
        user_prompt="extract this",
        json_response=True,
    )

    calls = llm_client.client.chat.completions.calls
    assert len(calls) == 2
    assert "response_format" in calls[0]
    assert "response_format" not in calls[1]
    assert result["families"] == []
