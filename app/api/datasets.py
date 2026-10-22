from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.core.pipeline import ingest_dataset, run_clustering
from app.core.schema import validate_schema
from app.models import ClusteringRequest, ClusteringResult, DatasetInfo, SchemaMapping
from app.services import Services, get_services

router = APIRouter(prefix="/datasets", tags=["datasets"])

MAX_UPLOAD_BYTES = 200 * 1024 * 1024


@router.post("", response_model=DatasetInfo)
def upload_dataset(file: UploadFile, services: Services = Depends(get_services)) -> DatasetInfo:
    content = file.file.read(MAX_UPLOAD_BYTES + 1)
    if not content:
        raise HTTPException(400, "Archivo vacío")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Archivo demasiado grande (máx. 200 MB)")
    try:
        record = ingest_dataset(content, file.filename or "upload.csv", services.llm, services.store)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    return record.info


@router.get("/{dataset_id}", response_model=DatasetInfo)
def get_dataset(dataset_id: str, services: Services = Depends(get_services)) -> DatasetInfo:
    return services.dataset(dataset_id).info


@router.put("/{dataset_id}/schema", response_model=DatasetInfo)
def confirm_schema(dataset_id: str, schema: SchemaMapping, services: Services = Depends(get_services)) -> DatasetInfo:
    record = services.dataset(dataset_id)
    problems = validate_schema(schema, list(record.df.columns))
    if problems:
        raise HTTPException(422, {"problems": problems})
    record.info.confirmed_schema = schema.model_copy(update={"source": "user"})
    services.store.save_dataset_info(record)
    return record.info


@router.post("/{dataset_id}/clusterings", response_model=ClusteringResult)
def create_clustering(
    dataset_id: str, req: ClusteringRequest | None = None, services: Services = Depends(get_services)
) -> ClusteringResult:
    record = services.dataset(dataset_id)
    try:
        clustering = run_clustering(record, req or ClusteringRequest(), services.llm, services.settings, services.store)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    return clustering.result
