"""
Widget Dashboard pour afficher l'etat des 4 agents.
"""

import tkinter as tk
from tkinter import ttk
from motherload_projet.desktop_app.agent_status import AgentName, AgentState

class AgentCard(ttk.Frame):
    """Carte individuelle pour un agent."""
    
    def __init__(self, parent, agent_name: AgentName, icon_char: str):
        super().__init__(parent, relief="ridge", borderwidth=2, padding=10)
        self.agent_name = agent_name
        
        # Header: Icon + Name
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 5))
        
        self.icon_label = tk.Label(
            header, 
            text=icon_char, 
            font=("Arial", 24), 
            fg="#808080"
        )
        self.icon_label.pack(side="left", padx=(0, 10))
        
        name_lbl = ttk.Label(header, text=agent_name.value, font=("Helvetica", 12, "bold"))
        name_lbl.pack(side="left", fill="x")
        
        # Status Text
        self.status_var = tk.StringVar(value="En veille")
        self.status_lbl = ttk.Label(
            self, 
            textvariable=self.status_var, 
            font=("Helvetica", 10),
            wraplength=180
        )
        self.status_lbl.pack(fill="x", pady=(5, 5))
        
        # Progress Bar
        self.progress = ttk.Progressbar(self, length=200, mode="determinate")
        self.progress.pack(fill="x", pady=(5, 0))
        
    def update_state(self, state: AgentState):
        self.status_var.set(state.status_text)
        self.progress["value"] = state.progress
        
        # Update active visual cue
        if state.is_active:
            self.icon_label.config(fg=state.color)
            self.configure(relief="solid")  # Highlight border
        else:
            self.icon_label.config(fg="#808080")
            self.configure(relief="ridge")

class DashboardWidget(ttk.Frame):
    """Panneau principal du Dashboard."""
    
    def __init__(self, parent, library_root=None, bibliotheque_root=None):
        super().__init__(parent, padding=20)
        
        self.cards = {}
        
        # Agent Cards Section
        cards_frame = ttk.Frame(self)
        cards_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Grid layout 2x2 for agent cards
        # Row 0
        self._create_card(cards_frame, AgentName.MINER, "⛏️", 0, 0)
        self._create_card(cards_frame, AgentName.LIBRARIAN, "📚", 0, 1)
        
        # Row 1
        self._create_card(cards_frame, AgentName.CARTOGRAPHER, "🗺️", 1, 0)
        self._create_card(cards_frame, AgentName.ANALYST, "🧠", 1, 1)
        
        # Center elements
        cards_frame.columnconfigure(0, weight=1)
        cards_frame.columnconfigure(1, weight=1)
        
        # Stats Widget Section (if paths provided)
        if library_root and bibliotheque_root:
            from motherload_projet.ui.stats_widget import StatsWidget
            separator = ttk.Separator(self, orient="horizontal")
            separator.pack(fill="x", pady=10)
            
            self.stats_widget = StatsWidget(self, library_root, bibliotheque_root)
            self.stats_widget.pack(fill="both", expand=True)
        else:
            self.stats_widget = None
        
    def _create_card(self, parent, agent: AgentName, icon: str, row: int, col: int):
        card = AgentCard(parent, agent, icon)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        self.cards[agent] = card
        
    def update_agent(self, state: AgentState):
        if state.name in self.cards:
            self.cards[state.name].update_state(state)
    
    def refresh_stats(self):
        """Rafraîchit les statistiques si le widget existe."""
        if self.stats_widget:
            self.stats_widget.refresh_stats()
