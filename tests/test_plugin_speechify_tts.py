# Copyright 2024 Speechify, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import base64
import os
from dataclasses import dataclass

import pytest
from livekit.agents import APIStatusError

from livekit.plugins import speechify

pytestmark = pytest.mark.plugin("speechify")

SAMPLE_RATE = 24000


def _pcm_b64(seconds: float) -> str:
    return base64.b64encode(b"\x00\x00" * int(seconds * SAMPLE_RATE)).decode()


@dataclass
class _Chunk:
    value: str
    start_time: float
    end_time: float


@dataclass
class _Marks:
    chunks: list[_Chunk]


@dataclass
class _SpeechResponse:
    audio_data: str
    speech_marks: _Marks


class _FakeAudio:
    def __init__(self, responder):
        self._responder = responder

    async def speech(self, **kwargs):
        return self._responder(kwargs)


class _FakeClient:
    def __init__(self, responder):
        self.audio = _FakeAudio(responder)


def _marks(words: list[tuple[str, float, float]]) -> _Marks:
    return _Marks(chunks=[_Chunk(v, s, e) for v, s, e in words])


async def _collect(stream):
    frames = 0
    samples = 0
    words: list[tuple[str, float]] = []
    async for ev in stream:
        frames += 1
        samples += ev.frame.samples_per_channel
        for w in ev.frame.userdata.get("lk.timed_transcripts", []):
            words.append((str(w), w.start_time))
    return frames, samples, words


def test_requires_api_key():
    prev = os.environ.pop("SPEECHIFY_API_KEY", None)
    try:
        with pytest.raises(ValueError, match="API key is required"):
            speechify.TTS()
    finally:
        if prev is not None:
            os.environ["SPEECHIFY_API_KEY"] = prev


def test_capabilities():
    tts = speechify.TTS(api_key="sk_test", client=_FakeClient(lambda _: None))
    assert tts.capabilities.streaming is True
    assert tts.capabilities.aligned_transcript is True
    assert tts.sample_rate == SAMPLE_RATE
    assert tts.num_channels == 1
    assert tts.provider == "Speechify"


async def test_synthesize_emits_frames_and_marks():
    def responder(_kwargs):
        return _SpeechResponse(
            audio_data=_pcm_b64(1.0),
            speech_marks=_marks([("Hello", 0, 500), ("world.", 500, 1000)]),
        )

    tts = speechify.TTS(api_key="sk_test", client=_FakeClient(responder))
    frames, samples, words = await _collect(tts.synthesize("Hello world."))

    assert frames > 0
    assert samples == pytest.approx(SAMPLE_RATE, abs=SAMPLE_RATE // 10)
    assert [w[0] for w in words] == ["Hello", "world."]
    assert words[0][1] == pytest.approx(0.0)
    assert words[1][1] == pytest.approx(0.5)


async def test_stream_offsets_marks_across_sentences():
    first = "The quick brown fox jumps over the lazy dog."
    second = "Pack my box with five dozen liquor jugs now."
    responses = {
        first: _SpeechResponse(_pcm_b64(1.0), _marks([("The", 0, 400), ("dog.", 400, 900)])),
        second: _SpeechResponse(_pcm_b64(1.0), _marks([("Pack", 0, 400), ("now.", 400, 800)])),
    }

    def responder(kwargs):
        return responses[kwargs["input"].strip()]

    tts = speechify.TTS(api_key="sk_test", client=_FakeClient(responder))
    stream = tts.stream()
    stream.push_text(f"{first} {second}")
    stream.flush()
    stream.end_input()

    _frames, samples, words = await _collect(stream)

    assert [w[0] for w in words] == ["The", "dog.", "Pack", "now."]
    assert words[2][1] == pytest.approx(1.0)
    assert words[3][1] == pytest.approx(1.4)
    times = [w[1] for w in words]
    assert times == sorted(times)
    assert samples == pytest.approx(SAMPLE_RATE * 2, abs=SAMPLE_RATE // 5)


async def test_maps_error_to_api_status_error():
    from speechify.core.api_error import ApiError

    def responder(_kwargs):
        raise ApiError(status_code=429, body={"error": {"message": "boom"}})

    tts = speechify.TTS(api_key="sk_test", client=_FakeClient(responder))
    with pytest.raises(APIStatusError) as exc:
        await _collect(tts.synthesize("fails"))
    assert exc.value.status_code == 429


@pytest.mark.skipif(not os.environ.get("SPEECHIFY_API_KEY"), reason="requires SPEECHIFY_API_KEY")
async def test_live_stream_monotonic_marks():
    tts = speechify.TTS(voice_id="jack", model="simba-3.0")
    stream = tts.stream()
    stream.push_text(
        "The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs now."
    )
    stream.flush()
    stream.end_input()

    frames, samples, words = await _collect(stream)
    assert frames > 0
    assert samples > 0
    assert len(words) > 0
    times = [w[1] for w in words]
    assert times == sorted(times)
