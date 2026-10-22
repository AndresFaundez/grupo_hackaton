"""Loop del agente: el LLM pide herramientas, el backend las ejecuta y registra la traza."""

from __future__ import annotations

import logging

from app.agent.llm import LLM, Message, ToolResult
from app.agent.prompts import analyst_system, persona_system
from app.agent.tools import TOOL_SPECS, ToolOutcome, execute_tool
from app.config import Settings
from app.models import ChatRequest, ChatResponse, ToolCallTrace
from app.store import ChatSession, ClusteringRecord, Store, new_id

log = logging.getLogger(__name__)

PERSONA_TOOLS = ["describe_cluster"]
OUT_OF_STEPS = "No alcancé a terminar el análisis con los pasos disponibles. ¿Puedes acotar un poco la pregunta?"


class ChatUnavailable(RuntimeError):
    pass


class ChatService:
    def __init__(self, llm: LLM | None, store: Store, settings: Settings):
        self.llm = llm
        self.store = store
        self.settings = settings

    def chat(self, record: ClusteringRecord, req: ChatRequest) -> ChatResponse:
        if self.llm is None:
            raise ChatUnavailable("El LLM no está configurado (revisa GOOGLE_CLOUD_PROJECT en .env)")

        persona_id = self._persona_cluster(record, req)
        session = self._session(record, req, persona_id)
        if persona_id is not None:
            system, tool_names = persona_system(record, persona_id), PERSONA_TOOLS
        else:
            system, tool_names = analyst_system(record), list(TOOL_SPECS)
        tools = [TOOL_SPECS[name] for name in tool_names]

        checkpoint = len(session.messages)
        session.messages.append(Message(role="user", text=self._user_text(record, req)))
        traces: list[ToolCallTrace] = []
        attachments = []
        answer = None
        try:
            for _ in range(self.settings.max_agent_steps):
                turn = self.llm.chat(session.messages, system, tools)
                session.messages.append(Message(role="model", text=turn.text, tool_calls=turn.tool_calls, raw=turn.raw))
                if not turn.tool_calls:
                    answer = turn.text or ""
                    break
                results = []
                for call in turn.tool_calls:
                    if call.name in tool_names:
                        outcome = execute_tool(call.name, call.args, record, self.store)
                    else:
                        message = f"Herramienta no disponible en este modo: {call.name}"
                        outcome = ToolOutcome(response={"error": message}, error=message)
                    traces.append(ToolCallTrace(name=call.name, args=call.args, result_preview=outcome.preview, error=outcome.error))
                    if outcome.attachment:
                        attachments.append(outcome.attachment)
                    results.append(ToolResult(name=call.name, response=outcome.response, id=call.id))
                session.messages.append(Message(role="tool", tool_results=results))
        except Exception:
            # Deja el historial como estaba para que la sesión siga siendo usable.
            del session.messages[checkpoint:]
            raise

        if answer is None:
            answer = OUT_OF_STEPS
            session.messages.append(Message(role="model", text=answer))
        return ChatResponse(
            session_id=session.session_id,
            answer=answer,
            tool_calls=traces,
            attachments=attachments,
            simulated=persona_id is not None,
        )

    @staticmethod
    def _persona_cluster(record: ClusteringRecord, req: ChatRequest) -> int | None:
        if req.mode != "persona":
            return None
        cluster_id = req.persona_cluster_id
        if cluster_id is None and len(req.cluster_ids) == 1:
            cluster_id = req.cluster_ids[0]
        if cluster_id is None or record.result.cluster(cluster_id) is None:
            raise ValueError("El modo persona requiere un persona_cluster_id válido")
        return cluster_id

    def _session(self, record: ClusteringRecord, req: ChatRequest, persona_id: int | None) -> ChatSession:
        existing = self.store.get_session(req.session_id) if req.session_id else None
        if (
            existing
            and existing.clustering_id == record.result.clustering_id
            and existing.mode == req.mode
            and existing.persona_cluster_id == persona_id
        ):
            return existing
        session = ChatSession(
            session_id=new_id("ses"),
            clustering_id=record.result.clustering_id,
            mode=req.mode,
            persona_cluster_id=persona_id,
        )
        self.store.add_session(session)
        return session

    @staticmethod
    def _user_text(record: ClusteringRecord, req: ChatRequest) -> str:
        if not req.cluster_ids or req.mode == "persona":
            return req.message
        selected = []
        for cluster_id in req.cluster_ids:
            c = record.result.cluster(cluster_id)
            if c:
                selected.append(f"{cluster_id} ({c.label.name})")
        if not selected:
            return req.message
        return f"[Contexto: el usuario tiene seleccionados los clusters {', '.join(selected)}]\n{req.message}"
