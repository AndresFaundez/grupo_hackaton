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


# Plantillas para cuando no hay LLM: dos versiones por objetivo para poder "generar otra versión".
# {producto} es lo que más compra el segmento.
TEMPLATES = {
    "recompra": [
        ("¡Hola [Nombre]! Ya es momento de reponer {producto}. Vuelve esta semana y llévate 10% de descuento.",
         "Tu próxima compra tiene premio"),
        ("[Nombre], tu {producto} favorito te espera. Compra antes del domingo y el envío va por nuestra cuenta.",
         "Envío gratis en tu próxima compra"),
    ],
    "fidelizar": [
        ("[Nombre], gracias por ser de nuestros mejores clientes. Tienes acceso anticipado a las novedades de {producto}.",
         "Acceso anticipado solo para ti"),
        ("[Nombre], por tu preferencia te regalamos un beneficio exclusivo en tu próxima compra de {producto}.",
         "Un regalo por ser cliente preferente"),
    ],
    "reactivar": [
        ("¡Te extrañamos, [Nombre]! Vuelve con 15% de descuento en {producto}, válido por 7 días.",
         "Te extrañamos: 15% para tu regreso"),
        ("[Nombre], hace tiempo que no te vemos. Tenemos novedades en {producto} y un descuento esperándote.",
         "Hay novedades que te van a gustar"),
    ],
    "ticket": [
        ("[Nombre], combina {producto} con algo nuevo y obtén envío gratis en compras sobre {monto}.",
         "Envío gratis sobre {monto}"),
        ("[Nombre], descubre la versión premium de {producto}. Esta semana con 10% en tu segundo producto.",
         "Sube de nivel tu próxima compra"),
    ],
}
SMS_MAX = 160


def template_campaign(summary: ClusterSummary, req: CampaignDraftRequest) -> CampaignDraft:
    """Borrador sin LLM: plantilla según objetivo y canal con datos del segmento."""
    p = summary.profile
    producto = p.top_products[0].name.lower() if p.top_products else "nuestros productos"
    ticket = p.metrics.avg_ticket
    monto = f"${round(ticket * 1.3, -3):,.0f}".replace(",", ".") if ticket else "un monto mínimo"

    variants = TEMPLATES[req.objective]
    message, subject = variants[0]
    if req.previous_message and req.previous_message.startswith(message.split("{")[0][:20]):
        message, subject = variants[1]
    message = message.format(producto=producto, monto=monto)
    subject = subject.format(monto=monto)

    if req.channel == "whatsapp":
        message += " 🛍️"
    elif req.channel == "email":
        message += "\n\nTe esperamos en la tienda o en nuestro sitio.\nUn saludo,\nEl equipo"
    elif len(message) > SMS_MAX:
        message = message[: SMS_MAX - 1].rstrip() + "…"

    rationale = (
        f"Plantilla automática para {OBJECTIVES[req.objective].split(':')[0]}: "
        f"el segmento compra sobre todo {producto}."
    )
    if req.instructions:
        rationale += " Para aplicar indicaciones personalizadas hace falta activar la IA."
    return CampaignDraft(
        subject=subject if req.channel == "email" else None,
        message=message,
        rationale=rationale,
        cluster_id=p.cluster_id,
        objective=req.objective,
        channel=req.channel,
        audience_size=p.size,
    )


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
