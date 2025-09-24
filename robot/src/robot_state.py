#!/usr/bin/env python3
"""
Gestionnaire d'état du robot pour gérer le freeze/unfreeze
"""

import os
import json
from datetime import datetime
from typing import Dict, Optional

import os
from dotenv import load_dotenv

class RobotStateManager:
    """Gestionnaire d'état du robot"""

    def __init__(self, state_file: str = "data/robot_state.json"):
        """
        Initialiser le gestionnaire d'état
        Args:
            state_file: Chemin vers le fichier d'état
        """
        load_dotenv()
        self.state_file = state_file
        self._ensure_data_directory()
        if not os.path.exists(self.state_file):
            # File does not exist, use .env for initial frozen state
            self.state = self._get_default_state()
            self.set_frozen_from_env()
        else:
            self._load_state()

    def set_frozen_from_env(self):
        status = os.getenv('ROBOT_STATUS', 'frozen').lower()
        if status in ['frozen', 'true', '1', 'yes']:
            self.state['is_frozen'] = True
            self.state['freeze_reason'] = 'Initial state from .env (frozen)'
        else:
            self.state['is_frozen'] = False
            self.state['freeze_reason'] = None
        self._save_state()
    
    def _ensure_data_directory(self):
        """S'assurer que le répertoire data existe"""
        data_dir = os.path.dirname(self.state_file)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
    
    def _load_state(self):
        """Charger l'état depuis le fichier"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    self.state = json.load(f)
                # Ensure newly added keys exist with defaults
                self._ensure_state_defaults()
            else:
                self.state = self._get_default_state()
                self._save_state()
        except Exception as e:
            print(f"Erreur lors du chargement de l'état: {e}")
            self.state = self._get_default_state()
            self._save_state()
    
    def _get_default_state(self) -> Dict:
        """Obtenir l'état par défaut"""
        return {
            "is_frozen": False,
            "freeze_reason": None,
            "freeze_timestamp": None,
            "last_cycle_time": None,
            "cycles_suspended": 0,
            # Trading window state
            "current_trade_number": 1,
            "trade_start_timestamp": None,
            "trade_start_bnb_reserve": None
        }
    
    def _ensure_state_defaults(self):
        """Backfill newly introduced keys in an existing state file"""
        defaults = self._get_default_state()
        changed = False
        for k, v in defaults.items():
            if k not in self.state:
                self.state[k] = v
                changed = True
        if changed:
            self._save_state()
    
    def _save_state(self):
        """Sauvegarder l'état dans le fichier"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de l'état: {e}")
    
    def is_frozen(self) -> bool:
        """Vérifier si le robot est gelé"""
        return self.state.get("is_frozen", False)
    
    def freeze_robot(self, reason: str = "Manuellement gelé par l'utilisateur") -> bool:
        """
        Geler le robot
        
        Args:
            reason: Raison du gel
            
        Returns:
            True si le gel a réussi
        """
        try:
            self.state["is_frozen"] = True
            self.state["freeze_reason"] = reason
            self.state["freeze_timestamp"] = datetime.now().isoformat()
            self._save_state()
            return True
        except Exception as e:
            print(f"Erreur lors du gel du robot: {e}")
            return False
    
    def unfreeze_robot(self) -> bool:
        """
        Dégeler le robot
        
        Returns:
            True si le dégel a réussi
        """
        try:
            self.state["is_frozen"] = False
            self.state["freeze_reason"] = None
            self.state["freeze_timestamp"] = None
            self._save_state()
            return True
        except Exception as e:
            print(f"Erreur lors du dégel du robot: {e}")
            return False
    
    def get_freeze_reason(self) -> Optional[str]:
        """Obtenir la raison du gel"""
        return self.state.get("freeze_reason")
    
    def get_freeze_timestamp(self) -> Optional[str]:
        """Obtenir le timestamp du gel"""
        return self.state.get("freeze_timestamp")
    
    def increment_suspended_cycles(self):
        """Incrémenter le compteur de cycles suspendus"""
        self.state["cycles_suspended"] = self.state.get("cycles_suspended", 0) + 1
        self._save_state()
    
    def reset_suspended_cycles(self):
        """Remettre à zéro le compteur de cycles suspendus"""
        self.state["cycles_suspended"] = 0
        self._save_state()
    
    def get_suspended_cycles(self) -> int:
        """Obtenir le nombre de cycles suspendus"""
        return self.state.get("cycles_suspended", 0)
    
    def update_last_cycle_time(self):
        """Mettre à jour l'heure du dernier cycle"""
        self.state["last_cycle_time"] = datetime.now().isoformat()
        self._save_state()
    
    def get_last_cycle_time(self) -> Optional[str]:
        """Obtenir l'heure du dernier cycle"""
        return self.state.get("last_cycle_time")
    
    # --- Trade window helpers ---
    def get_current_trade_number(self) -> int:
        """Obtenir le numéro du trade courant (débute à 1)"""
        return int(self.state.get("current_trade_number", 1))
    
    def set_current_trade_number(self, n: int):
        """Définir le numéro du trade courant"""
        try:
            self.state["current_trade_number"] = int(max(1, n))
            self._save_state()
        except Exception as e:
            print(f"Erreur lors de la mise à jour du numéro de trade: {e}")
    
    def increment_trade_number(self):
        """Incrémente le numéro du trade courant"""
        try:
            self.state["current_trade_number"] = int(self.state.get("current_trade_number", 1)) + 1
            self._save_state()
        except Exception as e:
            print(f"Erreur lors de l'incrément du numéro de trade: {e}")
    
    def get_status_summary(self) -> Dict:
        """Obtenir un résumé de l'état"""
        return {
            "is_frozen": self.is_frozen(),
            "freeze_reason": self.get_freeze_reason(),
            "freeze_timestamp": self.get_freeze_timestamp(),
            "last_cycle_time": self.get_last_cycle_time(),
            "cycles_suspended": self.get_suspended_cycles(),
            "current_trade_number": self.get_current_trade_number()
        }

# Instance globale du gestionnaire d'état
robot_state_manager = RobotStateManager()
