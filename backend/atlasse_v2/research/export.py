"""Export research artifacts to Markdown, CSV, configs, and notebook formats."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


class ResearchExporter:
    SUPPORTED = {"markdown", "pdf", "latex", "jupyter", "csv", "tensorboard", "configs"}

    def export(self, report: dict, formats: list[str], out_dir: Path) -> dict:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        written: list[str] = []
        errors: list[dict] = []

        for fmt in formats:
            fmt = fmt.lower().strip()
            if fmt not in self.SUPPORTED:
                errors.append({"format": fmt, "error": "unsupported_format"})
                continue
            try:
                path = self._export_one(report, fmt, out_dir)
                if path:
                    written.append(str(path))
            except Exception as exc:
                errors.append({"format": fmt, "error": str(exc)})

        manifest = {
            "paper_id": report.get("paper_id"),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "files": written,
            "errors": errors,
        }
        manifest_path = out_dir / "export_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))
        written.append(str(manifest_path))
        return manifest

    def _export_one(self, report: dict, fmt: str, out_dir: Path) -> Path | None:
        paper_id = report.get("paper_id", "paper")
        notebook = report.get("notebook", {})

        if fmt == "markdown":
            path = out_dir / f"{paper_id}_notebook.md"
            path.write_text(notebook.get("markdown", ""))
            return path

        if fmt == "csv":
            path = out_dir / f"{paper_id}_metrics.csv"
            rows = []
            paper_m = report.get("failure_analysis", {}).get("paper_metrics", {})
            rows.append(["source", "metric_text", "missing", "confidence"])
            rows.append([
                "paper",
                paper_m.get("text", ""),
                paper_m.get("missing", ""),
                paper_m.get("confidence", ""),
            ])
            obs = report.get("failure_analysis", {}).get("observed_metrics")
            if obs:
                for k, v in obs.items():
                    rows.append(["observed", k, v, ""])
            with path.open("w", newline="") as f:
                csv.writer(f).writerows(rows)
            return path

        if fmt == "configs":
            path = out_dir / f"{paper_id}_experiment_configs.json"
            configs = {
                "experiments": report.get("experiment_plan", {}).get("experiments", []),
                "ablations": report.get("ablation_plan", {}).get("experiments", []),
                "sensitivity": report.get("sensitivity_analysis", {}).get("variations", []),
            }
            path.write_text(json.dumps(configs, indent=2))
            return path

        if fmt == "jupyter":
            path = out_dir / f"{paper_id}_research.ipynb"
            cells = [
                {"cell_type": "markdown", "metadata": {}, "source": [notebook.get("markdown", "")]},
            ]
            nb = {
                "nbformat": 4,
                "nbformat_minor": 5,
                "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
                "cells": cells,
            }
            path.write_text(json.dumps(nb, indent=2))
            return path

        if fmt == "latex":
            path = out_dir / f"{paper_id}_notebook.tex"
            md = notebook.get("markdown", "").replace("&", "\\&").replace("%", "\\%")
            path.write_text(f"\\documentclass{{article}}\n\\begin{{document}}\n\\begin{{verbatim}}\n{md}\n\\end{{verbatim}}\n\\end{{document}}\n")
            return path

        if fmt == "pdf":
            # PDF requires external toolchain — emit LaTeX + instructions
            tex = self._export_one(report, "latex", out_dir)
            note = out_dir / f"{paper_id}_pdf_instructions.txt"
            note.write_text(
                f"Compile PDF from: {tex}\nRun: pdflatex {tex.name}\n"
                "Or export markdown and use pandoc: pandoc notebook.md -o notebook.pdf"
            )
            return note

        if fmt == "tensorboard":
            path = out_dir / f"{paper_id}_tensorboard_scalars.json"
            plots = report.get("sensitivity_analysis", {}).get("plots", [])
            path.write_text(json.dumps({"scalar_series": plots}, indent=2))
            return path

        return None
