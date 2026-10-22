"""Reglas legibles que delimitan cada cluster.

Un árbol de decisión chico aprende a predecir el cluster a partir de las features en
unidades originales; cada hoja es una regla del tipo "monetary > 120.000 Y recency_days ≤ 30".
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

from app.models import ClusterRule, Condition

MAX_RULES_PER_CLUSTER = 3
MIN_PRECISION = 0.5


@dataclass
class RuleSet:
    tree: DecisionTreeClassifier
    feature_names: list[str]
    fidelity: float
    rules: dict[int, list[ClusterRule]]
    integer_features: set[str]


def fit_rules(features: pd.DataFrame, labels: np.ndarray, max_depth: int = 4) -> RuleSet:
    F = features.to_numpy(dtype=float)
    names = list(features.columns)
    integer_features = {c for c in names if np.all(np.mod(features[c].to_numpy(dtype=float), 1) == 0)}
    tree = DecisionTreeClassifier(
        max_depth=max_depth, min_samples_leaf=max(5, int(0.01 * len(F))), random_state=42
    ).fit(F, labels)
    fidelity = float((tree.predict(F) == labels).mean())

    leaf_of = tree.apply(F)
    cluster_sizes = {c: int((labels == c).sum()) for c in np.unique(labels)}
    rules: dict[int, list[ClusterRule]] = defaultdict(list)
    for leaf, conditions in _leaf_paths(tree, names).items():
        in_leaf = leaf_of == leaf
        if not in_leaf.any():
            continue
        values, counts = np.unique(labels[in_leaf], return_counts=True)
        majority, hits = int(values[counts.argmax()]), int(counts.max())
        precision = hits / int(in_leaf.sum())
        if precision < MIN_PRECISION:
            continue
        conditions = _simplify(conditions)
        rules[majority].append(
            ClusterRule(
                text=rule_text(conditions, integer_features),
                conditions=conditions,
                precision=round(precision, 3),
                coverage=round(hits / cluster_sizes[majority], 3),
                support=int(in_leaf.sum()),
            )
        )

    top = {c: sorted(rs, key=lambda r: r.coverage, reverse=True)[:MAX_RULES_PER_CLUSTER] for c, rs in rules.items()}
    return RuleSet(tree=tree, feature_names=names, fidelity=round(fidelity, 3), rules=top, integer_features=integer_features)


def explain_row(rule_set: RuleSet, row: pd.Series) -> tuple[int, list[str]]:
    """Camino de decisión de un cliente: (cluster predicho, condiciones que cumplió)."""
    x = row[rule_set.feature_names].to_numpy(dtype=float).reshape(1, -1)
    t = rule_set.tree.tree_
    steps = []
    for node in rule_set.tree.decision_path(x).indices:
        if t.children_left[node] == t.children_right[node]:
            continue
        feature = rule_set.feature_names[t.feature[node]]
        op = "<=" if x[0, t.feature[node]] <= t.threshold[node] else ">"
        cond = Condition(feature=feature, op=op, threshold=float(t.threshold[node]))
        steps.append(f"{_condition_text(cond, rule_set.integer_features)} (valor: {_fmt(float(row[feature]))})")
    return int(rule_set.tree.predict(x)[0]), steps


def _leaf_paths(tree: DecisionTreeClassifier, names: list[str]) -> dict[int, list[Condition]]:
    t = tree.tree_
    paths: dict[int, list[Condition]] = {}
    stack: list[tuple[int, list[Condition]]] = [(0, [])]
    while stack:
        node, conds = stack.pop()
        left, right = t.children_left[node], t.children_right[node]
        if left == right:
            paths[node] = conds
            continue
        feature, threshold = names[t.feature[node]], float(t.threshold[node])
        stack.append((left, conds + [Condition(feature=feature, op="<=", threshold=threshold)]))
        stack.append((right, conds + [Condition(feature=feature, op=">", threshold=threshold)]))
    return paths


def _simplify(conditions: list[Condition]) -> list[Condition]:
    """Junta condiciones repetidas sobre una misma feature (x > 5 Y x > 10 -> x > 10)."""
    best: dict[tuple[str, str], float] = {}
    for c in conditions:
        key = (c.feature, c.op)
        if key not in best:
            best[key] = c.threshold
        else:
            best[key] = min(best[key], c.threshold) if c.op == "<=" else max(best[key], c.threshold)
    return [Condition(feature=f, op=op, threshold=t) for (f, op), t in best.items()]


def rule_text(conditions: list[Condition], integer_features: set[str]) -> str:
    by_feature: dict[str, dict[str, Condition]] = defaultdict(dict)
    for c in conditions:
        by_feature[c.feature][c.op] = c
    parts = []
    for feature, ops in by_feature.items():
        if "<=" in ops and ">" in ops and "=" not in feature:
            lo, hi = _display(ops[">"], integer_features), _display(ops["<="], integer_features)
            parts.append(f"{lo} < {feature} ≤ {hi}")
        else:
            parts.extend(_condition_text(c, integer_features) for c in ops.values())
    return " Y ".join(parts) if parts else "todos los clientes"


def _condition_text(c: Condition, integer_features: set[str]) -> str:
    if "=" in c.feature:  # one-hot: "genero=F"
        base, value = c.feature.split("=", 1)
        return f"{base} = {value}" if c.op == ">" else f"{base} ≠ {value}"
    symbol = "≤" if c.op == "<=" else ">"
    return f"{c.feature} {symbol} {_display(c, integer_features)}"


def _display(c: Condition, integer_features: set[str]) -> str:
    # En features enteras, x ≤ 30.5 equivale a x ≤ 30 y x > 30.5 a x > 30.
    return _fmt(float(np.floor(c.threshold))) if c.feature in integer_features else _fmt(c.threshold)


def _fmt(x: float) -> str:
    if abs(x) >= 100 or float(x).is_integer():
        return f"{x:,.0f}"
    if abs(x) >= 1:
        return f"{x:,.1f}"
    return f"{x:.2f}"
