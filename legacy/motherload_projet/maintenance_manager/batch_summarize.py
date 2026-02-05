"""Module de résumé en batch pour des collections entières."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from motherload_projet.data_mining.pdf_validate import validate_pdf_bytes
from motherload_projet.maintenance_manager.summarize import summarize_pdf


def setup_batch_logger(log_path: Path) -> logging.Logger:
    """Configure le logger pour le batch."""
    logger = logging.getLogger("batch_summarize")
    logger.setLevel(logging.INFO)
    
    # File handler
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Format
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger


def batch_summarize_collection(
    collection_path: Path,
    force: bool = False,
    log_dir: Path | None = None,
) -> dict[str, int]:
    """
    Traite tous les PDFs d'une collection.
    
    Args:
        collection_path: Chemin vers la collection à traiter.
        force: Si True, re-génère les résumés existants.
        log_dir: Dossier pour les logs (par défaut: collection_path).
        
    Returns:
        Dict avec stats (total, success, skipped, errors).
    """
    if not collection_path.exists():
        print(f"Collection introuvable: {collection_path}")
        return {"total": 0, "success": 0, "skipped": 0, "errors": 0}
    
    # Setup logging
    if log_dir is None:
        log_dir = collection_path
    log_path = log_dir / f"summarization_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logger = setup_batch_logger(log_path)
    
    logger.info(f"Démarrage batch summarization: {collection_path}")
    logger.info(f"Force mode: {force}")
    
    stats = {
        "total": 0,
        "success": 0,
        "skipped": 0,
        "errors": 0,
        "corrupt": 0,
        "already_summarized": 0,
    }
    
    # Scan tous les PDFs
    pdf_files = list(collection_path.rglob("*.pdf"))
    stats["total"] = len(pdf_files)
    
    logger.info(f"Trouvé {stats['total']} fichiers PDF")
    
    for idx, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{idx}/{stats['total']}] {pdf_path.name}")
        logger.info(f"Traitement [{idx}/{stats['total']}]: {pdf_path}")
        
        # 1. Vérifier si déjà résumé
        md_path = pdf_path.with_suffix(".md")
        if md_path.exists() and not force:
            print(f"  ✓ Résumé existant (skip)")
            logger.info(f"  Skip: résumé existant")
            stats["skipped"] += 1
            stats["already_summarized"] += 1
            continue
        
        # 2. Valider santé du PDF
        try:
            content = pdf_path.read_bytes()
            is_valid, reason = validate_pdf_bytes(content)
            
            if not is_valid:
                print(f"  ✗ PDF corrompu ({reason})")
                logger.warning(f"  PDF corrompu: {reason}")
                stats["errors"] += 1
                stats["corrupt"] += 1
                continue
                
        except Exception as e:
            print(f"  ✗ Erreur lecture: {e}")
            logger.error(f"  Erreur lecture: {e}")
            stats["errors"] += 1
            continue
        
        # 3. Résumer
        try:
            result = summarize_pdf(pdf_path, force=force)
            if result:
                print(f"  ✓ Résumé créé")
                logger.info(f"  Succès: {result}")
                stats["success"] += 1
            else:
                print(f"  ✗ Échec résumé (voir logs)")
                logger.warning(f"  Échec résumé (aucun texte ou erreur LLM)")
                stats["errors"] += 1
                
        except Exception as e:
            print(f"  ✗ Erreur résumé: {e}")
            logger.error(f"  Erreur résumé: {e}", exc_info=True)
            stats["errors"] += 1
    
    # Rapport final
    print("\n" + "=" * 50)
    print("RAPPORT FINAL")
    print("=" * 50)
    print(f"Total traité      : {stats['total']}")
    print(f"Succès            : {stats['success']}")
    print(f"Ignorés           : {stats['skipped']}")
    print(f"  - Déjà résumés  : {stats['already_summarized']}")
    print(f"Erreurs           : {stats['errors']}")
    print(f"  - PDFs corrompus: {stats['corrupt']}")
    print(f"\nLog détaillé: {log_path}")
    
    logger.info("=" * 50)
    logger.info("RAPPORT FINAL")
    logger.info(f"Total: {stats['total']}, Succès: {stats['success']}, Ignorés: {stats['skipped']}, Erreurs: {stats['errors']}")
    logger.info("=" * 50)
    
    return stats
