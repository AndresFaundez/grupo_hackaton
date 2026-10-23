import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response

from app.agent.llm import LLMError
from app.agent.tools import dataframe_payload
from app.core.campaign import draft_campaign, template_campaign
from app.models import CampaignDraft, CampaignDraftRequest, ClusteringResult, ClusterRename, ClusterSummary
from app.services import Services, get_services

router = APIRouter(tags=["clusterings"])
log = logging.getLogger(__name__)


def _table_response(df, name: str, format: str):
    if format == "csv":
        return Response(
            df.to_csv(index=False),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{name}.csv"'},
        )
    return dataframe_payload(df)


@router.get("/clusterings/{clustering_id}", response_model=ClusteringResult)
def get_clustering(clustering_id: str, services: Services = Depends(get_services)) -> ClusteringResult:
    return services.clustering(clustering_id).result


@router.get("/clusterings/{clustering_id}/clusters/{cluster_id}", response_model=ClusterSummary)
def get_cluster(clustering_id: str, cluster_id: int, services: Services = Depends(get_services)) -> ClusterSummary:
    return services.cluster(clustering_id, cluster_id)


@router.patch("/clusterings/{clustering_id}/clusters/{cluster_id}", response_model=ClusterSummary)
def rename_cluster(
    clustering_id: str, cluster_id: int, body: ClusterRename, services: Services = Depends(get_services)
) -> ClusterSummary:
    """Renombra el cluster en el resultado y en el sandbox, para que el chat use el nombre nuevo."""
    record = services.clustering(clustering_id)
    summary = services.cluster(clustering_id, cluster_id)
    name = body.name.strip()
    summary.label.name = name
    record.sandbox.rename_cluster(cluster_id, name)
    services.store.save_clustering(record)
    return summary


@router.get("/clusterings/{clustering_id}/clusters/{cluster_id}/customers")
def get_cluster_customers(
    clustering_id: str, cluster_id: int, format: Literal["json", "csv"] = "json", services: Services = Depends(get_services)
):
    """Audiencia completa del cluster, con datos de contacto (solo para la UI)."""
    record = services.clustering(clustering_id)
    services.cluster(clustering_id, cluster_id)
    members = record.customers[record.customers["cluster_id"] == cluster_id].join(record.pii, how="left")
    members.insert(0, "customer_ref", members.index)
    return _table_response(members.reset_index(drop=True), f"cluster_{cluster_id}", format)


@router.post("/clusterings/{clustering_id}/clusters/{cluster_id}/campaign-draft", response_model=CampaignDraft)
def campaign_draft(
    clustering_id: str, cluster_id: int, req: CampaignDraftRequest, services: Services = Depends(get_services)
) -> CampaignDraft:
    summary = services.cluster(clustering_id, cluster_id)
    if services.llm is None:
        return template_campaign(summary, req)
    try:
        return draft_campaign(summary, req, services.llm)
    except LLMError:
        log.warning("Borrador con LLM falló; uso plantilla", exc_info=True)
        return template_campaign(summary, req)


@router.get("/results/{handle}")
def get_result(handle: str, format: Literal["json", "csv"] = "json", services: Services = Depends(get_services)):
    df = services.store.get_result(handle)
    if df is None:
        raise HTTPException(404, f"Resultado {handle} no existe")
    return _table_response(df, handle, format)
