# Speechify plugin for LiveKit Agents

Speechify text-to-speech for [LiveKit Agents](https://docs.livekit.io/agents/). Built on the official [`speechify-api`](https://pypi.org/project/speechify-api/) SDK.

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
        voice_id="jack",
        model="simba-english",
    ),
)
```

## Options

| Option | Default | Description |
| --- | --- | --- |
| `voice_id` | `"jack"` | Voice to synthesize with (see the Speechify `/v1/voices` endpoint). |
| `encoding` | `"ogg_24000"` | `<format>_<rate>`. One of `mp3_24000`, `ogg_24000`, `aac_24000`, `pcm_24000`. |
| `model` | provider default | `simba-english`, `simba-multilingual`, or `simba-3.0`. |
| `language` | provider default | BCP-47 code of the input, e.g. `en-US`. |
| `loudness_normalization` | provider default | Normalize output loudness. |
| `text_normalization` | provider default | Expand numbers/dates into words before synthesis. |
| `api_key` | `$SPEECHIFY_API_KEY` | Speechify API key. |
| `base_url` | SDK default | Override the API base URL. |
| `client` | — | Pass a preconfigured `speechify.AsyncSpeechify` client. |

`pcm_24000` returns raw 16-bit little-endian PCM (24 kHz mono) for the lowest-latency path with no decoding.
