"""Nombres, personas y preguntas sugeridas por cluster, generados por el LLM.

Una sola llamada con todos los clusters, para que los nombres se diferencien entre sí.
El LLM solo ve agregados.
"""

from __future__ import annotations

import json
import logging

from app.agent.llm import LLM, LLMError
from app.models import ClusterLabel, ClusterLabelsLLM, ClusterProfile, ClusterRule

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """Eres un estratega de marketing y analista de clientes. Recibes los segmentos obtenidos \
por clustering de la base de clientes de una empresa, con estadísticas agregadas y reglas que los delimitan.

Para cada cluster genera:
- name: nombre corto (2-4 palabras), memorable y orientado a negocio, distinto de los demás. Ej: "VIP en riesgo", "Cazadores de ofertas".
- description: 1-2 frases sobre qué lo caracteriza.
- persona: cómo es un cliente típico, en tercera persona, 2 frases.
- key_traits: 3-5 rasgos con cifras tomadas de los datos.
- value_level: alto, medio o bajo según su aporte de ingresos y potencial.
- suggested_questions: 3 preguntas concretas que un analista le haría a este segmento.

Usa solo las cifras entregadas; no inventes datos. z indica cuántas desviaciones estándar se aleja \
la media del cluster del promedio general. Responde en español."""


def label_clusters(
    profiles: list[ClusterProfile],
    rules: dict[int, list[ClusterRule]],
    descriptions: dict[str, str],
    llm: LLM | None,
) -> tuple[list[ClusterLabel], str]:
    """Devuelve (etiquetas, origen) donde origen es "llm" o "fallback"."""
    fallback = [fallback_label(p) for p in profiles]
    if llm is None:
        return fallback, "fallback"

    payload = {
        "features": descriptions,
        "clusters": [
            {
                "cluster_id": p.cluster_id,
                "clientes": p.size,
                "porcentaje_clientes": p.share,
                "porcentaje_ingresos": p.revenue_share,
                "features": [
                    {"feature": s.feature, "media": s.mean, "mediana": s.median, "media_global": s.global_mean, "z": s.z}
                    for s in sorted(p.features, key=lambda s: abs(s.z), reverse=True)[:8]
                ],
                "categorias": p.categorical,
                "reglas": [r.text for r in rules.get(p.cluster_id, [])[:2]],
            }
            for p in profiles
        ],
    }
    prompt = f"Segmentos:\n```json\n{json.dumps(payload, ensure_ascii=False)}\n```"
    try:
        result = llm.generate_json(prompt, ClusterLabelsLLM, system=SYSTEM_PROMPT)
    except LLMError:
        log.warning("Etiquetado con LLM falló; uso fallback", exc_info=True)
        return fallback, "fallback"

    by_id = {label.cluster_id: label for label in result.clusters}
    labels = [by_id.get(p.cluster_id, fb) for p, fb in zip(profiles, fallback)]
    if len({label.name for label in labels}) < len(labels):
        log.warning("El LLM repitió nombres de cluster; uso fallback")
        return fallback, "fallback"
    return labels, "llm"


def fallback_label(profile: ClusterProfile) -> ClusterLabel:
    if profile.revenue_share is not None:
        ratio = profile.revenue_share / max(profile.share, 1e-9)
        value = "alto" if ratio >= 1.5 else "bajo" if ratio <= 0.6 else "medio"
    else:
        value = "medio"
    traits = profile.top_traits or ["sin rasgos marcados respecto al promedio"]
    return ClusterLabel(
        cluster_id=profile.cluster_id,
        name=f"Cluster {profile.cluster_id + 1}",
        description=f"{profile.size} clientes ({profile.share:.0%}). " + "; ".join(traits[:2]),
        persona="",
        key_traits=traits,
        value_level=value,
        suggested_questions=[
            "¿Qué caracteriza a este cluster?",
            "¿En qué se diferencia del resto?",
            "¿Qué campaña le harías a este segmento?",
        ],
    )
