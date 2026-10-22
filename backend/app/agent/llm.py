"""Wrapper fino sobre google-genai.

El resto de la app habla en términos de `Message`, `ToolSpec` y `LLMTurn`; solo este
archivo conoce los tipos de Gemini. `FakeLLM` permite testear sin credenciales.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, TypeVar

from pydantic import BaseModel

from app.config import Settings

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMError(RuntimeError):
    pass


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema


@dataclass
class ToolCall:
    name: str
    args: dict[str, Any]
    id: str | None = None


@dataclass
class ToolResult:
    name: str
    response: dict[str, Any]
    id: str | None = None


@dataclass
class Message:
    role: Literal["user", "model", "tool"]
    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)
    # Contenido original del proveedor. Gemini exige devolver las thought signatures
    # de los function calls tal cual, así que el turno del modelo se reenvía sin tocar.
    raw: Any = None


@dataclass
class LLMTurn:
    text: str | None
    tool_calls: list[ToolCall]
    raw: Any = None


class LLM(Protocol):
    def generate_json(self, prompt: str, schema: type[T], system: str | None = None) -> T: ...

    def chat(self, messages: list[Message], system: str, tools: list[ToolSpec]) -> LLMTurn: ...


class GeminiLLM:
    def __init__(self, settings: Settings):
        from google import genai

        if settings.google_genai_use_vertexai:
            credentials = None
            if settings.google_application_credentials:
                from google.oauth2 import service_account

                credentials = service_account.Credentials.from_service_account_file(
                    str(settings.google_application_credentials.expanduser()),
                    scopes=["https://www.googleapis.com/auth/cloud-platform"],
                )
            self._client = genai.Client(
                vertexai=True,
                project=settings.google_cloud_project,
                location=settings.google_cloud_location,
                credentials=credentials,
            )
        else:
            self._client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model
        self.thinking_level = settings.gemini_thinking_level

    def _thinking(self):
        from google.genai import types

        return types.ThinkingConfig(thinking_level=self.thinking_level) if self.thinking_level else None

    def generate_json(self, prompt: str, schema: type[T], system: str | None = None) -> T:
        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_json_schema=schema.model_json_schema(),
            temperature=0.2,
            thinking_config=self._thinking(),
        )
        try:
            response = self._client.models.generate_content(model=self.model, contents=prompt, config=config)
            return schema.model_validate_json(response.text or "")
        except Exception as e:
            raise LLMError(f"Gemini generate_json falló: {e}") from e

    def chat(self, messages: list[Message], system: str, tools: list[ToolSpec]) -> LLMTurn:
        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=system,
            tools=[
                types.Tool(
                    function_declarations=[
                        types.FunctionDeclaration(
                            name=t.name, description=t.description, parameters_json_schema=t.parameters
                        )
                        for t in tools
                    ]
                )
            ]
            if tools
            else None,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            temperature=0.3,
            thinking_config=self._thinking(),
        )
        contents = [self._to_content(m) for m in messages]
        try:
            response = self._client.models.generate_content(model=self.model, contents=contents, config=config)
        except Exception as e:
            raise LLMError(f"Gemini chat falló: {e}") from e

        if not response.candidates or response.candidates[0].content is None:
            return LLMTurn(text="", tool_calls=[], raw=None)
        content = response.candidates[0].content
        parts = content.parts or []
        text = "".join(p.text for p in parts if p.text and not p.thought)
        calls = [ToolCall(name=fc.name or "", args=dict(fc.args or {}), id=fc.id) for fc in response.function_calls or []]
        return LLMTurn(text=text or None, tool_calls=calls, raw=content)

    @staticmethod
    def _to_content(message: Message):
        from google.genai import types

        if message.role == "model":
            if message.raw is not None:
                return message.raw
            parts = [types.Part(text=message.text or "")]
            parts += [types.Part(function_call=types.FunctionCall(name=c.name, args=c.args, id=c.id)) for c in message.tool_calls]
            return types.Content(role="model", parts=parts)
        if message.role == "tool":
            return types.Content(
                role="user",
                parts=[
                    types.Part(function_response=types.FunctionResponse(name=r.name, response=r.response, id=r.id))
                    for r in message.tool_results
                ],
            )
        return types.Content(role="user", parts=[types.Part(text=message.text or "")])


class FakeLLM:
    """LLM guionizado para tests y para correr sin credenciales.

    - `json_responses`: schema -> instancia o función(prompt) -> instancia. Si falta, lanza LLMError
      (así se ejercitan los fallbacks).
    - `chat_script`: turnos que se devuelven en orden en cada llamada a `chat`.
    """

    def __init__(
        self,
        json_responses: dict[type[BaseModel], BaseModel | Callable[[str], BaseModel]] | None = None,
        chat_script: list[LLMTurn] | None = None,
    ):
        self.json_responses = json_responses or {}
        self.chat_script = list(chat_script or [])
        self.chat_calls: list[dict[str, Any]] = []

    def generate_json(self, prompt: str, schema: type[T], system: str | None = None) -> T:
        response = self.json_responses.get(schema)
        if response is None:
            raise LLMError(f"FakeLLM sin respuesta para {schema.__name__}")
        return response(prompt) if callable(response) else response  # type: ignore[return-value]

    def chat(self, messages: list[Message], system: str, tools: list[ToolSpec]) -> LLMTurn:
        self.chat_calls.append({"messages": list(messages), "system": system, "tools": [t.name for t in tools]})
        if not self.chat_script:
            return LLMTurn(text="(sin respuesta guionizada)", tool_calls=[])
        return self.chat_script.pop(0)


def build_llm(settings: Settings) -> LLM | None:
    if not settings.llm_configured:
        log.warning("LLM no configurado (falta GOOGLE_CLOUD_PROJECT o GEMINI_API_KEY): se usarán fallbacks")
        return None
    try:
        return GeminiLLM(settings)
    except Exception:
        log.exception("No se pudo inicializar Gemini; se usarán fallbacks")
        return None
