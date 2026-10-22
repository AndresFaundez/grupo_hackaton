"""Lectura de CSV/Excel, conversión de tipos y perfil de columnas con detección de PII."""

from __future__ import annotations

import csv
import io
import re
import unicodedata
import warnings
from pathlib import Path

import pandas as pd

from app.models import ColumnProfile

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")
RUT_RE = re.compile(r"^\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]$")
PHONE_RE = re.compile(r"^\+\d[\d\s\-()]{7,}$|^\(?\d{2,4}\)?[\s\-]\d{3,4}[\s\-]?\d{3,4}$")

STRONG_PII_TOKENS = {
    "email", "correo", "mail", "telefono", "phone", "celular", "movil", "fono", "rut", "dni",
    "direccion", "address", "apellido", "apellidos", "lastname", "surname", "firstname",
}
NAME_TOKENS = {"name", "nombre", "nombres"}
NAME_COMPANIONS = {"customer", "cliente", "client", "first", "last", "full", "contact", "contacto", "completo"}


def tokens(column: str) -> list[str]:
    """`NombreCliente` / `nombre_cliente` / `Nombre Cliente` -> ["nombre", "cliente"]."""
    text = unicodedata.normalize("NFKD", column).encode("ascii", "ignore").decode()
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    return [t for t in re.split(r"[^a-zA-Z0-9]+", text.lower()) if t]


def slugify(column: str) -> str:
    return "_".join(tokens(column)) or "col"


def read_table(content: bytes, filename: str) -> pd.DataFrame:
    suffix = Path(filename).suffix.lower()
    if suffix in {".xlsx", ".xlsm", ".xls"}:
        df = pd.read_excel(io.BytesIO(content))
    else:
        text = _decode(content)
        try:
            sep = csv.Sniffer().sniff(text[:20_000], delimiters=",;\t|").delimiter
        except csv.Error:
            sep = ","
        df = pd.read_csv(io.StringIO(text), sep=sep, low_memory=False)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")
    return coerce_types(df)


def _decode(content: bytes) -> str:
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte columnas de texto que en realidad son fechas o números."""
    df = df.copy()
    for col in df.columns:
        s = df[col]
        if not (pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s)):
            continue
        non_null = s.dropna().astype(str).str.strip()
        if non_null.empty:
            continue
        sample = non_null.sample(min(len(non_null), 2000), random_state=0)

        # Fechas: excluir columnas de solo dígitos (IDs) que pandas parsearía como fechas.
        if sample.str.fullmatch(r"\d+").mean() < 0.5:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                parsed = pd.to_datetime(sample, errors="coerce")
            if parsed.notna().mean() >= 0.9:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    df[col] = pd.to_datetime(s, errors="coerce")
                continue

        numeric = pd.to_numeric(sample, errors="coerce")
        if numeric.notna().mean() >= 0.98 and not sample.str.match(r"^0\d").any():
            df[col] = pd.to_numeric(s, errors="coerce")
    return df


def detect_pii(column: str, series: pd.Series) -> str | None:
    """Devuelve el tipo de PII detectado (email, rut, teléfono, nombre...) o None."""
    toks = set(tokens(column))
    for tok in toks & STRONG_PII_TOKENS:
        return tok
    if toks & NAME_TOKENS and (toks - NAME_TOKENS) <= NAME_COMPANIONS:
        return "nombre"

    if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_datetime64_any_dtype(series):
        return None
    values = series.dropna().astype(str).str.strip()
    if values.empty:
        return None
    values = values.sample(min(len(values), 500), random_state=0)
    for kind, pattern in (("email", EMAIL_RE), ("rut", RUT_RE), ("telefono", PHONE_RE)):
        if values.map(lambda v: bool(pattern.match(v))).mean() >= 0.8:
            return kind
    return None


def profile_columns(df: pd.DataFrame) -> list[ColumnProfile]:
    profiles = []
    for col in df.columns:
        s = df[col]
        pii_kind = detect_pii(col, s)
        examples = [str(v)[:40] for v in s.dropna().unique()[:3]]
        if pii_kind:
            examples = [f"[{pii_kind} oculto]"] * len(examples)

        stats: dict[str, float | str] | None = None
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            desc = s.describe()
            stats = {k: round(float(desc[k]), 4) for k in ("min", "max", "mean", "50%") if pd.notna(desc.get(k))}
        elif pd.api.types.is_datetime64_any_dtype(s):
            stats = {"min": str(s.min()), "max": str(s.max())}

        profiles.append(
            ColumnProfile(
                name=col,
                dtype=str(s.dtype),
                n_null=int(s.isna().sum()),
                n_unique=int(s.nunique(dropna=True)),
                examples=examples,
                pii_suspect=pii_kind is not None,
                stats=stats,
            )
        )
    return profiles


def preview_rows(df: pd.DataFrame, n: int = 10) -> list[dict]:
    head = df.head(n)
    return [{k: (None if pd.isna(v) else str(v)) for k, v in row.items()} for row in head.to_dict(orient="records")]
