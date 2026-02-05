import requests
from bs4 import BeautifulSoup
import time
import random

from motherload_projet.data_mining.user_agents import get_random_header
from motherload_projet.data_mining.mining_logger import log_mining_error

# Common Sci-Hub domains (rotate if needed)
SCIHUB_DOMAINS = ["https://sci-hub.si", "https://sci-hub.se", "https://sci-hub.ru", "https://sci-hub.st"]

def resolve_scihub_url(doi: str) -> dict:
    """Attempt to find a direct PDF download link from Sci-Hub for a given DOI."""
    
    # Validation basique du DOI pour eviter des requetes inutiles
    if not doi or len(doi) < 5:
        return {"status": "error", "message": "Invalid DOI"}

    for domain in SCIHUB_DOMAINS:
        try:
            target_url = f"{domain}/{doi}"
            # Utilisation de headers rotatifs
            headers = get_random_header()
            resp = requests.get(target_url, headers=headers, timeout=15)
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Sci-Hub usually puts the PDF link in an iframe or specific embed
                # Common pattern: <iframe src="..." id="pdf"> or <embed id="pdf" src="...">
                # Or sometimes directly in a button onclick
                
                pdf_src = None
                
                # Method 1: iframe
                iframe = soup.find('iframe', id='pdf')
                if iframe:
                    pdf_src = iframe.get('src')
                
                # Method 2: embed
                if not pdf_src:
                    embed = soup.find('embed', id='pdf')
                    if embed:
                        pdf_src = embed.get('src')
                        
                if pdf_src:
                    # Clean up URL
                    if pdf_src.startswith('//'):
                        pdf_src = 'https:' + pdf_src
                    elif pdf_src.startswith('/'):
                        pdf_src = domain + pdf_src
                        
                    return {
                        "status": "found",
                        "pdf_url": pdf_src,
                        "source": domain
                    }
            else:
                log_mining_error(target_url, f"SCIHUB_HTTP_{resp.status_code}", "Failed to resolve DOI", resp.status_code)
            
            # If we get here, this domain didn't have it or blocked us
            time.sleep(random.uniform(1, 3))
            
        except Exception as e:
            log_mining_error(f"{domain}/{doi}", "SCIHUB_rESOLVE_ERROR", str(e))
            continue
            
    return {"status": "not_found", "message": "DOI not found on active Sci-Hub mirrors"}

def download_scihub_pdf(pdf_url: str) -> bytes:
    """Download the actual PDF bytes from the resolved URL with strict validation."""
    headers = get_random_header()
    try:
        resp = requests.get(pdf_url, headers=headers, stream=True, timeout=30)
        
        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}")
            
        # Validation 1: Content-Type (soft check, server might lie or omit)
        content_type = resp.headers.get("Content-Type", "").lower()
        if content_type and "application/pdf" not in content_type and "application/octet-stream" not in content_type:
            # On loggue mais on continue pour vérifier les magic bytes, parfois misconfiguré
            log_mining_error(pdf_url, "SUSPICIOUS_CONTENT_TYPE", f"Got {content_type}")

        content = resp.content
        
        # Validation 2: Magic Bytes (Strict)
        # Un PDF commence généralement par %PDF-
        if not content.startswith(b"%PDF-"):
            # Parfois il y a des espaces ou charactères avant, on check les 1024 premiers octets
            if b"%PDF-" not in content[:1024]:
                log_mining_error(pdf_url, "INVALID_PDF_MAGIC", "File does not start with %PDF attribution")
                raise Exception("Telechargement invalide: Ce n'est pas un fichier PDF (magic bytes manquants)")

        return content
        
    except Exception as e:
        log_mining_error(pdf_url, "SCIHUB_DOWNLOAD_ERROR", str(e))
        raise Exception(f"Failed to download PDF from SciHub: {e}")
