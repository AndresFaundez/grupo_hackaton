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


class ClusterMetrics(BaseModel):
    """Métricas de negocio listas para mostrar (None si los datos no permiten calcularlas)."""

    avg_spend: float | None = Field(None, description="Gasto total promedio por cliente en el periodo")
    avg_ticket: float | None = Field(None, description="Gasto promedio por compra")
    purchases_per_year: float | None = Field(None, description="Compras promedio por cliente al año")
    days_since_last_purchase: float | None = Field(None, description="Días promedio desde la última compra")
    revenue: float | None = Field(None, description="Ventas totales del cluster")


class ProductShare(BaseModel):
    name: str
    share: float = Field(description="Fracción del gasto del cluster en esta categoría")


class ClusterProfile(BaseModel):
    cluster_id: int
    size: int
    share: float
    revenue_share: float | None = None
    metrics: ClusterMetrics = Field(default_factory=ClusterMetrics)
    top_products: list[ProductShare] = Field(default_factory=list)
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


Objective = Literal["recompra", "fidelizar", "reactivar", "ticket"]
Channel = Literal["email", "whatsapp", "sms"]


class ClusterLabel(BaseModel):
    cluster_id: int
    name: str = Field(description="Nombre corto y memorable del segmento, en español")
    description: str = Field(description="1-2 frases explicando qué caracteriza al segmento")
    persona: str = Field(description="Descripción de un cliente típico del segmento, en tercera persona")
    tags: list[str] = Field(description="3 etiquetas cortas de 1-3 palabras, ej: Frecuencia alta, Ticket medio")
    key_traits: list[str] = Field(description="3-5 rasgos distintivos con cifras")
    value_level: Literal["alto", "medio", "bajo"]
    suggested_objective: Objective = Field(
        description="Objetivo de marketing más indicado: recompra, fidelizar, reactivar o ticket (aumentar ticket)"
    )
    strategies: list[str] = Field(description="3 estrategias de marketing concretas para este segmento")
    suggested_questions: list[str] = Field(description="3 preguntas que un analista de negocio haría sobre este segmento")


class ClusterLabelsLLM(BaseModel):
    clusters: list[ClusterLabel]


class RepresentativeCustomer(BaseModel):
    """Cliente más cercano al centro del cluster. Contiene PII: es solo para la UI, nunca para el LLM."""

    customer_ref: int
    customer_id: str
    name: str | None = None
    features: dict[str, float | str]


class ClusterSummary(BaseModel):
    profile: ClusterProfile
    rules: list[ClusterRule]
    label: ClusterLabel
    representative: RepresentativeCustomer | None = None


class Point2D(BaseModel):
    customer_ref: int
    x: float
    y: float
    cluster_id: int


class ScatterData(BaseModel):
    x_label: str
    y_label: str
    points: list[Point2D]


class ClusteringRequest(BaseModel):
    k: int | None = Field(None, ge=2, le=12, description="Número de clusters; si falta se elige por silhouette")
    features: list[str] | None = Field(None, description="Subconjunto de features a usar; por defecto todas")


class ClusteringResult(BaseModel):
    clustering_id: str
    dataset_id: str
    filename: str
    data_shape: DataShape
    n_customers: int
    total_revenue: float | None = None
    k: int
    silhouette: float
    k_scores: dict[int, float]
    features: list[str]
    feature_descriptions: dict[str, str]
    rules_fidelity: float
    labels_source: Literal["llm", "fallback"]
    clusters: list[ClusterSummary]
    scatter: ScatterData

    def cluster(self, cluster_id: int) -> ClusterSummary | None:
        return next((c for c in self.clusters if c.profile.cluster_id == cluster_id), None)


class ClusterRename(BaseModel):
    name: str = Field(min_length=1, max_length=60)


# --- Campañas -----------------------------------------------------------------


class CampaignDraftRequest(BaseModel):
    objective: Objective
    channel: Channel
    instructions: str | None = Field(None, description="Indicaciones libres del usuario para ajustar el mensaje")
    previous_message: str | None = Field(None, description="Borrador anterior, para generar una versión distinta")


class CampaignDraftLLM(BaseModel):
    subject: str | None = Field(None, description="Asunto, solo para email")
    message: str = Field(description="Mensaje listo para enviar; usa [Nombre] donde va el nombre del cliente")
    rationale: str = Field(description="1-2 frases: por qué este mensaje funciona para el segmento, con datos")


class CampaignDraft(CampaignDraftLLM):
    cluster_id: int
    objective: Objective
    channel: Channel
    audience_size: int


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
