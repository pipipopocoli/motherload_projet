"""App desktop pour ingestion manuelle."""

from __future__ import annotations

from pathlib import Path
from datetime import datetime
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, simpledialog, ttk
from urllib.parse import unquote

import pandas as pd

from motherload_projet.config import get_manual_import_subdir
from motherload_projet.maintenance_manager.deps import (
    list_outdated,
    start_auto_update,
    upgrade_requirements,
)
from motherload_projet.ecosysteme_visualisation.indexer import (
    index_path,
    load_index,
    load_notes,
    notes_path,
    rebuild_index,
)
from motherload_projet.desktop_app.data import (
    count_indexed_articles,
    count_indexed_books,
    count_indexed_unknown,
    count_missing_pdfs,
    count_pdfs,
    count_references,
    count_to_be_downloaded,
    load_scan_runs,
    load_master_frame,
    search_pdfs_by_keyword,
    search_master,
    zotero_counts,
)
from motherload_projet.desktop_app.state import compute_progress, load_state, reset_tasks, save_state
from motherload_projet.local_pdf_update.local_pdf import (
    ingest_pdf,
    write_manual_ingest_report,
)
from motherload_projet.catalogs.scanner import scan_library as run_scan_library
from motherload_projet.library.paths import (
    bibliotheque_root,
    collections_root,
    ensure_dir,
    library_root,
)
from motherload_projet.data_mining.recuperation_article.run_unpaywall_batch import (
    run_unpaywall_csv_batch,
)

try:  # optionnel
    from motherload_projet.ecosysteme_visualisation.watcher import start_watchdog

    _WATCHDOG_AVAILABLE = True
except Exception:
    _WATCHDOG_AVAILABLE = False

try:  # optionnel
    from tkinterdnd2 import DND_FILES, TkinterDnD

    _DND_AVAILABLE = True
except Exception:
    _DND_AVAILABLE = False


def _list_collections(root: Path) -> list[Path]:
    """Liste les collections disponibles."""
    collections = [path for path in root.rglob("*") if path.is_dir()]
    return sorted(collections, key=lambda path: str(path.relative_to(root)).lower())


def _collection_label(path: Path, base: Path) -> str:
    """Formate un label de collection."""
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def _is_valid_collection_name(name: str) -> bool:
    """Valide un nom de collection."""
    if not name:
        return False
    candidate = Path(name)
    if candidate.is_absolute():
        return False
    return ".." not in candidate.parts


def _last_collection_path() -> Path:
    """Retourne le path du dernier choix."""
    return library_root() / ".last_collection"


def _load_last_collection() -> str | None:
    """Charge la derniere collection."""
    path = _last_collection_path()
    if not path.exists():
        return None
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


def _save_last_collection(label: str) -> None:
    """Sauvegarde la derniere collection."""
    path = _last_collection_path()
    try:
        path.write_text(label + "\n", encoding="utf-8")
    except OSError:
        return


def _normalize_path(item: str) -> str:
    """Normalise un chemin colle."""
    value = item.strip().strip("{}")
    if value.startswith("file://"):
        value = value[7:]
    if value.startswith("file:/"):
        value = value[6:]
    return unquote(value)


def _slugify(text: str) -> str:
    """Nettoie un texte pour nom de fichier."""
    cleaned = "".join(char if char.isalnum() or char in ("_", "-") else "_" for char in text)
    cleaned = "_".join(part for part in cleaned.split("_") if part)
    return cleaned[:60] or "groupe"


def _filter_files(paths: tuple[str, ...]) -> list[str]:
    """Filtre les chemins valides."""
    results: list[str] = []
    for item in paths:
        candidate = Path(_normalize_path(item)).expanduser()
        if candidate.exists() and candidate.is_file():
            results.append(str(candidate))
    return results


def _check_tk_support() -> None:
    """Verifie la compatibilite Tk."""
    executable = sys.executable or ""
    if "CommandLineTools/Library/Frameworks/Python3.framework" in executable:
        raise RuntimeError(
            "Python CommandLineTools non supporte pour Tkinter. "
            "Utilise Python.org ou Homebrew (Tk 8.6+) et recree la venv."
        )
    tcl_version = getattr(tk, "TclVersion", 0)
    if tcl_version and tcl_version < 8.6:
        raise RuntimeError(
            "Tcl/Tk 8.5 detecte. Installe Python avec Tk 8.6+ "
            "ou recree la venv avec ce Python."
        )


def _open_path(path: Path) -> bool:
    """Ouvre un fichier local."""
    if not path.exists():
        return False
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        elif os.name == "nt":
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
        return True
    except OSError:
        return False


def run_app() -> None:
    """Lance l app Tkinter."""
    _check_tk_support()
    base_dir = ensure_dir(collections_root())
    collections: list[Path] = []
    labels: list[str] = []
    collection_boxes: list[ttk.Combobox] = []
    csv_start_ref = {"fn": None}
    csv_tab_ref = {"tab": None}

    def _create_root() -> tk.Tk:
        if _DND_AVAILABLE:
            try:
                return TkinterDnD.Tk()
            except Exception:
                return tk.Tk()
        return tk.Tk()

    try:
        root = _create_root()
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Tkinter indisponible. Verifiez votre installation Python."
        ) from exc

    root.title("Motherload - Ingestion manuelle")
    root.geometry("900x720")

    status_var = tk.StringVar(value="")

    def set_status(message: str) -> None:
        status_var.set(message)

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # --- Onglet Ingestion ---
    ingest_tab = ttk.Frame(notebook, padding=12)
    notebook.add(ingest_tab, text="Ingestion")

    collection_var = tk.StringVar()
    subdir_var = tk.StringVar(value=get_manual_import_subdir())

    def refresh_collections() -> None:
        nonlocal collections, labels
        collections = _list_collections(base_dir)
        labels = [_collection_label(path, base_dir) for path in collections]
        for box in collection_boxes:
            box["values"] = labels
        current = collection_var.get().strip()
        if current and current in labels:
            return
        if labels:
            collection_var.set(labels[0])

    def resolve_collection_path(label: str) -> Path | None:
        if not label:
            return None
        candidate = Path(label)
        if not candidate.is_absolute():
            candidate = base_dir / candidate
        return candidate

    refresh_collections()
    last = _load_last_collection()
    if last and last in labels:
        collection_var.set(last)

    log_text = tk.Text(ingest_tab, height=12, state="disabled")

    def append_log(message: str) -> None:
        log_text.configure(state="normal")
        log_text.insert("end", message + "\n")
        log_text.configure(state="disabled")
        log_text.see("end")

    def on_collection_change(*_args: object) -> None:
        value = collection_var.get().strip()
        if value:
            _save_last_collection(value)

    def handle_files(paths: list[str]) -> None:
        if not labels:
            append_log("Aucune collection disponible.")
            return
        collection_label = collection_var.get().strip()
        if not collection_label:
            append_log("Collection manquante.")
            return
        subdir_value = subdir_var.get().strip() or get_manual_import_subdir()
        results = []
        for item in paths:
            result = ingest_pdf(Path(item), collection_label, subdir_value)
            results.append(result)
            if result.get("status") == "ok":
                append_log(f"OK -> {result.get('pdf_path')}")
            elif result.get("reason_code") == "DUPLICATE_HASH":
                append_log(f"DUPLICATE_HASH -> {Path(item).name}")
            else:
                error = result.get("error") or result.get("reason_code")
                append_log(f"ERROR -> {Path(item).name}: {error}")
        if results:
            report_path = write_manual_ingest_report(results)
            append_log(f"Rapport: {report_path}")

    def choose_files() -> None:
        files = filedialog.askopenfilenames(
            title="Choisir des PDFs ou EPUBs",
            filetypes=[("PDF/EPUB", "*.pdf *.epub"), ("PDF", "*.pdf"), ("EPUB", "*.epub")],
        )
        selected = _filter_files(files)
        if selected:
            handle_files(selected)

    ttk.Label(ingest_tab, text="Collection").pack(anchor="w")
    collection_box = ttk.Combobox(ingest_tab, textvariable=collection_var, values=labels)
    collection_box.state(["readonly"])
    collection_box.pack(fill="x", pady=(0, 8))
    collection_boxes.append(collection_box)
    collection_var.trace_add("write", on_collection_change)

    def create_collection() -> None:
        name = simpledialog.askstring("Nouvelle collection", "Nom collection:")
        if name is None:
            return
        name = name.strip()
        if not _is_valid_collection_name(name):
            append_log("Nom invalide.")
            return
        target = base_dir / Path(name)
        if target.exists():
            append_log("La collection existe deja.")
            return
        try:
            target.mkdir(parents=True, exist_ok=False)
        except OSError as exc:
            append_log(f"Erreur creation collection: {exc}")
            return
        refresh_collections()
        collection_var.set(_collection_label(target, base_dir))
        append_log(f"Collection creee: {name}")

    ttk.Label(ingest_tab, text="Subdir").pack(anchor="w")
    subdir_entry = ttk.Entry(ingest_tab, textvariable=subdir_var)
    subdir_entry.pack(fill="x", pady=(0, 12))

    buttons_row = ttk.Frame(ingest_tab)
    buttons_row.pack(fill="x", pady=(0, 8))
    ttk.Button(buttons_row, text="Choisir PDF/EPUB", command=choose_files).pack(
        side="left"
    )
    ttk.Button(buttons_row, text="Nouvelle collection", command=create_collection).pack(
        side="left", padx=(8, 0)
    )

    if _DND_AVAILABLE:
        drop_label = ttk.Label(
            ingest_tab,
            text="Glisser PDF/EPUB ou CSV ici",
            relief="ridge",
            padding=18,
            anchor="center",
        )
        drop_label.pack(fill="x", pady=(0, 8))

        def on_drop(event: tk.Event) -> None:
            raw = root.tk.splitlist(event.data)
            selected = _filter_files(tuple(raw))
            if not selected:
                return
            csv_candidate = None
            for item in selected:
                if Path(item).suffix.lower() == ".csv":
                    csv_candidate = Path(item)
                    break
            if csv_candidate is not None:
                if csv_tab_ref["tab"] is not None:
                    notebook.select(csv_tab_ref["tab"])
                if csv_start_ref["fn"] is not None:
                    csv_start_ref["fn"](csv_candidate)
                    append_log(f"CSV detecte -> recherche web: {csv_candidate}")
                else:
                    append_log("CSV detecte mais recherche web indisponible.")
                return
            docs = [
                item
                for item in selected
                if Path(item).suffix.lower() in {".pdf", ".epub"}
            ]
            if docs:
                handle_files(docs)

        drop_label.drop_target_register(DND_FILES)
        drop_label.dnd_bind("<<Drop>>", on_drop)
    else:
        ttk.Label(
            ingest_tab,
            text="Drag & drop indisponible. Installer: pip install tkinterdnd2",
        ).pack(anchor="w", pady=(0, 8))

    ttk.Label(ingest_tab, text="Log").pack(anchor="w")
    log_text.pack(fill="both", expand=True)

    if not labels:
        append_log("Aucune collection detectee. Creez un dossier dans collections/.")

    # --- Onglet Recherche Web (CSV) ---
    csv_tab = ttk.Frame(notebook, padding=12)
    notebook.add(csv_tab, text="Recherche web")
    csv_tab_ref["tab"] = csv_tab

    csv_status_var = tk.StringVar(value="")
    csv_step_var = tk.StringVar(value="")
    csv_limit_var = tk.StringVar(value="")
    csv_running = {"active": False}
    csv_spinner_job: list[str | None] = [None]
    csv_spinner_angle = {"value": 0}

    def _set_csv_status(message: str) -> None:
        csv_status_var.set(message)

    def _draw_csv_spinner() -> None:
        if not csv_running["active"]:
            csv_spinner.delete("all")
            csv_spinner_job[0] = None
            return
        csv_spinner.delete("all")
        angle = csv_spinner_angle["value"]
        csv_spinner.create_arc(2, 2, 18, 18, start=angle, extent=270, style="arc", width=3)
        csv_spinner_angle["value"] = (angle + 30) % 360
        csv_spinner_job[0] = root.after(120, _draw_csv_spinner)

    def _start_csv_spinner() -> None:
        if csv_spinner_job[0] is None:
            csv_running["active"] = True
            _draw_csv_spinner()

    def _stop_csv_spinner() -> None:
        csv_running["active"] = False
        if csv_spinner_job[0] is not None:
            try:
                root.after_cancel(csv_spinner_job[0])
            except Exception:
                pass
            csv_spinner_job[0] = None
        csv_spinner.delete("all")

    csv_progress = ttk.Progressbar(csv_tab, length=320, maximum=100)
    csv_spinner = tk.Canvas(csv_tab, width=20, height=20, highlightthickness=0)

    def _update_csv_progress(event: dict) -> None:
        stage = event.get("stage")
        if stage == "start":
            total = int(event.get("total") or 0)
            csv_progress["maximum"] = max(total, 1)
            csv_progress["value"] = 0
            csv_running["active"] = True
            _start_csv_spinner()
            csv_step_var.set("Etape: Lecture CSV")
            _set_csv_status("Lecture CSV et demarrage du batch...")
            return
        if stage == "item":
            done = int(event.get("done") or 0)
            total = int(event.get("total") or 0)
            csv_progress["maximum"] = max(total, 1)
            csv_progress["value"] = done
            doi = str(event.get("doi") or "")
            csv_step_var.set("Etape: Recherche OA / Telechargement")
            _set_csv_status(f"Traitement {done}/{total} {doi}")
            return
        if stage == "done":
            done = int(event.get("done") or 0)
            total = int(event.get("total") or 0)
            csv_progress["maximum"] = max(total, 1)
            csv_progress["value"] = done
            report_path = event.get("report_path")
            _stop_csv_spinner()
            csv_step_var.set("Etape: Termine")
            _set_csv_status(f"Termine. Rapport: {report_path}")
            return
        if stage == "cancelled":
            _stop_csv_spinner()
            csv_step_var.set("Etape: Annule")
            _set_csv_status("Annule.")

    def _run_csv_batch(csv_path: Path) -> None:
        label = collection_var.get().strip()
        collection_path = resolve_collection_path(label)
        if collection_path is None:
            root.after(0, lambda: _set_csv_status("Collection manquante."))
            return
        limit_value = None
        if csv_limit_var.get().strip().isdigit():
            limit_value = int(csv_limit_var.get().strip())

        def _cb(event: dict) -> None:
            root.after(0, lambda: _update_csv_progress(event))

        run_unpaywall_csv_batch(
            csv_path,
            collection_path,
            limit=limit_value,
            verbose_progress=False,
            progress_cb=_cb,
        )

    def start_csv_run(csv_path: Path) -> None:
        if csv_running["active"]:
            _set_csv_status("Un batch est deja en cours.")
            return
        if not csv_path.exists() or csv_path.suffix.lower() != ".csv":
            _set_csv_status("Fichier CSV invalide.")
            return
        csv_running["active"] = True
        thread = threading.Thread(target=_run_csv_batch, args=(csv_path,), daemon=True)
        thread.start()

    csv_start_ref["fn"] = start_csv_run

    def choose_csv() -> None:
        value = filedialog.askopenfilename(
            title="Choisir un CSV",
            filetypes=[("CSV", "*.csv")],
        )
        if value:
            start_csv_run(Path(value))

    def handle_csv_drop(paths: list[str]) -> None:
        for item in paths:
            path = Path(item)
            if path.suffix.lower() == ".csv":
                start_csv_run(path)
                return
        _set_csv_status("Aucun CSV detecte.")

    ttk.Label(csv_tab, text="Collection").pack(anchor="w")
    csv_collection_box = ttk.Combobox(csv_tab, textvariable=collection_var, values=labels)
    csv_collection_box.state(["readonly"])
    csv_collection_box.pack(fill="x", pady=(0, 8))
    collection_boxes.append(csv_collection_box)

    limit_row = ttk.Frame(csv_tab)
    limit_row.pack(fill="x", pady=(0, 8))
    ttk.Label(limit_row, text="Limite (option)").pack(side="left")
    ttk.Entry(limit_row, textvariable=csv_limit_var, width=8).pack(side="left", padx=(6, 0))

    ttk.Button(csv_tab, text="Choisir CSV", command=choose_csv).pack(anchor="w", pady=(0, 8))

    if _DND_AVAILABLE:
        csv_drop = ttk.Label(
            csv_tab,
            text="Glisser un CSV ici",
            relief="ridge",
            padding=14,
            anchor="center",
        )
        csv_drop.pack(fill="x", pady=(0, 8))

        def on_csv_drop(event: tk.Event) -> None:
            raw = root.tk.splitlist(event.data)
            selected = _filter_files(tuple(raw))
            if selected:
                handle_csv_drop(selected)

        csv_drop.drop_target_register(DND_FILES)
        csv_drop.dnd_bind("<<Drop>>", on_csv_drop)
    else:
        ttk.Label(csv_tab, text="Drag & drop indisponible (installe tkinterdnd2).").pack(
            anchor="w", pady=(0, 8)
        )

    progress_row = ttk.Frame(csv_tab)
    progress_row.pack(fill="x", pady=(4, 0))
    ttk.Label(progress_row, text="Progression").pack(side="left")
    csv_progress.pack(side="left", padx=(6, 6))
    csv_spinner.pack(side="left")
    ttk.Label(progress_row, textvariable=csv_step_var).pack(side="left", padx=(6, 0))

    ttk.Label(csv_tab, textvariable=csv_status_var).pack(anchor="w", pady=(6, 0))

    # --- Onglet Recherche ---
    search_tab = ttk.Frame(notebook, padding=12)
    notebook.add(search_tab, text="Recherche")

    search_var = tk.StringVar()
    field_var = tk.StringVar(value="Tous")
    master_df = load_master_frame()

    field_map = {
        "Tous": "all",
        "Titre": "title",
        "DOI": "doi",
        "Auteurs": "authors",
        "Annee": "year",
        "Mots-cles": "keywords",
        "Collection": "collection",
        "Chemin": "pdf_path",
    }

    def refresh_master() -> None:
        nonlocal master_df
        master_df = load_master_frame()
        set_status("Master catalog recharge.")

    def update_results(frame: ttk.Treeview, data: list[tuple[str, ...]]) -> None:
        for item in frame.get_children():
            frame.delete(item)
        for row in data:
            frame.insert("", "end", values=row)

    def run_search(*_args: object) -> None:
        query = search_var.get().strip()
        field_key = field_map.get(field_var.get(), "all")
        results = search_master(master_df, query, field_key)
        results = results.head(200)
        rows: list[tuple[str, ...]] = []
        for _, row in results.iterrows():
            rows.append(
                (
                    str(row.get("title", "")),
                    str(row.get("doi", "")),
                    str(row.get("year", "")),
                    str(row.get("collection", "")),
                    str(row.get("pdf_path", "")),
                )
            )
        update_results(results_view, rows)
        set_status(f"Resultats: {len(rows)}")

    search_row = ttk.Frame(search_tab)
    search_row.pack(fill="x", pady=(0, 8))
    ttk.Label(search_row, text="Recherche").pack(side="left")
    search_entry = ttk.Entry(search_row, textvariable=search_var)
    search_entry.pack(side="left", fill="x", expand=True, padx=6)
    field_box = ttk.Combobox(search_row, textvariable=field_var, values=list(field_map))
    field_box.state(["readonly"])
    field_box.pack(side="left", padx=6)
    ttk.Button(search_row, text="Rechercher", command=run_search).pack(side="left")
    ttk.Button(search_row, text="Rafraichir", command=refresh_master).pack(
        side="left", padx=(6, 0)
    )
    search_entry.bind("<Return>", run_search)

    results_view = ttk.Treeview(
        search_tab,
        columns=("title", "doi", "year", "collection", "pdf_path"),
        show="headings",
        height=12,
    )
    results_view.heading("title", text="Titre")
    results_view.heading("doi", text="DOI")
    results_view.heading("year", text="Annee")
    results_view.heading("collection", text="Collection")
    results_view.heading("pdf_path", text="Chemin PDF")
    results_view.column("title", width=260)
    results_view.column("doi", width=160)
    results_view.column("year", width=70)
    results_view.column("collection", width=120)
    results_view.column("pdf_path", width=280)

    results_scroll = ttk.Scrollbar(search_tab, orient="vertical", command=results_view.yview)
    results_view.configure(yscrollcommand=results_scroll.set)
    results_view.pack(side="left", fill="both", expand=True)
    results_scroll.pack(side="left", fill="y")

    def open_selected() -> None:
        selected = results_view.selection()
        if not selected:
            set_status("Aucun resultat selectionne.")
            return
        values = results_view.item(selected[0], "values")
        if not values or len(values) < 5:
            set_status("Chemin PDF manquant.")
            return
        path = Path(values[4]).expanduser()
        if not path.exists():
            set_status("PDF introuvable.")
            return
        if _open_path(path):
            set_status(f"Ouverture: {path}")
        else:
            set_status("Impossible d ouvrir le PDF.")

    ttk.Button(search_tab, text="Ouvrir PDF", command=open_selected).pack(
        anchor="w", pady=(8, 0)
    )
    results_view.bind("<Double-1>", lambda _event: open_selected())

    # --- Onglet Metadonnees ---
    meta_tab = ttk.Frame(notebook, padding=12)
    notebook.add(meta_tab, text="Metadonnees")

    meta_keyword_var = tk.StringVar()
    meta_pages_var = tk.StringVar(value="2")
    meta_status_var = tk.StringVar(value="")
    meta_activity_var = tk.StringVar(value="")
    meta_running = {"active": False}
    meta_activity_job: list[str | None] = [None]
    meta_progress = ttk.Progressbar(meta_tab, length=320, maximum=100)
    meta_results_paths: list[Path] = []

    def _set_meta_status(message: str) -> None:
        meta_status_var.set(message)

    def _start_meta_activity() -> None:
        if meta_activity_job[0] is not None:
            return
        frames = ["", ".", "..", "..."]

        def _tick(index: int = 0) -> None:
            if not meta_running["active"]:
                meta_activity_var.set("")
                meta_activity_job[0] = None
                return
            meta_activity_var.set(frames[index % len(frames)])
            meta_activity_job[0] = root.after(400, _tick, index + 1)

        _tick(0)

    def _stop_meta_activity() -> None:
        meta_running["active"] = False
        if meta_activity_job[0] is not None:
            try:
                root.after_cancel(meta_activity_job[0])
            except Exception:
                pass
            meta_activity_job[0] = None
        meta_activity_var.set("")

    meta_results_view = ttk.Treeview(
        meta_tab,
        columns=("title", "collection", "type", "pdf_path"),
        show="headings",
        height=12,
    )
    meta_results_view.heading("title", text="Titre")
    meta_results_view.heading("collection", text="Collection")
    meta_results_view.heading("type", text="Type")
    meta_results_view.heading("pdf_path", text="Chemin PDF")
    meta_results_view.column("title", width=260)
    meta_results_view.column("collection", width=140)
    meta_results_view.column("type", width=80)
    meta_results_view.column("pdf_path", width=320)

    meta_scroll = ttk.Scrollbar(meta_tab, orient="vertical", command=meta_results_view.yview)
    meta_results_view.configure(yscrollcommand=meta_scroll.set)

    def _update_meta_progress(event: dict) -> None:
        stage = event.get("stage")
        if stage == "start":
            total = int(event.get("total") or 0)
            meta_progress["maximum"] = max(total, 1)
            meta_progress["value"] = 0
            meta_running["active"] = True
            _start_meta_activity()
            _set_meta_status("Analyse des PDFs...")
            return
        if stage == "item":
            done = int(event.get("done") or 0)
            total = int(event.get("total") or 0)
            meta_progress["maximum"] = max(total, 1)
            meta_progress["value"] = done
            path = event.get("path")
            _set_meta_status(f"Scan {done}/{total} {path}")
            return
        if stage == "done":
            _stop_meta_activity()
            total = int(event.get("total") or 0)
            matches = int(event.get("matches") or 0)
            _set_meta_status(f"Termine. {matches}/{total} PDFs contiennent le mot-cle.")

    def _render_meta_results(paths: list[Path]) -> None:
        for item in meta_results_view.get_children():
            meta_results_view.delete(item)
        meta_results_paths.clear()
        master_df = load_master_frame()
        for pdf_path in paths:
            meta_results_paths.append(pdf_path)
            match = None
            if "pdf_path" in master_df.columns:
                mask = (
                    master_df["pdf_path"].fillna("").astype(str) == str(pdf_path)
                )
                if mask.any():
                    match = master_df[mask].iloc[0]
            if match is not None:
                title = str(match.get("title", "") or pdf_path.stem)
                collection = str(match.get("collection", ""))
                doc_type = str(match.get("type", ""))
            else:
                title = pdf_path.stem
                collection = ""
                doc_type = ""
            meta_results_view.insert(
                "", "end", values=(title, collection, doc_type, str(pdf_path))
            )

    def run_meta_search() -> None:
        if meta_running["active"]:
            _set_meta_status("Une recherche est deja en cours.")
            return
        keyword = meta_keyword_var.get().strip()
        if not keyword:
            _set_meta_status("Mot-cle manquant.")
            return
        try:
            max_pages = int(meta_pages_var.get().strip() or "2")
        except ValueError:
            _set_meta_status("Pages invalides.")
            return

        def _cb(event: dict) -> None:
            root.after(0, lambda: _update_meta_progress(event))

        def _worker() -> None:
            matches, errors = search_pdfs_by_keyword(
                keyword, max_pages=max_pages, progress_cb=_cb
            )
            root.after(0, lambda: _render_meta_results(matches))
            if errors:
                root.after(
                    0,
                    lambda: _set_meta_status(
                        f"Termine avec erreurs ({len(errors)})."
                    ),
                )

        meta_running["active"] = True
        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def open_meta_selected() -> None:
        selected = meta_results_view.selection()
        if not selected:
            _set_meta_status("Aucun resultat selectionne.")
            return
        values = meta_results_view.item(selected[0], "values")
        if not values or len(values) < 4:
            _set_meta_status("Chemin PDF manquant.")
            return
        path = Path(values[3]).expanduser()
        if not path.exists():
            _set_meta_status("PDF introuvable.")
            return
        if _open_path(path):
            _set_meta_status(f"Ouverture: {path}")
        else:
            _set_meta_status("Impossible d ouvrir le PDF.")

    def create_group() -> None:
        if not meta_results_paths:
            _set_meta_status("Aucun resultat a grouper.")
            return
        keyword = meta_keyword_var.get().strip()
        slug = _slugify(keyword)
        groups_dir = ensure_dir(bibliotheque_root() / "groups")
        tag = datetime.now().strftime("%Y%m%d_%H%M")
        output = groups_dir / f"group_{slug}_{tag}.csv"
        master_df = load_master_frame()
        rows = []
        for pdf_path in meta_results_paths:
            row = {
                "title": pdf_path.stem,
                "authors": "",
                "year": "",
                "type": "",
                "isbn": "",
                "collection": "",
                "keywords": "",
                "pdf_path": str(pdf_path),
            }
            if "pdf_path" in master_df.columns:
                mask = (
                    master_df["pdf_path"].fillna("").astype(str) == str(pdf_path)
                )
                if mask.any():
                    record = master_df[mask].iloc[0]
                    for key in row.keys():
                        if key in record:
                            row[key] = str(record.get(key, "") or row[key])
            rows.append(row)
        pd.DataFrame(rows).to_csv(output, index=False)
        _set_meta_status(f"Groupe cree: {output}")

    meta_controls = ttk.Frame(meta_tab)
    meta_controls.pack(fill="x", pady=(0, 8))
    ttk.Label(meta_controls, text="Mot-cle").pack(side="left")
    ttk.Entry(meta_controls, textvariable=meta_keyword_var).pack(
        side="left", fill="x", expand=True, padx=(6, 6)
    )
    ttk.Label(meta_controls, text="Pages").pack(side="left")
    ttk.Entry(meta_controls, textvariable=meta_pages_var, width=5).pack(
        side="left", padx=(6, 6)
    )
    ttk.Button(meta_controls, text="Rechercher", command=run_meta_search).pack(
        side="left"
    )
    ttk.Button(meta_controls, text="Creer groupe", command=create_group).pack(
        side="left", padx=(6, 0)
    )
    ttk.Button(meta_controls, text="Ouvrir PDF", command=open_meta_selected).pack(
        side="left", padx=(6, 0)
    )

    meta_progress_row = ttk.Frame(meta_tab)
    meta_progress_row.pack(fill="x", pady=(0, 8))
    ttk.Label(meta_progress_row, text="Progression").pack(side="left")
    meta_progress.pack(side="left", padx=(6, 6))
    ttk.Label(meta_progress_row, textvariable=meta_activity_var).pack(side="left")

    ttk.Label(meta_tab, textvariable=meta_status_var).pack(anchor="w", pady=(0, 6))

    meta_results_view.pack(side="left", fill="both", expand=True)
    meta_scroll.pack(side="left", fill="y")

    # --- Onglet Dashboard ---
    dashboard_tab = ttk.Frame(notebook, padding=12)
    notebook.add(dashboard_tab, text="Dashboard")

    zotero_items_var = tk.StringVar(value="0")
    zotero_pdfs_var = tk.StringVar(value="0")
    local_pdfs_var = tk.StringVar(value="0")
    references_var = tk.StringVar(value="0")
    indexed_count_var = tk.StringVar(value="0")
    books_count_var = tk.StringVar(value="0")
    unknown_count_var = tk.StringVar(value="0")
    missing_count_var = tk.StringVar(value="0")
    queue_count_var = tk.StringVar(value="0")
    progress_var = tk.StringVar(value="0%")

    progress_bar = ttk.Progressbar(dashboard_tab, length=260, maximum=100)

    def update_progress_from_state(state: dict) -> None:
        progress = compute_progress(state)
        percent = progress.get("percent", 0.0)
        progress_var.set(f"{percent:.0f}%")
        progress_bar["value"] = percent

    def refresh_counts() -> None:
        zotero = zotero_counts(Path.home() / "Zotero")
        zotero_items_var.set(str(zotero.get("items", 0)))
        zotero_pdfs_var.set(str(zotero.get("pdfs", 0)))
        if zotero.get("error"):
            set_status(f"Zotero: {zotero['error']}")
        local_pdfs_var.set(str(count_pdfs()))
        references_var.set(str(count_references()))
        indexed_count_var.set(str(count_indexed_articles()))
        books_count_var.set(str(count_indexed_books()))
        unknown_count_var.set(str(count_indexed_unknown()))
        missing_count_var.set(str(count_missing_pdfs()))
        queue_count_var.set(str(count_to_be_downloaded()))
        last_refresh_var.set(datetime.now().strftime("Mis a jour: %H:%M:%S"))
        runs = load_scan_runs(limit=2)
        summary_lines: list[str] = []
        error_lines: list[str] = []
        for run in runs:
            ts = run.get("timestamp", "")
            total = run.get("total_pdfs", 0)
            processed = run.get("processed_pdfs", 0)
            created = run.get("created", 0)
            updated = run.get("updated", 0)
            errors = run.get("errors", 0)
            warnings = run.get("warnings", 0)
            percent = int((processed / total) * 100) if total else 0
            summary_lines.append(
                f"{ts} | {processed}/{total} ({percent}%) | +{created} / ~{updated} | err {errors} warn {warnings}"
            )
            counts = {}
            counts.update(run.get("error_counts", {}) or {})
            counts.update(run.get("warning_counts", {}) or {})
            top = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:3]
            if top:
                errors_fmt = ", ".join(f"{name}:{value}" for name, value in top)
                error_lines.append(f"{ts} | {errors_fmt}")
        scan_summary_var.set("\\n".join(summary_lines) if summary_lines else "Aucun scan disponible.")
        scan_errors_var.set("\\n".join(error_lines) if error_lines else "-")

    dash_title_font = ("Avenir Next", 12, "bold")
    dash_value_font = ("Avenir Next", 22, "bold")
    dash_meta_font = ("Avenir Next", 10)

    last_refresh_var = tk.StringVar(value="")
    scan_summary_var = tk.StringVar(value="")
    scan_errors_var = tk.StringVar(value="")

    header = tk.Frame(dashboard_tab)
    header.pack(fill="x", pady=(0, 8))
    tk.Label(header, text="Dashboard", font=dash_title_font).pack(side="left")
    tk.Label(header, textvariable=last_refresh_var, font=dash_meta_font).pack(
        side="right"
    )

    stats_grid = tk.Frame(dashboard_tab)
    stats_grid.pack(fill="both", expand=True)
    for col in range(3):
        stats_grid.columnconfigure(col, weight=1, uniform="card")

    def _card(parent: tk.Widget, title: str, var: tk.StringVar, color: str) -> tk.Frame:
        frame = tk.Frame(parent, bg=color, padx=12, pady=10)
        tk.Label(
            frame,
            text=title,
            bg=color,
            fg="white",
            font=dash_meta_font,
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            frame,
            textvariable=var,
            bg=color,
            fg="white",
            font=dash_value_font,
            anchor="w",
        ).pack(fill="x")
        return frame

    cards = [
        ("PDFs locaux", local_pdfs_var, "#2563EB"),
        ("References bibliographiques", references_var, "#16A34A"),
        ("A telecharger (master)", missing_count_var, "#F59E0B"),
        ("Articles indexes (PDF)", indexed_count_var, "#0EA5E9"),
        ("Livres indexes (PDF)", books_count_var, "#22C55E"),
        ("Inconnu (PDF)", unknown_count_var, "#64748B"),
        ("Zotero items", zotero_items_var, "#06B6D4"),
        ("Zotero PDFs", zotero_pdfs_var, "#14B8A6"),
        ("Queue actuelle", queue_count_var, "#F97316"),
    ]

    for index, (title, var, color) in enumerate(cards):
        row, col = divmod(index, 3)
        card = _card(stats_grid, title, var, color)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

    progress_wrap = tk.Frame(dashboard_tab)
    progress_wrap.pack(fill="x", pady=(6, 8))
    tk.Label(progress_wrap, text="Progression projet", font=dash_meta_font).pack(
        side="left"
    )
    progress_bar.pack(side="left", padx=(8, 6))
    tk.Label(progress_wrap, textvariable=progress_var, font=dash_meta_font).pack(
        side="left"
    )

    scans_frame = tk.Frame(dashboard_tab)
    scans_frame.pack(fill="x", pady=(4, 6))
    tk.Label(scans_frame, text="Derniers scans", font=dash_meta_font).pack(anchor="w")
    tk.Label(
        scans_frame,
        textvariable=scan_summary_var,
        font=dash_meta_font,
        justify="left",
        anchor="w",
    ).pack(fill="x")
    tk.Label(scans_frame, text="Top erreurs", font=dash_meta_font).pack(
        anchor="w", pady=(4, 0)
    )
    tk.Label(
        scans_frame,
        textvariable=scan_errors_var,
        font=dash_meta_font,
        justify="left",
        anchor="w",
    ).pack(fill="x")

    scan_running = {"active": False}

    def scan_library_action() -> None:
        if scan_running["active"]:
            set_status("Analyse deja en cours...")
            return
        scan_running["active"] = True
        set_status("Analyse des PDFs en cours...")

        def _progress(info: dict) -> None:
            if info.get("stage") == "item":
                done = info.get("done", 0)
                total = info.get("total", 0)
                percent = int((done / total) * 100) if total else 0
                scan_summary_var.set(f"En cours: {done}/{total} ({percent}%)")
                set_status(f"Scan en cours: {done}/{total}")

        def _worker() -> None:
            result = run_scan_library(progress_cb=_progress, export_catalogs_flag=True, export_bib_flag=False)

            def _finish() -> None:
                scan_running["active"] = False
                refresh_counts()
                errors = result.get("errors", 0)
                created = result.get("created", 0)
                updated = result.get("updated", 0)
                total = result.get("total_pdfs", 0)
                set_status(
                    f"Scan termine: {total} PDFs, +{created} / ~{updated}, err {errors}."
                )

            root.after(0, _finish)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    actions = ttk.Frame(dashboard_tab)
    actions.pack(fill="x", pady=(6, 0))
    ttk.Button(actions, text="Rafraichir", command=refresh_counts).pack(
        side="left"
    )
    ttk.Button(actions, text="Analyser PDFs", command=scan_library_action).pack(
        side="left", padx=(8, 0)
    )

    

    # --- Onglet Ecosysteme ---
    eco_tab = ttk.Frame(notebook, padding=12)
    notebook.add(eco_tab, text="Ecosysteme")

    eco_status_var = tk.StringVar(value="")
    eco_selected_id: dict[str, str | None] = {"value": None}
    eco_nodes: dict[str, dict] = {}
    eco_item_to_node: dict[str, str] = {}
    eco_observer: dict[str, object | None] = {"value": None}
    deps_auto_stop: dict[str, object | None] = {"value": None}

    code_root = Path(__file__).resolve().parents[2]
    repo_root = code_root.parent
    requirements_path = repo_root / "requirements.txt"

    def eco_log(message: str) -> None:
        eco_status_var.set(message)

    def _node_info(node: dict) -> str:
        completion = int(node.get("completion", 0))
        outputs = node.get("outputs", "")
        if node.get("type") == "module":
            main = ", ".join(node.get("main_functions", []))
            return f"{outputs} | Fonctions: {main} | {completion}%"
        if node.get("type") == "function":
            module = node.get("module", "")
            return f"{outputs} | {module} | {completion}%"
        return f"{outputs} | {completion}%"

    eco_history: list[str] = []
    org_canvas_items: dict[int, str] = {}

    def _push_history(node_id: str) -> None:
        current = eco_selected_id.get("value")
        if current and current != node_id:
            eco_history.append(current)

    def go_back() -> None:
        if not eco_history:
            eco_log("Historique vide.")
            return
        previous = eco_history.pop()
        _select_node_by_id(previous)

    def _select_node_by_id(node_id: str) -> None:
        item = None
        for key, value in eco_item_to_node.items():
            if value == node_id:
                item = key
                break
        if item:
            eco_tree.selection_set(item)
            eco_tree.see(item)
        _show_details(node_id)

    def _build_schema_text(index: dict) -> str:
        root = repo_root / "motherload_projet"
        exclude = {".git", ".venv", "__pycache__", ".DS_Store"}

        lines = [root.name]

        def _walk(path: Path, prefix: str, depth: int, max_depth: int) -> None:
            if depth > max_depth:
                return
            entries = []
            try:
                entries = list(path.iterdir())
            except OSError:
                return
            filtered = [
                entry
                for entry in entries
                if entry.name not in exclude and not entry.name.startswith(".DS_")
            ]
            filtered.sort(key=lambda p: (not p.is_dir(), p.name.lower()))
            for idx, entry in enumerate(filtered):
                is_last = idx == len(filtered) - 1
                connector = "└─" if is_last else "├─"
                suffix = "/" if entry.is_dir() else ""
                lines.append(f"{prefix}{connector} {entry.name}{suffix}")
                if entry.is_dir():
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    _walk(entry, new_prefix, depth + 1, max_depth)

        _walk(root, "", 1, 3)
        return "\n".join(lines)

    def _render_schema_text(index: dict) -> None:
        text = _build_schema_text(index)
        schema_text.configure(state="normal")
        schema_text.delete("1.0", "end")
        schema_text.insert("1.0", text)
        schema_text.configure(state="disabled")

    def _render_org_chart(index: dict) -> None:
        org_canvas.delete("all")
        org_canvas_items.clear()
        nodes = index.get("nodes", [])
        modules = [n for n in nodes if n.get("type") == "module"]
        funcs = [n for n in nodes if n.get("type") == "function"]
        func_map: dict[str, list[dict]] = {}
        for fn in funcs:
            func_map.setdefault(fn.get("module", ""), []).append(fn)
        modules = sorted(modules, key=lambda item: item.get("name", ""))
        root_box = (20, 40, 200, 90)
        org_canvas.create_rectangle(*root_box, fill="#f2b134", outline="")
        org_canvas.create_text(110, 65, text="motherload_projet", fill="white")

        x_mod = 260
        x_func = 540
        y = 40
        box_h = 40
        gap = 20
        for mod in modules:
            mod_id = mod.get("id", "")
            y0 = y
            y1 = y + box_h
            org_canvas.create_line(root_box[2], 65, x_mod, y0 + box_h / 2, fill="#4a90e2", width=2)
            rect = org_canvas.create_rectangle(x_mod, y0, x_mod + 220, y1, fill="#4a90e2", outline="")
            text_id = org_canvas.create_text(x_mod + 110, y0 + 20, text=mod.get("name", ""), fill="white")
            org_canvas_items[rect] = mod_id
            org_canvas_items[text_id] = mod_id

            main = mod.get("main_functions") or []
            children = func_map.get(mod.get("name", ""), [])
            if main:
                children = [c for c in children if c.get("name") in main]
            if not children:
                children = func_map.get(mod.get("name", ""), [])[:3]
            child_y = y0
            for child in children:
                func_id = child.get("id", "")
                org_canvas.create_line(x_mod + 220, y0 + box_h / 2, x_func, child_y + box_h / 2, fill="#6fb14a", width=2)
                rect = org_canvas.create_rectangle(x_func, child_y, x_func + 240, child_y + box_h, fill="#6fb14a", outline="")
                text_id = org_canvas.create_text(x_func + 120, child_y + 20, text=child.get("name", ""), fill="white")
                org_canvas_items[rect] = func_id
                org_canvas_items[text_id] = func_id
                child_y += box_h + 10

            y = max(child_y, y + box_h + gap)

        org_canvas.configure(scrollregion=org_canvas.bbox("all"))

    def _build_tree(index: dict) -> None:
        eco_tree.delete(*eco_tree.get_children())
        eco_nodes.clear()
        eco_item_to_node.clear()
        nodes = index.get("nodes", [])
        type_order = {"package": 0, "module": 1, "function": 2}
        nodes = sorted(
            nodes,
            key=lambda item: (type_order.get(item.get("type", ""), 9), item.get("name", "")),
        )
        item_map: dict[str, str] = {}
        for node in nodes:
            node_id = str(node.get("id"))
            parent_id = node.get("parent")
            parent_item = item_map.get(parent_id, "")
            label = node.get("name", node_id)
            info = _node_info(node)
            item = eco_tree.insert(parent_item, "end", text=label, values=(info,))
            item_map[node_id] = item
            eco_nodes[node_id] = node
            eco_item_to_node[item] = node_id
        _render_schema_text(index)
        _render_org_chart(index)

    def refresh_ecosystem() -> None:
        eco_log("Mise a jour de l ecosysteme...")
        index = rebuild_index(code_root)
        _build_tree(index)
        eco_log(f"Index mis a jour: {index_path()}")

    def load_or_build_index() -> None:
        index = load_index()
        if not index:
            index = rebuild_index(code_root)
        _build_tree(index)
        eco_log("Ecosysteme charge.")

    def _show_details(node_id: str) -> None:
        node = eco_nodes.get(node_id)
        if not node:
            return
        eco_selected_id["value"] = node_id
        detail_title_var.set(f"{node.get('name', '')} [{node.get('type', '')}]")
        detail_program_var.set(str(node.get("module", node.get("name", ""))))
        detail_summary_var.set(str(node.get("summary", "")))
        detail_outputs_var.set(str(node.get("outputs", "")))
        completion = int(node.get("completion", 0))
        detail_completion_var.set(f"{completion}%")
        detail_progress["value"] = completion
        detail_path_var.set(str(node.get("path", "")))
        notes = load_notes(node_id)
        detail_notes.delete("1.0", "end")
        detail_notes.insert("1.0", notes)
        detail_note_path_var.set(str(notes_path(node_id)))

    def _open_details_window(node_id: str) -> None:
        node = eco_nodes.get(node_id)
        if not node:
            return
        window = tk.Toplevel(root)
        window.title(f"Details {node.get('name', '')}")
        window.geometry("520x520")

        ttk.Label(window, text=node.get("name", ""), font=("Helvetica", 14, "bold")).pack(
            anchor="w", padx=12, pady=(12, 4)
        )
        ttk.Label(window, text=f"Type: {node.get('type', '')}").pack(
            anchor="w", padx=12
        )
        ttk.Label(window, text=f"Programme: {node.get('module', node.get('name', ''))}").pack(
            anchor="w", padx=12, pady=(0, 6)
        )
        ttk.Label(window, text="Description").pack(anchor="w", padx=12)
        desc = tk.Text(window, height=6, wrap="word")
        desc.insert("1.0", node.get("detail", node.get("summary", "")))
        desc.configure(state="disabled")
        desc.pack(fill="x", padx=12, pady=(0, 8))

        ttk.Label(window, text="Notes").pack(anchor="w", padx=12)
        notes_box = tk.Text(window, height=8, wrap="word")
        notes_box.insert("1.0", load_notes(node_id))
        notes_box.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        def _save_notes_window() -> None:
            save_notes(node_id, notes_box.get("1.0", "end"))
            eco_log(f"Notes sauvegardees: {notes_path(node_id)}")

        ttk.Button(window, text="Sauvegarder notes", command=_save_notes_window).pack(
            anchor="e", padx=12, pady=(0, 12)
        )

    def on_tree_select(_event: object) -> None:
        selection = eco_tree.selection()
        if not selection:
            return
        node_id = eco_item_to_node.get(selection[0])
        if node_id:
            _push_history(node_id)
            _show_details(node_id)

    def on_tree_double(_event: object) -> None:
        selection = eco_tree.selection()
        if not selection:
            return
        node_id = eco_item_to_node.get(selection[0])
        if node_id:
            _push_history(node_id)
            _open_details_window(node_id)

    def save_current_note() -> None:
        node_id = eco_selected_id.get("value")
        if not node_id:
            eco_log("Selection manquante.")
            return
        save_notes(node_id, detail_notes.get("1.0", "end"))
        eco_log(f"Notes sauvegardees: {notes_path(node_id)}")

    def start_watchdog_if_enabled() -> None:
        if not _WATCHDOG_AVAILABLE:
            eco_log("watchdog non disponible.")
            return
        if eco_observer["value"] is not None:
            return

        def _on_change() -> None:
            root.after(0, refresh_ecosystem)

        try:
            eco_observer["value"] = start_watchdog(code_root, _on_change)
            eco_log("Auto update actif.")
        except Exception as exc:
            eco_log(f"watchdog erreur: {exc}")

    def stop_watchdog() -> None:
        observer = eco_observer.get("value")
        if observer is None:
            return
        try:
            observer.stop()
            observer.join(timeout=1)
        except Exception:
            pass
        eco_observer["value"] = None

    def toggle_watchdog() -> None:
        if eco_auto_var.get():
            start_watchdog_if_enabled()
        else:
            stop_watchdog()
            eco_log("Auto update desactive.")

    def check_deps() -> None:
        outdated = list_outdated()
        if not outdated:
            eco_log("Aucune dependance obsolete.")
            return
        lines = [
            f"{item.get('name')} {item.get('version')} -> {item.get('latest_version')}"
            for item in outdated
        ]
        eco_log("Deps obsoletes: " + "; ".join(lines[:4]))

    def run_deps_update() -> None:
        def _worker() -> None:
            code, output = upgrade_requirements(requirements_path)
            status = "OK" if code == 0 else "ERROR"
            root.after(0, lambda: eco_log(f"Update deps -> {status}"))
            if output:
                root.after(0, lambda: eco_log(output[:240]))

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def toggle_deps_auto() -> None:
        interval_text = deps_interval_var.get().strip()
        try:
            interval = int(interval_text)
        except ValueError:
            interval = 0
        if deps_auto_var.get() and interval > 0:
            if deps_auto_stop["value"] is not None:
                deps_auto_stop["value"].set()
            deps_auto_stop["value"] = start_auto_update(
                requirements_path, interval, on_log=eco_log
            )
            eco_log(f"Auto update deps toutes les {interval} min.")
        else:
            if deps_auto_stop["value"] is not None:
                deps_auto_stop["value"].set()
                deps_auto_stop["value"] = None
            eco_log("Auto update deps desactive.")

    controls_row = ttk.Frame(eco_tab)
    controls_row.pack(fill="x", pady=(0, 8))
    ttk.Button(controls_row, text="Rafraichir", command=refresh_ecosystem).pack(
        side="left"
    )
    eco_auto_var = tk.BooleanVar(value=_WATCHDOG_AVAILABLE)
    ttk.Checkbutton(
        controls_row,
        text="Auto update code",
        variable=eco_auto_var,
        command=toggle_watchdog,
    ).pack(side="left", padx=(8, 0))
    ttk.Button(controls_row, text="Verifier deps", command=check_deps).pack(
        side="left", padx=(12, 0)
    )
    ttk.Button(controls_row, text="Update deps", command=run_deps_update).pack(
        side="left", padx=(6, 0)
    )
    deps_interval_var = tk.StringVar(value="120")
    deps_auto_var = tk.BooleanVar(value=False)
    ttk.Label(controls_row, text="Auto deps (min)").pack(side="left", padx=(12, 2))
    ttk.Entry(controls_row, textvariable=deps_interval_var, width=6).pack(side="left")
    ttk.Checkbutton(
        controls_row,
        text="Activer",
        variable=deps_auto_var,
        command=toggle_deps_auto,
    ).pack(side="left", padx=(4, 0))

    eco_body = ttk.Frame(eco_tab)
    eco_body.pack(fill="both", expand=True)
    eco_body.columnconfigure(0, weight=4)
    eco_body.columnconfigure(1, weight=3)
    eco_body.rowconfigure(0, weight=1)

    eco_tree = ttk.Treeview(eco_body, columns=("info",), show="tree headings", height=22)
    eco_tree.heading("#0", text="Element")
    eco_tree.heading("info", text="Info")
    eco_tree.column("#0", width=260)
    eco_tree.column("info", width=380)

    eco_scroll = ttk.Scrollbar(eco_body, orient="vertical", command=eco_tree.yview)
    eco_tree.configure(yscrollcommand=eco_scroll.set)
    eco_tree.grid(row=0, column=0, sticky="nsew")
    eco_scroll.grid(row=0, column=0, sticky="nse")

    right_pane = ttk.Frame(eco_body)
    right_pane.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
    right_pane.rowconfigure(0, weight=3)
    right_pane.rowconfigure(1, weight=2)
    right_pane.columnconfigure(0, weight=1)

    view_tabs = ttk.Notebook(right_pane)
    view_tabs.grid(row=0, column=0, sticky="nsew")

    schema_tab = ttk.Frame(view_tabs)
    org_tab = ttk.Frame(view_tabs)
    view_tabs.add(schema_tab, text="Schema simple")
    view_tabs.add(org_tab, text="Organigramme")

    schema_text = tk.Text(schema_tab, wrap="none", height=12)
    schema_text.configure(state="disabled")
    schema_scroll = ttk.Scrollbar(schema_tab, orient="vertical", command=schema_text.yview)
    schema_text.configure(yscrollcommand=schema_scroll.set)
    schema_text.pack(side="left", fill="both", expand=True)
    schema_scroll.pack(side="left", fill="y")

    org_canvas = tk.Canvas(org_tab, background="white", height=320)
    org_hscroll = ttk.Scrollbar(org_tab, orient="horizontal", command=org_canvas.xview)
    org_vscroll = ttk.Scrollbar(org_tab, orient="vertical", command=org_canvas.yview)
    org_canvas.configure(xscrollcommand=org_hscroll.set, yscrollcommand=org_vscroll.set)
    org_canvas.pack(side="left", fill="both", expand=True)
    org_vscroll.pack(side="left", fill="y")
    org_hscroll.pack(side="bottom", fill="x")

    def _on_canvas_click(event: tk.Event) -> None:
        item = org_canvas.find_closest(event.x, event.y)
        if not item:
            return
        node_id = org_canvas_items.get(item[0])
        if node_id:
            _push_history(node_id)
            _select_node_by_id(node_id)

    org_canvas.bind("<Button-1>", _on_canvas_click)

    detail_frame = ttk.Frame(right_pane)
    detail_frame.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
    detail_frame.columnconfigure(0, weight=1)

    detail_title_var = tk.StringVar(value="")
    detail_program_var = tk.StringVar(value="")
    detail_summary_var = tk.StringVar(value="")
    detail_outputs_var = tk.StringVar(value="")
    detail_completion_var = tk.StringVar(value="0%")
    detail_path_var = tk.StringVar(value="")
    detail_note_path_var = tk.StringVar(value="")

    detail_header = ttk.Frame(detail_frame)
    detail_header.grid(row=0, column=0, sticky="ew")
    detail_header.columnconfigure(0, weight=1)
    ttk.Label(detail_header, textvariable=detail_title_var, font=("Helvetica", 12, "bold")).grid(
        row=0, column=0, sticky="w"
    )
    ttk.Button(detail_header, text="Retour", command=go_back).grid(row=0, column=1, sticky="e")
    ttk.Label(detail_frame, textvariable=detail_program_var).grid(
        row=1, column=0, sticky="w"
    )
    ttk.Label(detail_frame, textvariable=detail_path_var, wraplength=280).grid(
        row=2, column=0, sticky="w"
    )
    ttk.Label(detail_frame, text="Resume").grid(row=3, column=0, sticky="w", pady=(6, 0))
    ttk.Label(detail_frame, textvariable=detail_summary_var, wraplength=280).grid(
        row=4, column=0, sticky="w"
    )
    ttk.Label(detail_frame, text="Sorties").grid(row=5, column=0, sticky="w", pady=(6, 0))
    ttk.Label(detail_frame, textvariable=detail_outputs_var, wraplength=280).grid(
        row=6, column=0, sticky="w"
    )

    detail_progress = ttk.Progressbar(detail_frame, length=200, maximum=100)
    detail_progress.grid(row=7, column=0, sticky="w", pady=(6, 0))
    ttk.Label(detail_frame, textvariable=detail_completion_var).grid(row=7, column=0, sticky="e")

    ttk.Label(detail_frame, text="Notes").grid(row=8, column=0, sticky="w", pady=(6, 0))
    detail_notes = tk.Text(detail_frame, height=8, wrap="word")
    detail_notes.grid(row=9, column=0, sticky="nsew")

    ttk.Button(detail_frame, text="Sauvegarder", command=save_current_note).grid(
        row=10, column=0, sticky="e", pady=(6, 0)
    )
    ttk.Label(detail_frame, textvariable=detail_note_path_var, wraplength=280).grid(
        row=11, column=0, sticky="w", pady=(4, 0)
    )

    ttk.Label(eco_tab, textvariable=eco_status_var).pack(anchor="w", pady=(6, 0))

    eco_tree.bind("<<TreeviewSelect>>", on_tree_select)
    eco_tree.bind("<Double-1>", on_tree_double)

    load_or_build_index()
    if _WATCHDOG_AVAILABLE:
        start_watchdog_if_enabled()
    # --- Onglet Checklist ---
    checklist_tab = ttk.Frame(notebook, padding=12)
    notebook.add(checklist_tab, text="Checklist")

    state = load_state()

    checklist_canvas = tk.Canvas(checklist_tab, highlightthickness=0)
    checklist_scroll = ttk.Scrollbar(
        checklist_tab, orient="vertical", command=checklist_canvas.yview
    )
    checklist_frame = ttk.Frame(checklist_canvas)

    checklist_frame.bind(
        "<Configure>",
        lambda _event: checklist_canvas.configure(scrollregion=checklist_canvas.bbox("all")),
    )
    checklist_canvas.create_window((0, 0), window=checklist_frame, anchor="nw")
    checklist_canvas.configure(yscrollcommand=checklist_scroll.set)

    checklist_canvas.pack(side="left", fill="both", expand=True)
    checklist_scroll.pack(side="left", fill="y")

    def render_checklist() -> None:
        for child in checklist_frame.winfo_children():
            child.destroy()

        phases = state.get("phases", [])
        tasks = state.get("tasks", [])
        tasks_by_phase: dict[str, list[dict]] = {}
        for task in tasks:
            tasks_by_phase.setdefault(task.get("phase", ""), []).append(task)

        for phase in phases:
            phase_id = phase.get("id", "")
            phase_label = phase.get("label", phase_id)
            ttk.Label(checklist_frame, text=phase_label).pack(anchor="w", pady=(6, 0))
            phase_tasks = tasks_by_phase.get(phase_id, [])
            phase_tasks = sorted(phase_tasks, key=lambda item: (item.get("priority", 9), item.get("label", "")))
            for task in phase_tasks:
                var = tk.BooleanVar(value=bool(task.get("done")))

                def _toggle(task_id: str, value: tk.BooleanVar) -> None:
                    for entry in state.get("tasks", []):
                        if entry.get("id") == task_id:
                            entry["done"] = bool(value.get())
                            break
                    save_state(state)
                    update_progress_from_state(state)

                text = f"[P{task.get('priority', 3)}] {task.get('label', '')}"
                chk = ttk.Checkbutton(
                    checklist_frame,
                    text=text,
                    variable=var,
                    command=lambda tid=task.get("id", ""), v=var: _toggle(tid, v),
                )
                chk.pack(anchor="w")

        update_progress_from_state(state)

    def reset_checklist() -> None:
        nonlocal state
        state = reset_tasks()
        render_checklist()
        set_status("Checklist reinitialisee.")

    ttk.Button(checklist_tab, text="Reinitialiser", command=reset_checklist).pack(
        anchor="w", pady=(0, 8)
    )
    render_checklist()

    # --- Status ---
    ttk.Label(root, textvariable=status_var).pack(anchor="w", padx=12, pady=(4, 8))

    refresh_counts()
    update_progress_from_state(state)

    refresh_interval_ms = 30000

    def _auto_refresh() -> None:
        refresh_counts()
        root.after(refresh_interval_ms, _auto_refresh)

    root.after(refresh_interval_ms, _auto_refresh)

    def _on_close() -> None:
        if deps_auto_stop.get("value") is not None:
            deps_auto_stop["value"].set()
        stop_watchdog()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()


if __name__ == "__main__":
    try:
        run_app()
    except Exception as exc:
        print(f"Erreur UI: {exc}")
