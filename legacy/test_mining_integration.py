#!/usr/bin/env python3
"""
Phase 4 Integration Test - Le Mineur
Tests complets de l'infrastructure de mining en conditions réelles.
"""

import sys
import time
from pathlib import Path
from datetime import datetime
import json

# Imports du projet
from motherload_projet.data_mining.crawler import crawl_and_download
from motherload_projet.data_mining.scihub_connector import resolve_scihub_url
from motherload_projet.data_mining.fetcher import fetch_url
from motherload_projet.data_mining.user_agents import get_random_user_agent
from motherload_projet.data_mining.mining_logger import get_log_path
from motherload_projet.local_pdf_update.local_pdf import ingest_pdf
from motherload_projet.library.paths import collections_root

class TestReport:
    """Classe pour générer le rapport de test."""
    def __init__(self):
        self.start_time = datetime.now()
        self.tests = []
        self.stats = {
            "crawler_pdfs": 0,
            "shadow_successes": 0,
            "shadow_failures": 0,
            "ua_rotations": 0,
            "librarian_ingests": 0,
            "total_errors": 0
        }
    
    def add_test(self, name: str, status: str, details: str):
        self.tests.append({
            "name": name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def generate_report(self) -> str:
        duration = (datetime.now() - self.start_time).total_seconds()
        
        report = []
        report.append("=" * 60)
        report.append("RAPPORT DE TEST - PHASE 4 INTEGRATION")
        report.append("=" * 60)
        report.append(f"Début: {self.start_time.isoformat()}")
        report.append(f"Durée: {duration:.2f}s")
        report.append("")
        
        report.append("STATISTIQUES:")
        report.append(f"  - PDFs téléchargés (Crawler): {self.stats['crawler_pdfs']}")
        report.append(f"  - Shadow Mining (Succès): {self.stats['shadow_successes']}")
        report.append(f"  - Shadow Mining (Échecs): {self.stats['shadow_failures']}")
        report.append(f"  - User-Agent Rotations vérifiées: {self.stats['ua_rotations']}")
        report.append(f"  - PDFs ingérés par Librarian: {self.stats['librarian_ingests']}")
        report.append(f"  - Erreurs totales: {self.stats['total_errors']}")
        report.append("")
        
        report.append("DÉTAILS DES TESTS:")
        for test in self.tests:
            status_icon = "✓" if test["status"] == "PASS" else "✗"
            report.append(f"{status_icon} {test['name']}: {test['status']}")
            report.append(f"   {test['details']}")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)

def test_user_agent_rotation(report: TestReport):
    """Test 1: Vérification de la rotation des User-Agents."""
    print("\n[TEST 1] User-Agent Rotation...")
    
    try:
        agents = set()
        for i in range(10):
            ua = get_random_user_agent()
            agents.add(ua)
        
        if len(agents) > 1:
            report.add_test(
                "User-Agent Rotation",
                "PASS",
                f"{len(agents)} User-Agents différents sur 10 requêtes"
            )
            report.stats["ua_rotations"] = len(agents)
            print(f"  ✓ {len(agents)} User-Agents différents détectés")
        else:
            report.add_test(
                "User-Agent Rotation",
                "FAIL",
                "Aucune rotation détectée"
            )
            print("  ✗ ÉCHEC: Pas de rotation")
    except Exception as e:
        report.add_test("User-Agent Rotation", "ERROR", str(e))
        report.stats["total_errors"] += 1
        print(f"  ✗ ERREUR: {e}")

def test_shadow_mining(report: TestReport):
    """Test 2: Validation du Shadow Mining (SciHub fallback)."""
    print("\n[TEST 2] Shadow Mining (SciHub)...")
    
    # DOIs de test (articles Open Access connus)
    test_dois = [
        "10.1371/journal.pone.0259580",  # PLOS ONE
        "10.7717/peerj.4375",            # PeerJ
        "10.1038/nphys1170",             # Nature Physics (peut échouer si paywall)
        "10.1103/PhysRevLett.116.061102", # Physical Review (peut échouer)
        "10.1093/nar/gkz1031"            # Nucleic Acids Research
    ]
    
    for doi in test_dois:
        try:
            print(f"  Testing DOI: {doi}")
            result = resolve_scihub_url(doi)
            
            if result.get("status") == "found":
                report.stats["shadow_successes"] += 1
                print(f"    ✓ Trouvé: {result.get('pdf_url')}")
            else:
                report.stats["shadow_failures"] += 1
                print(f"    ✗ Non trouvé: {result.get('message')}")
            
            time.sleep(2)  # Politesse
        except Exception as e:
            report.stats["shadow_failures"] += 1
            report.stats["total_errors"] += 1
            print(f"    ✗ ERREUR: {e}")
    
    total = len(test_dois)
    success_rate = (report.stats["shadow_successes"] / total) * 100
    
    report.add_test(
        "Shadow Mining",
        "PASS" if success_rate >= 40 else "PARTIAL",
        f"{report.stats['shadow_successes']}/{total} DOIs résolus ({success_rate:.1f}%)"
    )

def test_crawler_stress(report: TestReport):
    """Test 3: Stress test du crawler sur une vraie page."""
    print("\n[TEST 3] Crawler Stress Test...")
    
    # On va utiliser arXiv qui est public et a beaucoup de PDFs
    test_url = "https://arxiv.org/list/cs.AI/recent"
    output_dir = Path("./test_mining_output")
    
    try:
        print(f"  Crawling: {test_url}")
        print(f"  Output: {output_dir}")
        
        # Nettoyer le dossier de test s'il existe
        if output_dir.exists():
            for f in output_dir.glob("*.pdf"):
                f.unlink()
        
        # Lancer le crawler (depth=0 pour juste la page)
        crawl_and_download(test_url, output_dir, max_depth=0)
        
        # Compter les PDFs téléchargés
        pdfs = list(output_dir.glob("*.pdf"))
        report.stats["crawler_pdfs"] = len(pdfs)
        
        if len(pdfs) >= 10:
            report.add_test(
                "Crawler Stress Test",
                "PASS",
                f"{len(pdfs)} PDFs téléchargés (objectif: ≥10)"
            )
            print(f"  ✓ {len(pdfs)} PDFs téléchargés")
        elif len(pdfs) > 0:
            report.add_test(
                "Crawler Stress Test",
                "PARTIAL",
                f"{len(pdfs)} PDFs téléchargés (objectif: ≥10)"
            )
            print(f"  ⚠ Seulement {len(pdfs)} PDFs téléchargés")
        else:
            report.add_test(
                "Crawler Stress Test",
                "FAIL",
                "Aucun PDF téléchargé"
            )
            print("  ✗ ÉCHEC: Aucun PDF")
            
    except Exception as e:
        report.add_test("Crawler Stress Test", "ERROR", str(e))
        report.stats["total_errors"] += 1
        print(f"  ✗ ERREUR: {e}")

def test_librarian_integration(report: TestReport):
    """Test 4: Intégration avec le Bibliothécaire."""
    print("\n[TEST 4] Intégration Librarian...")
    
    try:
        output_dir = Path("./test_mining_output")
        pdfs = list(output_dir.glob("*.pdf"))
        
        if not pdfs:
            report.add_test(
                "Librarian Integration",
                "SKIP",
                "Aucun PDF disponible pour test"
            )
            print("  ⚠ SKIP: Pas de PDFs à ingérer")
            return
        
        # Tester l'ingestion du premier PDF
        test_pdf = pdfs[0]
        print(f"  Ingesting: {test_pdf.name}")
        
        # Créer une collection de test
        test_collection = "test_mining"
        
        result = ingest_pdf(test_pdf, test_collection, None)
        
        if result.get("status") == "success":
            report.stats["librarian_ingests"] += 1
            report.add_test(
                "Librarian Integration",
                "PASS",
                f"PDF ingéré avec succès: {result.get('new_name', 'N/A')}"
            )
            print(f"  ✓ Ingestion réussie: {result.get('new_name')}")
        else:
            report.add_test(
                "Librarian Integration",
                "FAIL",
                f"Échec: {result.get('error', 'Unknown')}"
            )
            print(f"  ✗ ÉCHEC: {result.get('error')}")
            
    except Exception as e:
        report.add_test("Librarian Integration", "ERROR", str(e))
        report.stats["total_errors"] += 1
        print(f"  ✗ ERREUR: {e}")

def test_error_logging(report: TestReport):
    """Test 5: Vérification du logging des erreurs."""
    print("\n[TEST 5] Error Logging...")
    
    try:
        log_path = get_log_path()
        
        # Forcer une erreur
        fetch_url("https://this-domain-does-not-exist-test-12345.com")
        
        time.sleep(0.5)  # Attendre que le log soit écrit
        
        if log_path.exists():
            content = log_path.read_text()
            if "this-domain-does-not-exist" in content:
                report.add_test(
                    "Error Logging",
                    "PASS",
                    f"Log actif: {log_path}"
                )
                print(f"  ✓ Logging fonctionnel: {log_path}")
            else:
                report.add_test(
                    "Error Logging",
                    "PARTIAL",
                    "Log existe mais erreur de test non trouvée"
                )
                print("  ⚠ Log existe mais contenu incomplet")
        else:
            report.add_test(
                "Error Logging",
                "FAIL",
                "Fichier de log non créé"
            )
            print("  ✗ ÉCHEC: Pas de fichier log")
            
    except Exception as e:
        report.add_test("Error Logging", "ERROR", str(e))
        report.stats["total_errors"] += 1
        print(f"  ✗ ERREUR: {e}")

def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  PHASE 4 - INTEGRATION TEST - LE MINEUR                   ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    report = TestReport()
    
    # Exécuter tous les tests
    test_user_agent_rotation(report)
    test_shadow_mining(report)
    test_crawler_stress(report)
    test_librarian_integration(report)
    test_error_logging(report)
    
    # Générer le rapport
    print("\n" + "=" * 60)
    report_text = report.generate_report()
    print(report_text)
    
    # Sauvegarder le rapport
    report_path = Path("mining_integration_test_report.txt")
    report_path.write_text(report_text)
    print(f"\nRapport sauvegardé: {report_path}")
    
    # Sauvegarder aussi en JSON pour analyse
    json_path = Path("mining_integration_test_report.json")
    json_data = {
        "timestamp": report.start_time.isoformat(),
        "stats": report.stats,
        "tests": report.tests
    }
    json_path.write_text(json.dumps(json_data, indent=2))
    print(f"Rapport JSON: {json_path}")

if __name__ == "__main__":
    main()
