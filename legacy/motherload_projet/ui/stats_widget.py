"""
Module de statistiques pour le Dashboard.
Génère des graphiques simples en ASCII/Canvas pour visualiser les métriques.
"""

from pathlib import Path
from datetime import datetime
from collections import defaultdict
import tkinter as tk
from tkinter import ttk

def count_pdfs_by_month(library_root: Path) -> dict[str, int]:
    """Compte les PDFs par mois de création."""
    counts = defaultdict(int)
    
    if not library_root.exists():
        return counts
    
    for pdf in library_root.rglob("*.pdf"):
        try:
            mtime = pdf.stat().st_mtime
            month_key = datetime.fromtimestamp(mtime).strftime("%Y-%m")
            counts[month_key] += 1
        except Exception:
            continue
    
    return dict(sorted(counts.items())[-12:])  # Last 12 months

def count_queue_items(bibliotheque_root: Path) -> int:
    """Compte le nombre total d'items dans les queues."""
    total = 0
    
    if not bibliotheque_root.exists():
        return 0
    
    try:
        import pandas as pd
        for queue_file in bibliotheque_root.glob("to_be_downloaded_*.csv"):
            try:
                df = pd.read_csv(queue_file)
                total += len(df)
            except Exception:
                continue
    except ImportError:
        pass
    
    return total

class StatsWidget(ttk.Frame):
    """Widget de statistiques pour le Dashboard."""
    
    def __init__(self, parent, library_root: Path, bibliotheque_root: Path):
        super().__init__(parent, padding=10)
        self.library_root = library_root
        self.bibliotheque_root = bibliotheque_root
        
        # Title
        title = ttk.Label(self, text="📊 Statistiques", font=("Helvetica", 14, "bold"))
        title.pack(anchor="w", pady=(0, 10))
        
        # Stats Frame
        stats_frame = ttk.Frame(self)
        stats_frame.pack(fill="both", expand=True)
        
        # Queue Size
        self.queue_label = ttk.Label(
            stats_frame, 
            text="Queue: Calcul...", 
            font=("Helvetica", 11)
        )
        self.queue_label.pack(anchor="w", pady=5)
        
        # PDFs per Month (Simple Bar Chart)
        chart_label = ttk.Label(stats_frame, text="PDFs par mois (12 derniers):", font=("Helvetica", 10))
        chart_label.pack(anchor="w", pady=(10, 5))
        
        self.chart_canvas = tk.Canvas(stats_frame, height=120, bg="#f5f5f5")
        self.chart_canvas.pack(fill="x", expand=True)
        
        # Refresh button
        ttk.Button(self, text="🔄 Rafraîchir", command=self.refresh_stats).pack(anchor="e", pady=(10, 0))
        
        # Initial load
        self.refresh_stats()
    
    def refresh_stats(self):
        """Rafraîchit les statistiques."""
        # Queue count
        queue_count = count_queue_items(self.bibliotheque_root)
        self.queue_label.config(text=f"📥 Queue: {queue_count} articles en attente")
        
        # PDFs by month
        monthly_data = count_pdfs_by_month(self.library_root)
        self._draw_bar_chart(monthly_data)
    
    def _draw_bar_chart(self, data: dict[str, int]):
        """Dessine un graphique à barres simple."""
        self.chart_canvas.delete("all")
        
        if not data:
            self.chart_canvas.create_text(
                10, 60, 
                text="Aucune donnée disponible", 
                anchor="w",
                fill="#999"
            )
            return
        
        width = self.chart_canvas.winfo_width()
        if width < 10:
            width = 600  # Default
        
        height = 120
        max_val = max(data.values()) if data else 1
        bar_width = max(width / len(data) - 10, 20)
        
        x = 10
        for month, count in data.items():
            bar_height = (count / max_val) * 80 if max_val > 0 else 0
            
            # Bar
            self.chart_canvas.create_rectangle(
                x, height - bar_height - 20,
                x + bar_width, height - 20,
                fill="#4caf50",
                outline=""
            )
            
            # Label (month)
            month_short = month[-2:]  # Just MM
            self.chart_canvas.create_text(
                x + bar_width/2, height - 5,
                text=month_short,
                font=("Arial", 8),
                fill="#666"
            )
            
            # Count
            if count > 0:
                self.chart_canvas.create_text(
                    x + bar_width/2, height - bar_height - 25,
                    text=str(count),
                    font=("Arial", 9, "bold"),
                    fill="#333"
                )
            
            x += bar_width + 10
