"""
Crawler de PDFs pour le projet Motherload.
Aspirateur de site qui recherche et télécharge tous les fichiers PDF.
"""

import argparse
import time
import os
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

# Import interne
from motherload_projet.data_mining.fetcher import fetch_url
from motherload_projet.data_mining.mining_logger import log_mining_error
from motherload_projet.data_mining.user_agents import get_random_header

def is_pdf_url(url: str) -> bool:
    """Verifie si l'URL pointe probablement vers un PDF."""
    path = urlparse(url).path.lower()
    return path.endswith(".pdf")

def sanitize_filename(url: str) -> str:
    """Cree un nom de fichier sur a partir de l'URL."""
    path = urlparse(url).path
    name = os.path.basename(path)
    if not name.lower().endswith(".pdf"):
        name = "document.pdf"
    # Basic cleanup
    return "".join(c for c in name if c.isalnum() or c in "._-")

def crawl_and_download(start_url: str, output_dir: Path, max_depth: int = 0):
    """
    Crawle l'URL donnee et telecharge les PDFs trouves.
    Note: max_depth=0 signifie "juste cette page".
    """
    visited = set()
    queue = [(start_url, 0)]
    
    # Ensure output dir exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[*] Demarrage du crawler sur: {start_url}")
    print(f"[*] Dossier de destination: {output_dir}")

    total_downloaded = 0
    total_errors = 0

    while queue:
        url, depth = queue.pop(0)
        
        if url in visited:
            continue
        visited.add(url)
        
        if depth > max_depth:
            continue

        print(f"[-] Parsing: {url} (Depth: {depth})")
        
        # 1. Fetch de la page
        ok, status, ctype, final_url, content, error = fetch_url(url)
        
        if not ok:
            print(f"[!] Echec fetch {url}: {status} {error}")
            log_mining_error(url, f"CRAWL_FETCH_ERROR_{status}", str(error), status)
            total_errors += 1
            continue

        # Si c'est directement un PDF (cas rare si on crawle une page HTML, mais possible)
        if "application/pdf" in ctype or is_pdf_url(final_url):
            filename = sanitize_filename(final_url)
            # Eviter doublons
            count = 1
            target_path = output_dir / filename
            while target_path.exists():
                stem = target_path.stem
                if "_" in stem and stem.rsplit("_", 1)[-1].isdigit():
                     stem = stem.rsplit("_", 1)[0]
                target_path = output_dir / f"{stem}_{count:02d}.pdf"
                count += 1
            
            try:
                if content.startswith(b"%PDF") or b"%PDF-" in content[:1024]:
                    target_path.write_bytes(content)
                    print(f"[+] PDF Telecharge: {target_path.name}")
                    total_downloaded += 1
                else:
                    print(f"[!] Faux PDF detecte: {url}")
                    log_mining_error(url, "FAKE_PDF", "Content-Type is PDF but magic bytes missing")
            except Exception as e:
                print(f"[!] Erreur ecriture: {e}")
                log_mining_error(url, "WRITE_ERROR", str(e))
            continue

        # 2. Parse HTML pour trouver des liens
        try:
            soup = BeautifulSoup(content, 'html.parser')
            links = soup.find_all('a', href=True)
            
            for link in links:
                raw_href = link['href']
                full_url = urljoin(final_url, raw_href)
                
                # Filtrage basique
                if not full_url.startswith("http"):
                    continue
                
                if is_pdf_url(full_url):
                    # On telecharge le PDF detecte
                    if full_url not in visited:
                        # On l'ajoute a la queue avec depth + 1 pour qu'il soit traite comme un "PDF direct"
                        # au prochain tour de boucle ou on le traite tout de suite?
                        # Mieux vaut le traiter a part pour ne pas melanger logic de crawling et downloading
                        # Mais ici notre boucle traite tout.
                        # Cependant, fetch_url fait une requete. 
                        # Si on veut juste telecharger, on peut l'ajouter a la queue.
                        # Mais attention, si max_depth est atteint, on ne le telechargera pas si on check depth > max_depth au debut.
                        # Pour les fichiers terminaux (PDF), on devrait peut-etre ignorer depth?
                        # Ou dire que depth est pour "suivre les liens HTML".
                        
                        print(f"    -> Trouve PDF: {full_url}")
                        # On peut appeler fetch_url ici directement pour simplifier
                        ok_pdf, code_pdf, type_pdf, final_pdf, content_pdf, err_pdf = fetch_url(full_url)
                        visited.add(full_url) # Mark as visited
                        
                        if ok_pdf and (b"%PDF-" in content_pdf[:1024]):
                            filename = sanitize_filename(final_pdf)
                            target_path = output_dir / filename
                            
                            # Deduplication nom
                            count = 1
                            while target_path.exists():
                                target_path = output_dir / f"{target_path.stem}_{count}.pdf"
                                count += 1
                                
                            target_path.write_bytes(content_pdf)
                            print(f"    [+] Telecharge: {target_path.name}")
                            total_downloaded += 1
                        else:
                             print(f"    [!] Echec download PDF: {code_pdf}")
                             log_mining_error(full_url, "PDF_DOWNLOAD_FAIL", f"Status: {code_pdf}")
                             total_errors += 1
                    
                elif depth < max_depth:
                    # Si c'est un lien HTML et qu'on veut approfondir
                    # On evite de sortir du domaine principal pour eviter de crawler internet entier
                    if urlparse(full_url).netloc == urlparse(start_url).netloc:
                         queue.append((full_url, depth + 1))
        
        except Exception as e:
             print(f"[!] Erreur parsing {url}: {e}")
             log_mining_error(url, "PARSE_ERROR", str(e))
             
        # Petite pause pour etre poli
        time.sleep(1)

    print("-" * 30)
    print(f"Termine. Telecharges: {total_downloaded}, Erreurs: {total_errors}")


def main():
    parser = argparse.ArgumentParser(description="Motherload PDF Crawler")
    parser.add_argument("url", help="URL de depart")
    parser.add_argument("--output", "-o", default="./downloads", help="Dossier de sortie")
    parser.add_argument("--depth", "-d", type=int, default=0, help="Profondeur de crawl (0 = juste la page, 1 = liens suivis)")
    
    args = parser.parse_args()
    
    crawl_and_download(args.url, Path(args.output), args.depth)

if __name__ == "__main__":
    main()
