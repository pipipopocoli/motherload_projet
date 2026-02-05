"""
Widget LogConsole pour afficher les logs avec des codes couleurs.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from motherload_projet.desktop_app.agent_status import AgentName

class LogConsole(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self)
        scrollbar.pack(side="right", fill="y")
        
        # Text widget
        self.text_area = tk.Text(
            self, 
            height=8, 
            state="disabled", 
            yscrollcommand=scrollbar.set,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#d4d4d4"
        )
        self.text_area.pack(fill="both", expand=True)
        scrollbar.config(command=self.text_area.yview)
        
        # Configure tags for colors
        self.text_area.tag_config(AgentName.MINER.value, foreground="#ffb74d")       # Light Orange
        self.text_area.tag_config(AgentName.LIBRARIAN.value, foreground="#64b5f6")   # Light Blue
        self.text_area.tag_config(AgentName.CARTOGRAPHER.value, foreground="#81c784")# Light Green
        self.text_area.tag_config(AgentName.ANALYST.value, foreground="#ba68c8")     # Light Purple
        self.text_area.tag_config(AgentName.SYSTEM.value, foreground="#90a4ae")      # Light Blue Grey
        self.text_area.tag_config("TIMESTAMP", foreground="#616161")                 # Dark Grey
        
    def append_log(self, agent: AgentName, message: str, level: str = "INFO"):
        self.text_area.configure(state="normal")
        
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        
        # Insert line: [Time] [Agent] Message
        self.text_area.insert("end", f"{timestamp} ", "TIMESTAMP")
        self.text_area.insert("end", f"[{agent.value}] ", agent.value)
        self.text_area.insert("end", f"{message}\n")
        
        self.text_area.configure(state="disabled")
        self.text_area.see("end")
