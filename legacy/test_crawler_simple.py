#!/usr/bin/env python3
"""
Test simplifié du crawler avec une source fiable (bioRxiv).
"""

from pathlib import Path
from motherload_projet.data_mining.crawler import crawl_and_download

def test_crawler_biorxiv():
    """Test le crawler sur bioRxiv qui a des liens PDF directs."""
    
    # bioRxiv a une structure HTML simple avec des liens .pdf directs
    test_url = "https://www.biorxiv.org/content/early/recent"
    output_dir = Path("./test_crawler_biorxiv")
    
    print(f"Testing crawler on: {test_url}")
    print(f"Output directory: {output_dir}")
    print("-" * 60)
    
    # Nettoyer le dossier s'il existe
    if output_dir.exists():
        for f in output_dir.glob("*.pdf"):
            f.unlink()
    
    # Lancer le crawler
    crawl_and_download(test_url, output_dir, max_depth=0)
    
    # Compter les résultats
    pdfs = list(output_dir.glob("*.pdf"))
    
    print("-" * 60)
    print(f"RÉSULTAT: {len(pdfs)} PDFs téléchargés")
    
    if pdfs:
        print("\nPDFs téléchargés:")
        for pdf in pdfs[:5]:  # Montrer les 5 premiers
            size_kb = pdf.stat().st_size / 1024
            print(f"  - {pdf.name} ({size_kb:.1f} KB)")
        if len(pdfs) > 5:
            print(f"  ... et {len(pdfs) - 5} autres")
    
    return len(pdfs)

if __name__ == "__main__":
    count = test_crawler_biorxiv()
    
    if count >= 5:
        print(f"\n✓ TEST PASSED: {count} PDFs téléchargés (objectif: ≥5)")
        exit(0)
    else:
        print(f"\n✗ TEST FAILED: Seulement {count} PDFs (objectif: ≥5)")
        exit(1)
