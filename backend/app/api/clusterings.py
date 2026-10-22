from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response

from app.agent.tools import dataframe_payload
from app.models import ClusteringResult, ClusterSummary
from app.services import Services, get_services

router = APIRouter(tags=["clusterings"])


@router.get("/clusterings/{clustering_id}", response_model=ClusteringResult)
def get_clustering(clustering_id: str, services: Services = Depends(get_services)) -> ClusteringResult:
    return services.clustering(clustering_id).result


@router.get("/clusterings/{clustering_id}/clusters/{cluster_id}", response_model=ClusterSummary)
def get_cluster(clustering_id: str, cluster_id: int, services: Services = Depends(get_services)) -> ClusterSummary:
    summary = services.clustering(clustering_id).result.cluster(cluster_id)
    if summary is None:
        raise HTTPException(404, f"Cluster {cluster_id} no existe")
    return summary


@router.get("/results/{handle}")
def get_result(handle: str, format: Literal["json", "csv"] = "json", services: Services = Depends(get_services)):
    df = services.store.get_result(handle)
    if df is None:
        raise HTTPException(404, f"Resultado {handle} no existe")
    if format == "csv":
        return Response(
            df.to_csv(index=False),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{handle}.csv"'},
        )
    return dataframe_payload(df)
