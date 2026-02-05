#!/usr/bin/env python3
"""
Test manuel du crawler avec un lien PDF direct.
Cela permet de vérifier que le téléchargement fonctionne, indépendamment du parsing HTML.
"""

from pathlib import Path
from motherload_projet.data_mining.fetcher import fetch_url
from motherload_projet.data_mining.pdf_validate import validate_pdf_bytes

def test_direct_pdf_download():
    """Test le téléchargement d'un PDF direct."""
    
    # URL d'un PDF public connu (exemple: un article arXiv)
    pdf_url = "https://arxiv.org/pdf/2301.00001.pdf"
    
    print(f"Testing direct PDF download...")
    print(f"URL: {pdf_url}")
    print("-" * 60)
    
    ok, status, ctype, final_url, content, error = fetch_url(pdf_url)
    
    print(f"Status: {status}")
    print(f"Content-Type: {ctype}")
    print(f"Size: {len(content)} bytes")
    print(f"OK: {ok}")
    
    if ok:
        # Vérifier si c'est un vrai PDF
        is_valid, code = validate_pdf_bytes(content, min_size_kb=10)
        print(f"PDF Valid: {is_valid} (code: {code})")
        
        if is_valid:
            # Sauvegarder
            output = Path("test_direct_download.pdf")
            output.write_bytes(content)
            print(f"\n✓ PDF téléchargé avec succès: {output}")
            print(f"  Taille: {len(content) / 1024:.1f} KB")
            return True
        else:
            print(f"\n✗ Contenu invalide: {code}")
            # Sauvegarder quand même pour debug
            Path("test_direct_download_invalid.bin").write_bytes(content[:1000])
            return False
    else:
        print(f"\n✗ Échec téléchargement: {error}")
        return False

if __name__ == "__main__":
    success = test_direct_pdf_download()
    exit(0 if success else 1)
