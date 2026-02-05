
import os
import shutil
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from pypdf import PdfWriter

# Add project root to path
sys.path.append(os.getcwd())

from motherload_projet.local_pdf_update.local_pdf import retro_clean_library

def create_dummy_pdf(path: Path, title=None, author=None, year=None, content="Dummy content"):
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    
    meta = {}
    if title: meta["/Title"] = title
    if author: meta["/Author"] = author
    if year: meta["/CreationDate"] = f"D:{year}0101000000" # Simple PDF date format
    
    writer.add_metadata(meta)
    
    with open(path, "wb") as f:
        writer.write(f)

def test_retro_clean():
    base_dir = Path("temp_test_lib")
    if base_dir.exists():
        shutil.rmtree(base_dir)
    base_dir.mkdir()
    
    pdf_root = base_dir / "pdfs"
    collections_root = base_dir / "collections"
    collections_root.mkdir()
    
    # Setup Collections
    (collections_root / "Bio").mkdir()
    (collections_root / "Architecture").mkdir()
    
    # 1. Normal Rename Case
    # Bio/Sub1/badname.pdf -> Author - Year - Title.pdf
    p1 = pdf_root / "Bio" / "Sub1" / "badname.pdf"
    create_dummy_pdf(p1, title="Cell Biology", author="Smith, John", year="2020")
    
    # 2. Unknown Case
    # Bio/Sub1/unknown.pdf -> Bio/_Inconnus_A_Trier/unknown.pdf
    p2 = pdf_root / "Bio" / "Sub1" / "unknown.pdf"
    create_dummy_pdf(p2) # No metadata
    
    # 3. Semantic Suggestion Case
    # Bio/Sub1/arch.pdf -> Suggestion to move to Architecture
    p3 = pdf_root / "Bio" / "Sub1" / "arch.pdf"
    create_dummy_pdf(p3, title="Modern Architecture Design", author="Doe, Jane", year="2021")
    
    print("Files created. Running cleanup...")
    
    # Mock paths
    with patch("motherload_projet.local_pdf_update.local_pdf.library_root", return_value=base_dir), \
         patch("motherload_projet.local_pdf_update.local_pdf.collections_root", return_value=collections_root), \
         patch("motherload_projet.local_pdf_update.local_pdf.bibliotheque_root", return_value=base_dir / "bib"), \
         patch("motherload_projet.local_pdf_update.local_pdf.reports_root", return_value=base_dir / "reports"):
         
         # Mock catalog functions to avoid CSV errors if any
         with patch("motherload_projet.local_pdf_update.local_pdf.load_master_catalog", return_value=MagicMock()), \
              patch("motherload_projet.local_pdf_update.local_pdf.upsert_scan_pdf_entry", return_value=(MagicMock(), {"action": "created"})):
              
              # Call function
              result = retro_clean_library(pdf_root)
              
    print("Result:", result)
    
    # Verification
    # 1. Check Rename
    expected_name = "Smith - 2020 - Cell Biology.pdf"
    if (pdf_root / "Bio" / "Sub1" / expected_name).exists():
        print("[PASS] Normal Rename")
    else:
        print(f"[FAIL] Normal Rename. File not found: {expected_name}")
        print("Found:", list((pdf_root / "Bio" / "Sub1").iterdir()))

    # 2. Check Unknown
    if (pdf_root / "Bio" / "_Inconnus_A_Trier" / "unknown.pdf").exists():
        print("[PASS] Unknown Move")
    else:
        print("[FAIL] Unknown Move")
        
    # 3. Check Suggestions (in report lines, but we can't easily check internal var)
    # However we can check if file was NOT moved but renamed in place
    expected_arch = "Doe - 2021 - Modern Architecture Design.pdf"
    if (pdf_root / "Bio" / "Sub1" / expected_arch).exists():
        print("[PASS] Semantic Rename (Stayed in place)")
    else:
        print(f"[FAIL] Semantic Rename. File: {expected_arch}")

    # Check report content if possible, but for now we rely on function return 'suggestions' key if we added it
    if result.get("suggestions", 0) > 0:
        print(f"[PASS] Suggestions count: {result['suggestions']}")
    else:
        print("[FAIL] No suggestions reported")

    # Clean up
    # shutil.rmtree(base_dir)

if __name__ == "__main__":
    try:
        test_retro_clean()
    except Exception as e:
        print(f"Test failed with error: {e}")
