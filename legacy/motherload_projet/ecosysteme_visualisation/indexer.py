"""Indexation simple du code."""

from __future__ import annotations

import ast
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from motherload_projet.library.paths import ensure_dir, library_root


def _ecosystem_root() -> Path:
    """Retourne le dossier ecosysteme."""
    root = ensure_dir(library_root() / "ecosysteme_visualisation")
    ensure_dir(root / "notes")
    return root


def index_path() -> Path:
    """Retourne le chemin d index."""
    return _ecosystem_root() / "index.json"


def notes_root() -> Path:
    """Retourne le dossier des notes."""
    return _ecosystem_root() / "notes"


def _node_filename(node_id: str) -> str:
    """Genere un nom de fichier safe."""
    cleaned = re.sub(r"[^A-Za-z0-9_.-]", "_", node_id)
    return f"{cleaned}.txt"


def notes_path(node_id: str) -> Path:
    """Retourne le chemin de note."""
    return notes_root() / _node_filename(node_id)


def load_notes(node_id: str) -> str:
    """Charge une note."""
    path = notes_path(node_id)
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def save_notes(node_id: str, text: str) -> None:
    """Sauvegarde une note."""
    path = notes_path(node_id)
    try:
        path.write_text(text.rstrip() + "\n", encoding="utf-8")
    except OSError:
        return


def load_index() -> dict[str, Any]:
    """Charge l index existant."""
    path = index_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_index(index: dict[str, Any]) -> Path:
    """Ecrit l index sur disque."""
    path = index_path()
    path.write_text(json.dumps(index, ensure_ascii=True, indent=2), encoding="utf-8")
    return path


def _first_sentence(text: str) -> str:
    """Retourne la premiere phrase."""
    cleaned = " ".join((text or "").strip().split())
    if not cleaned:
        return ""
    for token in (".", "!", "?"):
        if token in cleaned:
            return cleaned.split(token, 1)[0].strip() + token
    return cleaned


def _extract_output(text: str) -> str:
    """Extrait une sortie depuis la docstring."""
    if not text:
        return ""
    match = re.search(r"Retourne\s+([^\n\.]+)", text, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r"Return[s]?\s+([^\n\.]+)", text, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def _infer_module_outputs(module_name: str, doc: str) -> str:
    """Devine les sorties d un module."""
    name = module_name.lower()
    if "maintenance_manager" in name:
        return "Maintenance et updates"
    if "connecteurs" in name:
        return "Connecteurs externes"
    if "note_systeme" in name:
        return "Notes et bugs"
    if "data_mining" in name:
        return "Extraction et telechargements"
    if "recuperation_oa" in name:
        return "Liens Open Access"
    if "recuperation_article" in name:
        return "Batchs OA et proxy"
    if "download" in name:
        return "PDFs telecharges"
    if "report" in name:
        return "Rapports texte"
    if "desktop_app" in name or "ui" in name:
        return "Interface utilisateur"
    if "ingest" in name:
        return "Master catalog mis a jour"
    if "workflow" in name:
        return "CSVs + rapports"
    if "library" in name:
        return "Catalogue + chemins"
    if "oa" in name:
        return "Liens OA"
    sentence = _first_sentence(doc)
    return sentence or "Sorties diverses"


def _completion_score(text: str, name: str, base: int = 75) -> int:
    """Estime un pourcentage de completion."""
    lowered = (text or "").lower()
    if "todo" in lowered or "wip" in lowered or "phase suivante" in lowered:
        return 45
    if name.startswith("_"):
        return min(90, base + 10)
    return base


def _module_summary(doc: str) -> str:
    """Resume un module."""
    sentence = _first_sentence(doc)
    return sentence or "Module de l ecosysteme Motherload."


def _function_summary(name: str, doc: str) -> str:
    """Resume une fonction."""
    if doc:
        return _first_sentence(doc)
    if name.startswith("get_"):
        return "Recupere une valeur de configuration."
    if name.startswith("load_"):
        return "Charge des donnees depuis disque."
    if name.startswith("save_"):
        return "Sauvegarde des donnees sur disque."
    if name.startswith("run_"):
        return "Execute un workflow principal."
    if name.startswith("count_"):
        return "Compte des elements dans la bibliotheque."
    return "Fonction utilitaire de l ecosysteme."


def _detail_text(summary: str, outputs: str) -> str:
    """Construit un detail long."""
    summary = summary or "Fonction de l ecosysteme."
    outputs = outputs or "Sorties variables."
    return (
        f"Objectif: {summary}\n"
        f"But: Supporter le flux Motherload et garder la coherence.\n"
        f"Fait: {outputs}."
    )


def _signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Construit une signature simple."""
    parts: list[str] = []
    for arg in node.args.args:
        parts.append(arg.arg)
    if node.args.vararg:
        parts.append(f"*{node.args.vararg.arg}")
    for arg in node.args.kwonlyargs:
        parts.append(arg.arg)
    if node.args.kwarg:
        parts.append(f"**{node.args.kwarg.arg}")
    return f"({', '.join(parts)})"


def scan_codebase(code_root: Path) -> dict[str, Any]:
    """Scanne le code et genere un index."""
    code_root = Path(code_root)
    nodes: list[dict[str, Any]] = []
    root_id = "pkg:motherload_projet"
    nodes.append(
        {
            "id": root_id,
            "parent": None,
            "type": "package",
            "name": "motherload_projet",
            "summary": "Package racine de l ecosysteme Motherload.",
            "outputs": "Modules de traitement PDF et bibliotheque",
            "completion": 70,
            "detail": _detail_text(
                "Package racine de l ecosysteme Motherload.",
                "Modules de traitement PDF et bibliotheque",
            ),
        }
    )

    package_nodes: dict[str, dict[str, Any]] = {}

    for path in sorted(code_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        if path.name.startswith("."):
            continue
        rel = path.relative_to(code_root)
        module_stem = rel.with_suffix("")
        parts = list(module_stem.parts)
        if not parts:
            continue
        if parts[-1] == "__init__":
            parts = parts[:-1]
        module_name = ".".join(parts)
        if not module_name:
            continue

        package_name = parts[0] if len(parts) > 1 else ""
        package_id = f"pkg:{package_name}" if package_name else root_id
        if package_name and package_id not in package_nodes:
            package_nodes[package_id] = {
                "id": package_id,
                "parent": root_id,
                "type": "package",
                "name": package_name,
                "summary": f"Sous-package {package_name}.",
                "outputs": "Fonctions specialisees",
                "completion": 70,
                "detail": _detail_text(
                    f"Sous-package {package_name}.",
                    "Fonctions specialisees",
                ),
                "_modules": [],
            }

        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        module_doc = ast.get_docstring(tree) or ""
        module_summary = _module_summary(module_doc)
        module_outputs = _infer_module_outputs(module_name, module_doc)

        functions: list[dict[str, Any]] = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_doc = ast.get_docstring(node) or ""
                func_summary = _function_summary(node.name, func_doc)
                func_output = _extract_output(func_doc)
                if not func_output and node.returns is not None:
                    try:
                        func_output = ast.unparse(node.returns)
                    except Exception:
                        func_output = ""
                func_output = func_output or "Sortie variable"
                func_completion = _completion_score(func_doc, node.name, base=75)
                func_id = f"func:{module_name}.{node.name}"
                functions.append(
                    {
                        "id": func_id,
                        "parent": f"mod:{module_name}",
                        "type": "function",
                        "name": node.name,
                        "module": module_name,
                        "signature": _signature(node),
                        "summary": func_summary,
                        "outputs": func_output,
                        "completion": func_completion,
                        "detail": _detail_text(func_summary, func_output),
                    }
                )

        main_functions = [item["name"] for item in functions if not item["name"].startswith("_")]
        if not main_functions:
            main_functions = [item["name"] for item in functions]
        main_functions = main_functions[:3]

        module_completion = 70
        if functions:
            module_completion = int(sum(item["completion"] for item in functions) / len(functions))

        module_id = f"mod:{module_name}"
        module_node = {
            "id": module_id,
            "parent": package_id,
            "type": "module",
            "name": module_name,
            "path": str(path),
            "summary": module_summary,
            "outputs": module_outputs,
            "completion": module_completion,
            "main_functions": main_functions,
            "detail": _detail_text(module_summary, module_outputs),
        }
        nodes.append(module_node)
        nodes.extend(functions)

        if package_id in package_nodes:
            package_nodes[package_id]["_modules"].append(module_node)

    for package_id, package_node in package_nodes.items():
        modules = package_node.pop("_modules", [])
        if modules:
            package_node["completion"] = int(
                sum(mod["completion"] for mod in modules) / len(modules)
            )
            outputs = " / ".join(
                sorted({mod.get("outputs", "") for mod in modules if mod.get("outputs")})
            )
            package_node["outputs"] = outputs or package_node.get("outputs", "")
            package_node["detail"] = _detail_text(
                package_node.get("summary", ""), package_node.get("outputs", "")
            )
        nodes.append(package_node)

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": "motherload_projet",
        "nodes": nodes,
    }


def rebuild_index(code_root: Path) -> dict[str, Any]:
    """Reconstruit et sauve l index."""
    index = scan_codebase(code_root)
    write_index(index)
    return index
