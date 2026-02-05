from pydantic import BaseModel
import json
import os

class GameState(BaseModel):
    xp: int = 0
    level: int = 1
    title: str = "Novice Librarian"

class GamificationSystem:
    def __init__(self, data_path="~/Desktop/grand_librairy/game/player_state.json"):
        self.data_path = os.path.expanduser(data_path)
        self.state = self._load_state()

    def _load_state(self) -> GameState:
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r') as f:
                    data = json.load(f)
                return GameState(**data)
            except Exception:
                return GameState()
        return GameState()

    def _save_state(self):
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        with open(self.data_path, 'w') as f:
            f.write(self.state.model_dump_json(indent=2))

    def add_xp(self, amount: int) -> GameState:
        self.state.xp += amount
        self._check_level_up()
        self._save_state()
        return self.state

    def _check_level_up(self):
        # Simple formula: Level = sqrt(XP / 100) or similar, but let's do linear for now
        # Level N requires N * 1000 XP total
        required_xp = self.state.level * 1000
        if self.state.xp >= required_xp:
            self.state.level += 1
            # Update title based on level map (simplified)
            titles = {
                1: "Novice Librarian",
                5: "Scholar",
                10: "Grand Archivist",
                20: "Keeper of Knowledge"
            }
            # Find highest title <= current level
            current_title = "Novice Librarian"
            for lvl, title in sorted(titles.items()):
                if self.state.level >= lvl:
                    current_title = title
            self.state.title = current_title

    def get_level_info(self):
        return self.state.model_dump()
