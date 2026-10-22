"""Dataset transaccional sintético con segmentos plantados (verdad conocida).

Sirve para la demo y para testear que el pipeline recupera los segmentos.
Todos los datos personales son inventados.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

START = pd.Timestamp("2025-01-01")
END = pd.Timestamp("2025-12-31")

CATEGORIES = ["Abarrotes", "Bebidas", "Lácteos", "Limpieza", "Electro", "Vestuario"]
OFFERS = "Ofertas"
COMUNAS = ["Santiago", "Providencia", "Ñuñoa", "Las Condes", "Maipú", "La Florida", "Puente Alto", "Valparaíso", "Concepción"]
FIRST_NAMES = ["Camila", "Matías", "Valentina", "Benjamín", "Sofía", "Vicente", "Isidora", "Martín", "Florencia", "Tomás",
               "Javiera", "Joaquín", "Antonia", "Agustín", "Catalina", "Diego", "Fernanda", "Felipe", "Constanza", "Ignacio"]
LAST_NAMES = ["González", "Muñoz", "Rojas", "Díaz", "Pérez", "Soto", "Contreras", "Silva", "Martínez", "Sepúlveda",
              "Morales", "Rodríguez", "López", "Fuentes", "Hernández", "Torres", "Araya", "Flores", "Espinoza", "Valenzuela"]

# share: fracción de clientes; freq: compras en el año; ticket: CLP por compra; recency: días desde la última compra.
SEGMENTS = {
    "vip": {"share": 0.10, "freq": (20, 40), "ticket": (80_000, 150_000), "recency": (1, 20), "offers": 0.05},
    "en_riesgo": {"share": 0.20, "freq": (8, 15), "ticket": (50_000, 90_000), "recency": (120, 300), "offers": 0.10},
    "ocasionales": {"share": 0.45, "freq": (1, 3), "ticket": (10_000, 25_000), "recency": (30, 250), "offers": 0.15},
    "cazadores": {"share": 0.25, "freq": (10, 20), "ticket": (5_000, 12_000), "recency": (1, 30), "offers": 0.85},
}


def rut(number: int) -> str:
    digits, factor, total = str(number), 2, 0
    for d in reversed(digits):
        total += int(d) * factor
        factor = 2 if factor == 7 else factor + 1
    check = 11 - total % 11
    dv = {11: "0", 10: "K"}.get(check, str(check))
    return f"{number:,}".replace(",", ".") + f"-{dv}"


def generate(n_customers: int = 2000, seed: int = 7) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (transacciones, verdad) donde verdad mapea rut_cliente -> segmento plantado."""
    rng = np.random.default_rng(seed)
    segment_names = list(SEGMENTS)
    counts = np.round([SEGMENTS[s]["share"] * n_customers for s in segment_names]).astype(int)

    rows, truth = [], []
    numbers = rng.choice(np.arange(8_000_000, 25_000_000), size=int(counts.sum()), replace=False)
    order_id, customer_idx = 100_000, 0
    for segment, count in zip(segment_names, counts):
        cfg = SEGMENTS[segment]
        for _ in range(count):
            customer_rut = rut(int(numbers[customer_idx]))
            customer_idx += 1
            first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
            name = f"{first} {last}"
            email = f"{first.lower()}.{last.lower()}{rng.integers(1, 999)}@example.com"
            comuna = rng.choice(COMUNAS)
            truth.append({"rut_cliente": customer_rut, "segmento": segment})

            n_orders = int(rng.integers(cfg["freq"][0], cfg["freq"][1] + 1))
            last_date = END - pd.Timedelta(days=int(rng.integers(cfg["recency"][0], cfg["recency"][1] + 1)))
            span = max((last_date - START).days, 1)
            offsets = np.sort(rng.integers(0, span, size=n_orders - 1)) if n_orders > 1 else np.array([], dtype=int)
            dates = [START + pd.Timedelta(days=int(o)) for o in offsets] + [last_date]
            favorite = rng.choice(CATEGORIES)

            for date in dates:
                order_id += 1
                ticket = rng.uniform(*cfg["ticket"]) * rng.lognormal(0, 0.15)
                n_lines = int(rng.integers(1, 5))
                weights = rng.dirichlet(np.ones(n_lines))
                when = date + pd.Timedelta(minutes=int(rng.integers(9 * 60, 21 * 60)))
                for w in weights:
                    if rng.random() < cfg["offers"]:
                        category = OFFERS
                    elif rng.random() < 0.5:
                        category = favorite
                    else:
                        category = rng.choice(CATEGORIES)
                    rows.append({
                        "boleta": order_id,
                        "fecha": when.strftime("%Y-%m-%d %H:%M"),
                        "rut_cliente": customer_rut,
                        "nombre_cliente": name,
                        "email": email,
                        "comuna": comuna,
                        "categoria": category,
                        "monto": int(round(ticket * w)),
                    })

    tx = pd.DataFrame(rows).sample(frac=1, random_state=seed).reset_index(drop=True)
    return tx, pd.DataFrame(truth)
