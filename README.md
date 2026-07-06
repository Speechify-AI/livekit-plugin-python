# Speechify plugin for LiveKit Agents (Python)

Speechify text-to-speech for [LiveKit Agents](https://docs.livekit.io/agents/), maintained by Speechify.

> **This repository is the maintenance source for the plugin. Distribution is handled by LiveKit.**
>
> The plugin ships inside the [`livekit/agents`](https://github.com/livekit/agents) monorepo and is published to PyPI by LiveKit as [`livekit-plugins-speechify`](https://pypi.org/project/livekit-plugins-speechify/). This repo mirrors that code so Speechify can maintain it, triage issues, and propose changes upstream. Bugs and contributions specific to the Speechify plugin are welcome here; releases are cut by LiveKit.

## Installation

```bash
pip install livekit-plugins-speechify
```

## Authentication

Set your Speechify API key via the environment:

```bash
export SPEECHIFY_API_KEY="your-api-key"
```

Or pass it directly with `api_key=...`.

## Usage

```python
from livekit.agents import AgentSession
from livekit.plugins import speechify

session = AgentSession(
    tts=speechify.TTS(
        voice_id="dominic_32",
        model="simba-3.2",
    ),
)
```

## Options

| Option | Default | Description |
| --- | --- | --- |
| `voice_id` | `"dominic_32"` | Voice to synthesize with (see the Speechify `/v1/voices` endpoint). |
| `model` | provider default | `simba-english`, `simba-multilingual`, `simba-3.0`, or `simba-3.2` (default). |
| `language` | provider default | BCP-47 code of the input, e.g. `en-US`. |
| `loudness_normalization` | provider default | Normalize output loudness. |
| `text_normalization` | provider default | Expand numbers/dates into words before synthesis. |
| `tokenizer` | basic sentence tokenizer | Sentence tokenizer used to chunk input in `stream()`. |
| `api_key` | `$SPEECHIFY_API_KEY` | Speechify API key. |
| `base_url` | SDK default | Override the API base URL. |
| `client` | — | Pass a preconfigured `speechify.AsyncSpeechify` client. |

## How it works

Built on the official [`speechify-api`](https://pypi.org/project/speechify-api/) SDK. `stream()` splits input into sentences and issues one `/audio/speech` request per sentence, emitting audio and aligned word-level timestamps as each sentence completes — near-streaming time-to-first-audio plus word marks (`streaming` and `aligned_transcript` capabilities). Audio is raw 16-bit little-endian PCM at 24 kHz mono; `simba-3.2` is the default and recommended for the lowest time-to-first-audio.

## Run it locally

A smoke runner exercises both synthesis paths against the live API (no LiveKit room needed), writes WAV files, and prints word timestamps + time-to-first-audio:

```bash
export SPEECHIFY_API_KEY="your-api-key"
pip install -e .
python scripts/synthesize.py "Hello from Speechify."
```

## Maintainers

Maintained by Speechify. Published and distributed by LiveKit as part of [`livekit/agents`](https://github.com/livekit/agents).
