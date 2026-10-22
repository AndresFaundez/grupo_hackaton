from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import HTTPException, Request

from app.agent.chat import ChatService
from app.agent.llm import LLM
from app.config import Settings
from app.store import ClusteringRecord, DatasetRecord, Store


@dataclass
class Services:
    settings: Settings
    store: Store
    llm: LLM | None
    chat: ChatService = field(init=False)

    def __post_init__(self) -> None:
        self.chat = ChatService(self.llm, self.store, self.settings)

    def dataset(self, dataset_id: str) -> DatasetRecord:
        record = self.store.get_dataset(dataset_id)
        if record is None:
            raise HTTPException(404, f"Dataset {dataset_id} no existe")
        return record

    def clustering(self, clustering_id: str) -> ClusteringRecord:
        record = self.store.get_clustering(clustering_id)
        if record is None:
            raise HTTPException(404, f"Clustering {clustering_id} no existe")
        return record


def get_services(request: Request) -> Services:
    return request.app.state.services
