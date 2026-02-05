"""Module de synthese LLM pour les articles."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None  # Gestion de l'absence de pypdf

# Essai d'import d'OpenAI, facultatif
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Essai d'import de requests pour Ollama
try:
    import requests
except ImportError:
    requests = None


def extract_text_start(pdf_path: Path, max_pages: int = 2) -> str:
    """
    Extrait le texte des premieres pages d'un PDF.
    """
    if PdfReader is None:
        return "ERREUR: pypdf non installe. `pip install pypdf`"
    
    try:
        reader = PdfReader(pdf_path)
        text = []
        count = 0
        for page in reader.pages:
            if count >= max_pages:
                break
            extracted = page.extract_text()
            if extracted:
                text.append(extracted)
            count += 1
        return "\n\n".join(text)
    except Exception as e:
        return f"ERREUR lors de l'extraction: {e}"


def _call_llm(text: str, timeout: int = 60) -> str:
    """
    Appelle le LLM pour resumer le texte.
    Ordre de priorite: OpenAI > Ollama > Mock.
    
    Args:
        text: Texte a resumer.
        timeout: Timeout en secondes pour les requetes LLM.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    ollama_endpoint = os.environ.get("OLLAMA_ENDPOINT")
    ollama_model = os.environ.get("OLLAMA_MODEL", "llama3.2")
    
    prompt = (
        "Tu es un analyste scientifique. "
        "Fais un resume structure en 5 points cles du texte suivant (qui est le debut d'un article). "
        "Concentre-toi sur l'objectif, la methode et les resultats si visibles.\n\n"
        f"{text[:4000]}"  # Tronque pour eviter overflow context
    )
    
    # 1. Option OpenAI
    if OpenAI and api_key:
        try:
            client = OpenAI(api_key=api_key, timeout=timeout)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Tu es un assistant utile et precis."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"ERREUR LLM (OpenAI): {e}"
    
    # 2. Option Ollama
    if requests and ollama_endpoint:
        try:
            response = requests.post(
                f"{ollama_endpoint}/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=timeout,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "ERREUR: reponse vide")
        except requests.exceptions.Timeout:
            return f"ERREUR LLM (Ollama): Timeout apres {timeout}s"
        except Exception as e:
            return f"ERREUR LLM (Ollama): {e}"

    # 3. Option Mock
    return (
        "# Résumé (MOCK)\n\n"
        "Ceci est un resume simule car aucun LLM n'est configure.\n\n"
        "1. **Contexte**: Le document semble traiter de sujets academiques.\n"
        "2. **Objectif**: Non determine sans lecture reelle.\n"
        "3. **Methode**: Analyse de texte simulee.\n"
        "4. **Resultats**: En attente de configuration LLM.\n"
        "5. **Conclusion**: Veuillez configurer OPENAI_API_KEY ou OLLAMA_ENDPOINT.\n"
    )


def summarize_pdf(pdf_path: Path, force: bool = False) -> Path | None:
    """
    Genere un resume .md a cote du PDF.
    
    Returns:
        Chemin du fichier resume cree, ou None si echec/existe deja.
    """
    if not pdf_path.exists():
        print(f"Fichier non trouve: {pdf_path}")
        return None
        
    md_path = pdf_path.with_suffix(".md")
    if md_path.exists() and not force:
        print(f"Resume existant (skip): {md_path.name}")
        return None
        
    print(f"Lecture: {pdf_path.name}")
    text = extract_text_start(pdf_path)
    
    if text.startswith("ERREUR"):
        print(f" -> {text}")
        return None
        
    if not text.strip():
        print(" -> Aucun texte extrait (PDF image ou vide?)")
        return None
        
    print(" -> Generation du resume...")
    summary = _call_llm(text)
    
    header = f"# Résumé : {pdf_path.name}\n\n*Généré par Motherload Analyst*\n\n"
    md_path.write_text(header + summary, encoding="utf-8")
    print(f" -> Cree: {md_path.name}")
    
    return md_path


def summarize_selected(pdf_path: Path | str) -> dict[str, str | None]:
    """
    Fonction hook pour l'interface UI.
    Genere un resume pour un PDF selectionne.
    
    Args:
        pdf_path: Chemin vers le PDF a resumer.
        
    Returns:
        Dict avec 'status' ('success'/'error'), 'md_path', 'error'.
    """
    if isinstance(pdf_path, str):
        pdf_path = Path(pdf_path)
        
    try:
        result = summarize_pdf(pdf_path, force=False)
        if result:
            return {
                "status": "success",
                "md_path": str(result),
                "error": None,
            }
        else:
            return {
                "status": "error",
                "md_path": None,
                "error": "Impossible de generer le resume (voir console)",
            }
    except Exception as e:
        return {
            "status": "error",
            "md_path": None,
            "error": str(e),
        }
