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

import os
from dataclasses import dataclass, replace

from livekit.agents import (
    APIConnectionError,
    APIConnectOptions,
    APIStatusError,
    APITimeoutError,
    tts,
    utils,
)
from livekit.agents.types import (
    DEFAULT_API_CONNECT_OPTIONS,
    NOT_GIVEN,
    NotGivenOr,
)
from livekit.agents.utils import is_given

from speechify.client import AsyncSpeechify
from speechify.core.api_error import ApiError

from .models import TTSEncoding, TTSModels

DEFAULT_VOICE_ID = "jack"
DEFAULT_ENCODING: TTSEncoding = "ogg_24000"

_ACCEPT_BY_FORMAT = {
    "mp3": "audio/mpeg",
    "ogg": "audio/ogg",
    "aac": "audio/aac",
    "pcm": "audio/pcm",
}


def _format_from_encoding(encoding: TTSEncoding) -> str:
    return encoding.split("_", 1)[0]


def _sample_rate_from_encoding(encoding: TTSEncoding) -> int:
    return int(encoding.split("_", 1)[1])


def _mime_type_from_encoding(encoding: TTSEncoding) -> str:
    fmt = _format_from_encoding(encoding)
    accept = _ACCEPT_BY_FORMAT[fmt]
    if fmt == "pcm":
        return f"audio/pcm;rate={_sample_rate_from_encoding(encoding)}"
    return accept


@dataclass
class _TTSOptions:
    voice_id: str
    encoding: TTSEncoding
    model: NotGivenOr[TTSModels]
    language: NotGivenOr[str]
    loudness_normalization: NotGivenOr[bool]
    text_normalization: NotGivenOr[bool]
    sample_rate: int


class TTS(tts.TTS):
    def __init__(
        self,
        *,
        voice_id: str = DEFAULT_VOICE_ID,
        encoding: NotGivenOr[TTSEncoding] = NOT_GIVEN,
        model: NotGivenOr[TTSModels] = NOT_GIVEN,
        language: NotGivenOr[str] = NOT_GIVEN,
        loudness_normalization: NotGivenOr[bool] = NOT_GIVEN,
        text_normalization: NotGivenOr[bool] = NOT_GIVEN,
        api_key: NotGivenOr[str] = NOT_GIVEN,
        base_url: NotGivenOr[str] = NOT_GIVEN,
        client: AsyncSpeechify | None = None,
    ) -> None:
        """Create a new instance of Speechify TTS.

        Args:
            voice_id: Id of the voice to synthesize with. See the Speechify
                ``/v1/voices`` endpoint for the available voices.
            encoding: Audio encoding to request, as ``<format>_<rate>`` (e.g.
                ``ogg_24000``). Defaults to ``ogg_24000``.
            model: Synthesis model. One of ``simba-english``,
                ``simba-multilingual`` or ``simba-3.0``.
            language: BCP-47 language code of the input (e.g. ``en-US``).
            loudness_normalization: Normalize output loudness to a standard
                level. Increases latency slightly when enabled.
            text_normalization: Expand numbers, dates, etc. into words before
                synthesis. Increases latency slightly when enabled.
            api_key: Speechify API key. Falls back to the ``SPEECHIFY_API_KEY``
                environment variable.
            base_url: Override the Speechify API base URL.
            client: A preconfigured ``AsyncSpeechify`` client. When provided,
                ``api_key`` and ``base_url`` are ignored.
        """
        if not is_given(encoding):
            encoding = DEFAULT_ENCODING

        sample_rate = _sample_rate_from_encoding(encoding)
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=sample_rate,
            num_channels=1,
        )

        if client is not None:
            self._client = client
        else:
            token = api_key if is_given(api_key) else os.environ.get("SPEECHIFY_API_KEY")
            if not token:
                raise ValueError(
                    "Speechify API key is required, either as the api_key argument "
                    "or via the SPEECHIFY_API_KEY environment variable"
                )
            self._client = AsyncSpeechify(
                api_key=token,
                base_url=base_url if is_given(base_url) else None,
            )

        self._opts = _TTSOptions(
            voice_id=voice_id,
            encoding=encoding,
            model=model,
            language=language,
            loudness_normalization=loudness_normalization,
            text_normalization=text_normalization,
            sample_rate=sample_rate,
        )

    @property
    def model(self) -> str:
        return self._opts.model if is_given(self._opts.model) else "unknown"

    @property
    def provider(self) -> str:
        return "Speechify"

    def update_options(
        self,
        *,
        voice_id: NotGivenOr[str] = NOT_GIVEN,
        model: NotGivenOr[TTSModels] = NOT_GIVEN,
        language: NotGivenOr[str] = NOT_GIVEN,
        loudness_normalization: NotGivenOr[bool] = NOT_GIVEN,
        text_normalization: NotGivenOr[bool] = NOT_GIVEN,
    ) -> None:
        if is_given(voice_id):
            self._opts.voice_id = voice_id
        if is_given(model):
            self._opts.model = model
        if is_given(language):
            self._opts.language = language
        if is_given(loudness_normalization):
            self._opts.loudness_normalization = loudness_normalization
        if is_given(text_normalization):
            self._opts.text_normalization = text_normalization

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> ChunkedStream:
        return ChunkedStream(tts=self, input_text=text, conn_options=conn_options)


class ChunkedStream(tts.ChunkedStream):
    def __init__(self, *, tts: TTS, input_text: str, conn_options: APIConnectOptions) -> None:
        super().__init__(tts=tts, input_text=input_text, conn_options=conn_options)
        self._tts: TTS = tts
        self._opts = replace(tts._opts)

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        opts = self._opts
        options: dict[str, bool] = {}
        if is_given(opts.loudness_normalization):
            options["loudness_normalization"] = opts.loudness_normalization
        if is_given(opts.text_normalization):
            options["text_normalization"] = opts.text_normalization

        request: dict[str, object] = {
            "accept": _ACCEPT_BY_FORMAT[_format_from_encoding(opts.encoding)],
            "input": self._input_text,
            "voice_id": opts.voice_id,
        }
        if is_given(opts.model):
            request["model"] = opts.model
        if is_given(opts.language):
            request["language"] = opts.language
        if options:
            request["options"] = options

        try:
            output_emitter.initialize(
                request_id=utils.shortuuid(),
                sample_rate=opts.sample_rate,
                num_channels=1,
                mime_type=_mime_type_from_encoding(opts.encoding),
            )

            stream = self._tts._client.audio.stream(
                **request,
                request_options={"timeout_in_seconds": int(self._conn_options.timeout)},
            )
            async for chunk in stream:
                output_emitter.push(chunk)

            output_emitter.flush()

        except ApiError as e:
            raise APIStatusError(
                message=str(e.body) if e.body is not None else "Speechify API error",
                status_code=e.status_code or -1,
                request_id=None,
                body=None,
            ) from None
        except TimeoutError:
            raise APITimeoutError() from None
        except Exception as e:
            raise APIConnectionError() from e
