"""Module d'analyse avancee de PDF (DOI, Biblio)."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

# Regex DOI robuste (prend en compte differents formats)
DOI_REGEX = re.compile(r'\b(10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+)\b')
BIB_HEADERS = [
    "references",
    "bibliography",
    "works cited",
    "bibliographie",
    "références",
]


def _clean_text(text: str) -> str:
    """Nettoie le texte pour l'analyse."""
    return re.sub(r'\s+', ' ', text).strip()


def extract_doi_advanced(pdf_path: Path) -> str | None:
    """
    Essaie d'extraire un DOI meme dans des PDFs sales.
    Stratégie:
    1. Scan texte complet pages 1 et 2.
    2. Cherche pattern 'doi: ...' ou 'https://doi.org/...' prioritaires.
    3. Fallback sur regex brute.
    """
    if PdfReader is None:
        return None

    try:
        reader = PdfReader(pdf_path)
        text_content = ""
        # On regarde les 3 premieres pages max pour le DOI
        for i in range(min(3, len(reader.pages))):
            extracted = reader.pages[i].extract_text()
            if extracted:
                text_content += " " + extracted
        
        # 1. Recherche explicite
        match_explicit = re.search(r'doi\.org/(10\.\d{4,}/[\S]+)', text_content, re.IGNORECASE)
        if match_explicit:
            return _clean_doi(match_explicit.group(1))
            
        match_explicit_2 = re.search(r'doi:?\s?(10\.\d{4,}/[\S]+)', text_content, re.IGNORECASE)
        if match_explicit_2:
            return _clean_doi(match_explicit_2.group(1))

        # 2. Recherche brute
        matches = DOI_REGEX.findall(text_content)
        if matches:
            # On prend le premier qui ressemble valider
            for match in matches:
                cleaned = _clean_doi(match)
                if cleaned:
                    return cleaned
                    
        return None
        
    except Exception as e:
        print(f"Erreur extract_doi {pdf_path.name}: {e}")
        return None


def _clean_doi(candidate: str) -> str | None:
    """Nettoie un candidat DOI (enleve ponctuation finale)."""
    candidate = candidate.strip().rstrip(".,;)")
    # Verif basique structure
    if candidate.startswith("10.") and "/" in candidate:
        return candidate
    return None


def extract_bibliography(pdf_path: Path) -> str | None:
    """
    Extrait la section bibliographique.
    Cherche un header 'References' et prend tout ce qui suit.
    """
    if PdfReader is None:
        return None
        
    try:
        reader = PdfReader(pdf_path)
        full_text = ""
        # On lit toutes les pages
        for page in reader.pages:
            t = page.extract_text()
            if t:
                full_text += "\n" + t
                
        # On cherche la derniere occurrence d'un header biblio
        last_idx = -1
        best_header = ""
        
        lower_text = full_text.lower()
        
        for header in BIB_HEADERS:
            # On cherche header en debut de ligne ou apres saut de ligne pour eviter faux positifs
            # Simplification: on cherche juste le mot cle isole
            # On cherche la DERNIERE occurrence pour eviter les tables des matieres
            idx = lower_text.rfind(header)
            if idx > last_idx:
                # Verifions si c'est 'titre' (ligne courte ?)
                # Pour l'instant on prend brut
                last_idx = idx
                best_header = header
                
        if last_idx != -1:
            # On prend tout apres
            bib_content = full_text[last_idx:]
            # On enleve le header lui meme dans la premiere ligne si possible
            # Mais souvent c'est extraction brute
            return bib_content.strip()
            
        return None
        
    except Exception as e:
        print(f"Erreur extract_bib {pdf_path.name}: {e}")
        return None
