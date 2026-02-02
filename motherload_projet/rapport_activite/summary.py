"""Sommaire de reporting."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_report(df: pd.DataFrame, report_path: Path) -> Path:
    """Ecrit un rapport simple."""
    if report_path.exists():
        raise FileExistsError("Rapport deja present.")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "Rapport motherload_projet",
        f"Lignes: {len(df)}",
        f"Colonnes: {', '.join(df.columns)}",
    ]

    if "type" in df.columns:
        counts = df["type"].value_counts()
        lines.append("Types:")
        for item_type, count in counts.items():
            lines.append(f"- {item_type}: {count}")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path
