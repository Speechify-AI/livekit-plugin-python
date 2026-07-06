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

"""Local smoke runner for the Speechify TTS plugin.

Synthesizes text against the live Speechify API (no LiveKit room required),
writes a WAV file, and prints the word-level timestamps and time-to-first-audio
for both the one-shot ``synthesize()`` and the streamed ``stream()`` paths.

Usage:
    export SPEECHIFY_API_KEY=...
    python scripts/synthesize.py "Hello from Speechify."
"""

from __future__ import annotations

import asyncio
import sys
import time
import wave

from livekit.agents.types import USERDATA_TIMED_TRANSCRIPT
from livekit.plugins import speechify

SAMPLE_RATE = 24000
NUM_CHANNELS = 1


def _write_wav(path: str, frames: list) -> None:
    with wave.open(path, "wb") as w:
        w.setnchannels(NUM_CHANNELS)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        for frame in frames:
            w.writeframes(bytes(frame.data))


async def main() -> None:
    text = sys.argv[1] if len(sys.argv) > 1 else "Hello from the Speechify LiveKit plugin."
    tts = speechify.TTS()
    print(f"provider={tts.provider} model={tts.model} sample_rate={tts.sample_rate}")

    print("\n== synthesize() ==")
    started = time.monotonic()
    ttfb = None
    frames = []
    words = []
    async for ev in tts.synthesize(text):
        if ttfb is None:
            ttfb = time.monotonic() - started
        frames.append(ev.frame)
        for w in ev.frame.userdata.get(USERDATA_TIMED_TRANSCRIPT, []):
            words.append((str(w), w.start_time))
    _write_wav("synthesize.wav", frames)
    dur = sum(f.samples_per_channel for f in frames) / SAMPLE_RATE
    print(f"  ttfb={ttfb:.2f}s audio={dur:.2f}s frames={len(frames)} -> synthesize.wav")
    print(f"  words: {' '.join(f'{t}@{s:.2f}' for t, s in words)}")

    print("\n== stream() ==")
    stream = tts.stream()
    stream.push_text(text)
    stream.end_input()
    started = time.monotonic()
    ttfb = None
    frames = []
    words = []
    async for ev in stream:
        if ttfb is None:
            ttfb = time.monotonic() - started
        frames.append(ev.frame)
        for w in ev.frame.userdata.get(USERDATA_TIMED_TRANSCRIPT, []):
            words.append((str(w), w.start_time))
    await stream.aclose()
    _write_wav("stream.wav", frames)
    dur = sum(f.samples_per_channel for f in frames) / SAMPLE_RATE
    print(f"  ttfb={ttfb:.2f}s audio={dur:.2f}s frames={len(frames)} -> stream.wav")
    print(f"  words: {' '.join(f'{t}@{s:.2f}' for t, s in words)}")


if __name__ == "__main__":
    asyncio.run(main())
