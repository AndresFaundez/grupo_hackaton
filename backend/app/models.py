"""Contratos compartidos entre módulos y con la API.

Los modelos con sufijo `LLM` son los que se piden a Gemini como salida estructurada:
se mantienen simples (sin dicts libres) para que el schema sea compatible.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

SemanticType = Literal["id", "datetime", "monetary", "numeric", "categorical", "text", "pii", "ignore"]
DataShape = Literal["transactional", "customer"]


# --- Ingesta y schema ---------------------------------------------------------


class ColumnProfile(BaseModel):
    name: str
    dtype: str
    n_null: int
    n_unique: int
    examples: list[str] = Field(description="Hasta 3 valores de ejemplo; enmascarados si la columna parece PII")
    pii_suspect: bool = False
    stats: dict[str, float | str] | None = None


class ColumnSpec(BaseModel):
    name: str
    semantic_type: SemanticType
    use_as_feature: bool = False
    description: str | None = None


class SchemaMappingLLM(BaseModel):
    data_shape: DataShape = Field(
        description="transactional: una fila por compra (el cliente se repite). customer: una fila por cliente."
    )
    customer_id: str = Field(description="Columna que identifica al cliente")
    date: str | None = Field(None, description="Columna de fecha de la compra (transaccional)")
    amount: str | None = Field(None, description="Columna con el monto total de la línea o compra")
    quantity: str | None = Field(None, description="Columna de cantidad, si no hay monto total")
    unit_price: str | None = Field(None, description="Columna de precio unitario, si no hay monto total")
    invoice_id: str | None = Field(None, description="Columna que identifica la compra/boleta/factura")
    category: str | None = Field(None, description="Columna de categoría de producto")
    pii_columns: list[str] = Field(default_factory=list, description="Columnas con datos personales")
    columns: list[ColumnSpec] = Field(default_factory=list)


class SchemaMapping(SchemaMappingLLM):
    source: Literal["llm", "heuristic", "user"] = "heuristic"


class DatasetInfo(BaseModel):
    dataset_id: str
    filename: str
    n_rows: int
    columns: list[ColumnProfile]
    proposed_schema: SchemaMapping
    confirmed_schema: SchemaMapping | None = None
    preview: list[dict[str, Any]] = Field(default_factory=list)

    @property
    def schema_in_use(self) -> SchemaMapping:
        return self.confirmed_schema or self.proposed_schema


# --- Clustering ---------------------------------------------------------------


class FeatureStat(BaseModel):
    feature: str
    mean: float
    median: float
    global_mean: float
    z: float = Field(description="Desviación de la media del cluster vs. la global, en desviaciones estándar")


class ClusterProfile(BaseModel):
    cluster_id: int
    size: int
    share: float
    revenue_share: float | None = None
    features: list[FeatureStat]
    top_traits: list[str]
    categorical: dict[str, dict[str, float]] = Field(
        default_factory=dict, description="columna -> valor -> proporción dentro del cluster"
    )


class Condition(BaseModel):
    feature: str
    op: Literal["<=", ">"]
    threshold: float


class ClusterRule(BaseModel):
    text: str
    conditions: list[Condition]
    precision: float = Field(description="Fracción de clientes que cumplen la regla y pertenecen al cluster")
    coverage: float = Field(description="Fracción del cluster que cumple la regla")
    support: int


class ClusterLabel(BaseModel):
    cluster_id: int
    name: str = Field(description="Nombre corto y memorable del segmento, en español")
    description: str = Field(description="1-2 frases explicando qué caracteriza al segmento")
    persona: str = Field(description="Descripción de un cliente típico del segmento, en tercera persona")
    key_traits: list[str] = Field(description="3-5 rasgos distintivos con cifras")
    value_level: Literal["alto", "medio", "bajo"]
    suggested_questions: list[str] = Field(description="3 preguntas que un analista de negocio haría sobre este segmento")


class ClusterLabelsLLM(BaseModel):
    clusters: list[ClusterLabel]


class ClusterSummary(BaseModel):
    profile: ClusterProfile
    rules: list[ClusterRule]
    label: ClusterLabel


class Point2D(BaseModel):
    customer_ref: int
    x: float
    y: float
    cluster_id: int


class ClusteringRequest(BaseModel):
    k: int | None = Field(None, ge=2, le=12, description="Número de clusters; si falta se elige por silhouette")
    features: list[str] | None = Field(None, description="Subconjunto de features a usar; por defecto todas")


class ClusteringResult(BaseModel):
    clustering_id: str
    dataset_id: str
    data_shape: DataShape
    n_customers: int
    k: int
    silhouette: float
    k_scores: dict[int, float]
    features: list[str]
    feature_descriptions: dict[str, str]
    rules_fidelity: float
    labels_source: Literal["llm", "fallback"]
    clusters: list[ClusterSummary]
    embedding: list[Point2D]

    def cluster(self, cluster_id: int) -> ClusterSummary | None:
        return next((c for c in self.clusters if c.profile.cluster_id == cluster_id), None)


# --- Chat ---------------------------------------------------------------------


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    cluster_ids: list[int] = Field(default_factory=list, description="Clusters que el usuario tiene seleccionados")
    mode: Literal["analyst", "persona"] = "analyst"
    persona_cluster_id: int | None = None


class ToolCallTrace(BaseModel):
    name: str
    args: dict[str, Any]
    result_preview: Any = None
    error: str | None = None


class Attachment(BaseModel):
    type: Literal["table", "customer_list"]
    title: str | None = None
    columns: list[str] | None = None
    rows: list[list[Any]] | None = None
    handle: str | None = None
    count: int | None = None


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)
    simulated: bool = False
