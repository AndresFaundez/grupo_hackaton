"""Registro en memoria de datasets, clusterings, resultados y sesiones de chat.

Para la hackatón no hay base de datos: todo vive en memoria y se escribe una copia
en `workspace/` para depurar. Reiniciar el servidor borra el estado.
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd

from app.models import ClusteringResult, DatasetInfo

if TYPE_CHECKING:
    from app.agent.llm import Message
    from app.agent.sandbox import Sandbox
    from app.core.rules import RuleSet

log = logging.getLogger(__name__)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


# Tope de objetos en memoria: al pasarlo se descartan los más antiguos, para que el
# servidor no crezca sin límite si queda corriendo y se suben muchos archivos.
MAX_DATASETS = 20
MAX_CLUSTERINGS = 30
MAX_RESULTS = 200
MAX_SESSIONS = 200


def _evict(items: dict, limit: int) -> None:
    while len(items) > limit:
        items.pop(next(iter(items)))


@dataclass
class DatasetRecord:
    info: DatasetInfo
    df: pd.DataFrame


@dataclass
class ClusteringRecord:
    result: ClusteringResult
    # Una fila por cliente, indexada por customer_ref: customer_id original, features en
    # unidades originales, atributos descriptivos y cluster_id.
    customers: pd.DataFrame
    # Columnas PII por customer_ref. Nunca se pasan al LLM; solo van a la UI.
    pii: pd.DataFrame
    rule_set: RuleSet
    sandbox: Sandbox


@dataclass
class ChatSession:
    session_id: str
    clustering_id: str
    mode: str
    persona_cluster_id: int | None
    messages: list[Message] = field(default_factory=list)


class Store:
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.datasets: dict[str, DatasetRecord] = {}
        self.clusterings: dict[str, ClusteringRecord] = {}
        self.results: dict[str, pd.DataFrame] = {}
        self.sessions: dict[str, ChatSession] = {}
        self._lock = threading.Lock()

    # --- datasets ---

    def add_dataset(self, record: DatasetRecord) -> None:
        with self._lock:
            self.datasets[record.info.dataset_id] = record
            _evict(self.datasets, MAX_DATASETS)
        self._persist_dataset(record)

    def get_dataset(self, dataset_id: str) -> DatasetRecord | None:
        return self.datasets.get(dataset_id)

    def save_dataset_info(self, record: DatasetRecord) -> None:
        self._write_json(self._dir(record.info.dataset_id) / "dataset.json", record.info.model_dump(mode="json"))

    # --- clusterings ---

    def add_clustering(self, record: ClusteringRecord) -> None:
        with self._lock:
            self.clusterings[record.result.clustering_id] = record
            _evict(self.clusterings, MAX_CLUSTERINGS)
        self.save_clustering(record)

    def save_clustering(self, record: ClusteringRecord) -> None:
        folder = self._dir(record.result.dataset_id) / record.result.clustering_id
        self._write_json(folder / "result.json", record.result.model_dump(mode="json"))

    def get_clustering(self, clustering_id: str) -> ClusteringRecord | None:
        return self.clusterings.get(clustering_id)

    # --- listas de clientes (se entregan a la UI, no al LLM) ---

    def add_result(self, df: pd.DataFrame) -> str:
        handle = new_id("res")
        with self._lock:
            self.results[handle] = df
            _evict(self.results, MAX_RESULTS)
        return handle

    def get_result(self, handle: str) -> pd.DataFrame | None:
        return self.results.get(handle)

    # --- sesiones de chat ---

    def get_session(self, session_id: str) -> ChatSession | None:
        return self.sessions.get(session_id)

    def add_session(self, session: ChatSession) -> None:
        with self._lock:
            self.sessions[session.session_id] = session
            _evict(self.sessions, MAX_SESSIONS)

    # --- persistencia best-effort ---

    def _dir(self, dataset_id: str) -> Path:
        return self.workspace_dir / dataset_id

    def _persist_dataset(self, record: DatasetRecord) -> None:
        folder = self._dir(record.info.dataset_id)
        try:
            folder.mkdir(parents=True, exist_ok=True)
            record.df.to_parquet(folder / "raw.parquet", index=False)
        except Exception:
            log.warning("No se pudo guardar raw.parquet de %s", record.info.dataset_id, exc_info=True)
        self.save_dataset_info(record)

    @staticmethod
    def _write_json(path: Path, payload: Any) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            # utf-8 explícito: en Windows el default (cp1252) falla con emojis y otros caracteres.
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        except Exception:
            log.warning("No se pudo escribir %s", path, exc_info=True)
