# Speechify plugin for LiveKit Agents

Speechify text-to-speech for [LiveKit Agents](https://docs.livekit.io/agents/). Built on the official [`speechify-api`](https://pypi.org/project/speechify-api/) SDK.

Streaming with word-level timestamps: `stream()` splits input into sentences and issues one `/audio/speech` request per sentence, emitting audio and aligned word timestamps as each sentence completes — near-streaming time-to-first-audio plus word marks (`streaming` and `aligned_transcript` capabilities).

## Installation

```bash
pip install speechify-livekit
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
        voice_id="jack",
        model="simba-english",
    ),
)
```

## Options

| Option | Default | Description |
| --- | --- | --- |
| `voice_id` | `"jack"` | Voice to synthesize with (see the Speechify `/v1/voices` endpoint). |
| `model` | provider default | `simba-english`, `simba-multilingual`, or `simba-3.0`. |
| `language` | provider default | BCP-47 code of the input, e.g. `en-US`. |
| `loudness_normalization` | provider default | Normalize output loudness. |
| `text_normalization` | provider default | Expand numbers/dates into words before synthesis. |
| `tokenizer` | basic sentence tokenizer | Sentence tokenizer used to chunk input in `stream()`. |
| `api_key` | `$SPEECHIFY_API_KEY` | Speechify API key. |
| `base_url` | SDK default | Override the API base URL. |
| `client` | — | Pass a preconfigured `speechify.AsyncSpeechify` client. |

Audio is raw 16-bit little-endian PCM at 24 kHz mono. `simba-3.0` is recommended for the lowest time-to-first-audio.
