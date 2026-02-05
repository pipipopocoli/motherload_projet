"""
Manager singleton pour gerer les statuts des agents et les logs de maniere thread-safe.
Utilise par l'interface Tkinter pour se mettre a jour.
"""

import queue
from dataclasses importdataclass
from enum import Enum
from typing import Any, Optional

class AgentName(str, Enum):
    MINER = "Mineur"
    LIBRARIAN = "Bibliothécaire"
    CARTOGRAPHER = "Cartographe"
    ANALYST = "Analyste"
    SYSTEM = "Système"

@dataclass
class AgentState:
    name: AgentName
    status_text: str = "En veille"
    progress: int = 0  # 0-100
    is_active: bool = False
    color: str = "#808080"  # Default gray

# Queue globale pour communiquer avec le thread principal Tkinter
# Contient des tuples: ("log", {name, message, level}) ou ("status", AgentState)
UI_QUEUE: queue.Queue = queue.Queue()

class AgentStatusManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentStatusManager, cls).__new__(cls)
        return cls._instance

    @staticmethod
    def emit_log(agent: AgentName, message: str, level: str = "INFO") -> None:
        """Envoie un log a la console UI."""
        UI_QUEUE.put(("log", {
            "agent": agent,
            "message": message,
            "level": level,
            "timestamp": None  # Sera ajoute a l'affichage
        }))

    @staticmethod
    def update_agent(
        agent: AgentName, 
        status: str, 
        progress: int = 0, 
        is_active: bool = True
    ) -> None:
        """Met a jour l'affichage d'un agent."""
        # Couleurs par defaut pour chaque agent
        colors = {
            AgentName.MINER: "#ff9800",       # Orange
            AgentName.LIBRARIAN: "#2196f3",   # Blue
            AgentName.CARTOGRAPHER: "#4caf50",# Green
            AgentName.ANALYST: "#9c27b0",     # Purple
            AgentName.SYSTEM: "#607d8b"       # Blue Grey
        }
        
        state = AgentState(
            name=agent,
            status_text=status,
            progress=progress,
            is_active=is_active,
            color=colors.get(agent, "#808080")
        )
        UI_QUEUE.put(("status", state))

    @staticmethod
    def reset_agent(agent: AgentName) -> None:
        """Remet un agent en veille."""
        AgentStatusManager.update_agent(agent, "En veille", 0, False)
