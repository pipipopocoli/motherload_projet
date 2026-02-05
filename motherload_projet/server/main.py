from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import pandas as pd
import threading
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from motherload_projet.ecosysteme_visualisation.indexer import load_index, rebuild_index
from motherload_projet.data_mining.recuperation_article.run_unpaywall_batch import run_unpaywall_csv_batch
from motherload_projet.data_mining.tor_connector import check_tor_connection, fetch_zclient_onion
from motherload_projet.data_mining.scihub_connector import resolve_scihub_url
from .gamification import GamificationSystem
from .agent_neo import AgentNeo

app = FastAPI(title="Motherload Grand Librarium", version="3.0.0")

# CORS for React Client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the client URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize subsystems
game_system = GamificationSystem()
agent_neo = AgentNeo()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Grand Librarium", "version": "Phase 3 (Renaissance)"}

@app.get("/api/status")
def get_status():
    return {
        "neo_status": agent_neo.status,
        "level": game_system.get_level_info(),
        "tasks_pending": 0
    }

    new_state = game_system.add_xp(amount)
    return new_state

@app.get("/api/library")
def get_library():
    # Hardcoded path for now, should use config in future
    catalog_path = Path.home() / "Desktop/grand_librairy/bibliotheque/master_catalog.csv"
    if not catalog_path.exists():
        return {"count": 0, "articles": []}
    
    try:
        df = pd.read_csv(catalog_path)
        # Handle nan values for JSON conversion
        df = df.where(pd.notnull(df), None)
        return {
            "count": len(df),
            "articles": df.to_dict(orient="records")
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/ecosystem")
def get_ecosystem():
    """Returns the current cached index."""
    return load_index()

@app.post("/api/ecosystem/scan")
def scan_ecosystem(background_tasks: BackgroundTasks):
    """Triggers a rebuild of the index."""
    # We scan the parent directory of 'motherload_projet' package, which is roughly CWD based on structure
    # based on structure: Desktop/motherload_projet/motherload_projet
    # We want to scan Desktop/motherload_projet
    
    # Actually, let's scan the current working directory's 'motherload_projet' subfolder
    # Assuming CWD is the project root.
    project_root = Path.cwd() 
    
    # Run synchronously for now to return result immediately, or async if slow
    try:
        index = rebuild_index(project_root)
        return index
    except Exception as e:
        return {"error": str(e)}



@app.post("/api/scanner/demo")
def start_demo_scan(background_tasks: BackgroundTasks):
    """Starts a demo Unpaywall batch scan in the background."""
    try:
        # Create sample CSV on desktop if not exists (or temp dir)
        # For simplicity, we assume we can write to a temp path
        desktop = Path.home() / "Desktop"
        csv_path = desktop / "demo_articles.csv"
        
        # Determine output dir
        collection_dir = Path.home() / "Desktop/grand_librairy/collections/demo_scan"
        collection_dir.mkdir(parents=True, exist_ok=True)
        
        def run_task():
            if not csv_path.exists():
                generate_sample_csv(csv_path)
            run_unpaywall_csv_batch(csv_path, collection_dir)

        background_tasks.add_task(run_task)
        return {"status": "started", "message": "Demo scan running in background. Check terminal for progress."}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/tor/status")
def get_tor_status():
    """Check if Tor proxy is accessible."""
    return check_tor_connection()

@app.get("/api/tor/check-zlib")
def check_zlib_status():
    """Check connection to Z-Library onion address."""
    # Hardcoded address from user request
    ONION = "loginzlib2vrak5zzpcocc3ouizykn6k5qecgj2tzlnab5wcbqhembyd.onion"
    # Append http schema if missing
    url = f"http://{ONION}"
    return fetch_zclient_onion(url)

@app.get("/api/scihub/resolve")
def get_scihub_link(doi: str):
    """Resolve a DOI to a Sci-Hub PDF URL."""
    return resolve_scihub_url(doi)

@app.get("/api/scihub/resolve")
def get_scihub_link(doi: str):
    """Resolve a DOI to a Sci-Hub PDF URL."""
    return resolve_scihub_url(doi)

# Mount the React App Static Files
# We serve 'dist' which is built by 'npm run build' / 'vite build'
static_dir = Path(__file__).parent.parent / "client/dist"
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        """Serve the React app (index.html) for any unmatched route."""
        # API routes are already matched above.
        # Check if file exists in static (e.g. icon.png)
        possible_file = static_dir / full_path
        if possible_file.is_file():
            return FileResponse(possible_file)
            
        # Fallback to index.html for SPA routing
        return FileResponse(static_dir / "index.html")
else:
    print(f"WARNING: Static directory not found at {static_dir}")

# app.mount("/", StaticFiles(directory="motherload_projet/client/dist", html=True), name="static")

def start_server(host="127.0.0.1", port=8000):
    """Function to start the server programmatically"""
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_server()
