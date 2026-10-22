"""Borradores de mensajes de campaña por segmento, generados por el LLM con datos agregados."""

from __future__ import annotations

import json

from app.agent.llm import LLM
from app.models import CampaignDraft, CampaignDraftLLM, CampaignDraftRequest, ClusterSummary

OBJECTIVES = {
    "recompra": "impulsar la recompra: que vuelvan a comprar pronto",
    "fidelizar": "fidelizar: premiar y retener",
    "reactivar": "reactivar: recuperar clientes inactivos",
    "ticket": "aumentar el ticket: venta cruzada o productos premium",
}
CHANNEL_RULES = {
    "email": "Email: incluye subject (máx. 60 caracteres) y un cuerpo de máximo 90 palabras.",
    "whatsapp": "WhatsApp: tono cercano, máximo 300 caracteres, 1-2 emojis como máximo. subject = null.",
    "sms": "SMS: máximo 160 caracteres, sin emojis, con una llamada a la acción clara. subject = null.",
}

SYSTEM_PROMPT = """Eres un copywriter de marketing experto en campañas segmentadas. Escribes en español \
neutro, claro y persuasivo, sin exagerar. Usa [Nombre] donde va el nombre del cliente. Si propones un \
descuento o código, que sea razonable para el ticket del segmento. Basa el mensaje y la justificación \
en los datos del segmento."""


def draft_campaign(summary: ClusterSummary, req: CampaignDraftRequest, llm: LLM) -> CampaignDraft:
    p, label = summary.profile, summary.label
    segment = {
        "nombre": label.name,
        "descripcion": label.description,
        "persona": label.persona,
        "rasgos": label.key_traits,
        "clientes": p.size,
        "porcentaje_ingresos": p.revenue_share,
        "metricas": p.metrics.model_dump(exclude_none=True),
        "que_compran": [f"{x.name} ({x.share:.0%})" for x in p.top_products],
        "estrategias_sugeridas": label.strategies,
    }
    parts = [
        f"Segmento:\n```json\n{json.dumps(segment, ensure_ascii=False)}\n```",
        f"Objetivo de la campaña: {OBJECTIVES[req.objective]}.",
        f"Canal: {CHANNEL_RULES[req.channel]}",
    ]
    if req.instructions:
        parts.append(f"Indicaciones del usuario (aplícalas): {req.instructions}")
    if req.previous_message:
        parts.append(f"Borrador anterior (escribe una versión claramente distinta):\n{req.previous_message}")

    draft = llm.generate_json("\n\n".join(parts), CampaignDraftLLM, system=SYSTEM_PROMPT)
    if req.channel != "email":
        draft.subject = None
    return CampaignDraft(
        **draft.model_dump(),
        cluster_id=p.cluster_id,
        objective=req.objective,
        channel=req.channel,
        audience_size=p.size,
    )
