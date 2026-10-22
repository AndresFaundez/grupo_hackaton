"""Genera data/samples/synthetic_tx.csv (+ synthetic_truth.csv con el segmento plantado).

Uso: python scripts/make_synthetic.py [--customers 2000] [--seed 7]
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.synthetic import generate  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--customers", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "samples")
    args = parser.parse_args()

    tx, truth = generate(args.customers, args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    tx.to_csv(args.out / "synthetic_tx.csv", index=False)
    truth.to_csv(args.out / "synthetic_truth.csv", index=False)
    print(f"{len(tx):,} transacciones de {len(truth):,} clientes -> {args.out / 'synthetic_tx.csv'}")
    print(truth["segmento"].value_counts().to_string())


if __name__ == "__main__":
    main()
