#!/usr/bin/env python3
"""
Calibration Manager

Manages calibration profiles for the simulation engine, including loading,
applying, and integrating with the web interface.
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class CalibrationManager:
    """Manages calibration profiles for simulations"""
    
    def __init__(self):
        self.profiles_dir = os.getenv('CALIBRATION_PROFILES_DIR', 'calibration_profiles')
        self.default_profile = os.getenv('DEFAULT_CALIBRATION_PROFILE', 'live_robot_performance')
        self.enable_calibration = os.getenv('ENABLE_CALIBRATION', 'true').lower() == 'true'
        
        self._ensure_profiles_directory()
    
    def _ensure_profiles_directory(self):
        """Ensure calibration profiles directory exists"""
        if not os.path.exists(self.profiles_dir):
            os.makedirs(self.profiles_dir)
    
    def get_available_profiles(self) -> List[Dict]:
        """Get list of available calibration profiles"""
        
        profiles = []
        
        if not os.path.exists(self.profiles_dir):
            return profiles
        
        for filename in os.listdir(self.profiles_dir):
            if filename.endswith('.json'):
                try:
                    profile_path = os.path.join(self.profiles_dir, filename)
                    with open(profile_path, 'r') as f:
                        profile = json.load(f)
                    
                    # Skip placeholder profiles
                    if profile.get('status') == 'insufficient_data':
                        continue
                    
                    # Extract key information
                    profile_info = {
                        'name': profile['profile_name'],
                        'description': profile.get('description', 'Custom calibration profile'),
                        'expected_return': profile.get('expected_performance', {}).get('monthly_return_range', 'Unknown'),
                        'risk_level': profile.get('expected_performance', {}).get('risk_level', 'medium'),
                        'market_regime': profile.get('market_conditions', {}).get('market_regime', 'unknown'),
                        'created_date': profile.get('created_date', ''),
                        'profile_type': profile.get('profile_type', 'custom'),
                        'file_path': profile_path
                    }
                    
                    profiles.append(profile_info)
                    
                except Exception as e:
                    print(f"Warning: Could not load profile {filename}: {e}")
                    continue
        
        # Sort by name
        profiles.sort(key=lambda x: x['name'])
        
        return profiles
    
    def get_profile_for_web_form(self) -> List[Tuple[str, str]]:
        """Get profiles formatted for web form dropdown"""
        
        profiles = self.get_available_profiles()
        
        # Format for web form: (value, display_text)
        form_options = [('none', 'No Calibration (Original Performance)')]
        
        for profile in profiles:
            display_text = f"{profile['name']} ({profile['expected_return']}, {profile['risk_level']} risk)"
            form_options.append((profile['name'], display_text))
        
        return form_options
    
    def load_profile(self, profile_name: str) -> Optional[Dict]:
        """Load a specific calibration profile"""
        
        if not profile_name or profile_name == 'none':
            return None
        
        profile_path = os.path.join(self.profiles_dir, f"{profile_name}.json")
        
        if not os.path.exists(profile_path):
            print(f"Warning: Calibration profile not found: {profile_name}")
            return None
        
        try:
            with open(profile_path, 'r') as f:
                profile = json.load(f)
            return profile
        except Exception as e:
            print(f"Error loading calibration profile {profile_name}: {e}")
            return None
    
    def get_default_profile(self) -> Optional[Dict]:
        """Get the default calibration profile"""
        
        if not self.enable_calibration:
            return None
        
        return self.load_profile(self.default_profile)
    
    def apply_profile_to_simulation_data(self, cycles_data: List[Dict], profile_name: str, starting_capital: float) -> Tuple[List[Dict], Dict]:
        """
        Apply calibration profile to simulation cycle data
        
        Args:
            cycles_data: List of simulation cycle data
            profile_name: Name of calibration profile to apply
            starting_capital: Starting capital amount
            
        Returns:
            Tuple of (modified_cycles_data, calibration_info)
        """
        
        if not profile_name or profile_name == 'none':
            return cycles_data, {'profile_applied': False}
        
        profile = self.load_profile(profile_name)
        if not profile:
            return cycles_data, {'profile_applied': False, 'error': 'Profile not found'}
        
        try:
            # Get calibration parameters
            params = profile['calibration_parameters']
            
            # Apply calibration to each cycle
            modified_cycles = []
            current_capital = starting_capital
            total_trading_costs = 0
            
            for i, cycle_data in enumerate(cycles_data):
                # Get original return
                if i == 0:
                    original_return = (cycle_data['total_value'] - starting_capital) / starting_capital
                else:
                    prev_value = cycles_data[i-1]['total_value']
                    original_return = (cycle_data['total_value'] - prev_value) / prev_value
                
                # Apply calibration parameters
                timing_adjusted = original_return * params['market_timing_efficiency']
                
                # Cap daily return
                capped_return = min(params['max_daily_return'], 
                                  max(params['min_daily_return'], timing_adjusted))
                
                # Subtract costs
                after_costs = (capped_return 
                             - params['daily_slippage']
                             - params['volatility_drag']
                             - (params['trading_fee'] * 2))  # Buy + sell
                
                # Calculate new capital
                new_capital = current_capital * (1 + after_costs)
                
                # Track costs
                daily_cost = current_capital * params['trading_fee'] * 2
                total_trading_costs += daily_cost
                
                # Create modified cycle data
                modified_cycle = cycle_data.copy()
                modified_cycle['total_value'] = new_capital
                modified_cycle['portfolio_value'] = new_capital * 0.95
                modified_cycle['bnb_reserve'] = new_capital * 0.05
                modified_cycle['trading_costs'] = daily_cost
                modified_cycle['calibration_applied'] = True
                modified_cycle['calibration_profile'] = profile_name
                
                modified_cycles.append(modified_cycle)
                current_capital = new_capital
            
            # Calculate calibration info
            final_return = ((current_capital - starting_capital) / starting_capital) * 100
            original_final = ((cycles_data[-1]['total_value'] - starting_capital) / starting_capital) * 100
            
            calibration_info = {
                'profile_applied': True,
                'profile_name': profile_name,
                'original_return': original_final,
                'calibrated_return': final_return,
                'adjustment': final_return - original_final,
                'total_trading_costs': total_trading_costs,
                'parameters_used': params
            }
            
            return modified_cycles, calibration_info
            
        except Exception as e:
            print(f"Error applying calibration profile {profile_name}: {e}")
            return cycles_data, {'profile_applied': False, 'error': str(e)}
    
    def get_profile_summary(self, profile_name: str) -> Dict:
        """Get summary information about a profile"""
        
        if not profile_name or profile_name == 'none':
            return {
                'name': 'none',
                'description': 'No calibration applied',
                'expected_return': 'Original simulation performance',
                'risk_level': 'varies'
            }
        
        profile = self.load_profile(profile_name)
        if not profile:
            return {
                'name': profile_name,
                'description': 'Profile not found',
                'expected_return': 'Unknown',
                'risk_level': 'unknown'
            }
        
        return {
            'name': profile['profile_name'],
            'description': profile.get('description', 'Custom calibration profile'),
            'expected_return': profile.get('expected_performance', {}).get('monthly_return_range', 'Unknown'),
            'risk_level': profile.get('expected_performance', {}).get('risk_level', 'medium'),
            'market_regime': profile.get('market_conditions', {}).get('market_regime', 'unknown'),
            'created_date': profile.get('created_date', '')[:10] if profile.get('created_date') else 'Unknown'
        }
    
    def validate_profile_compatibility(self, profile_name: str, simulation_params: Dict) -> Dict:
        """Validate if profile is compatible with simulation parameters"""
        
        if not profile_name or profile_name == 'none':
            return {'compatible': True, 'warnings': []}
        
        profile = self.load_profile(profile_name)
        if not profile:
            return {'compatible': False, 'warnings': ['Profile not found']}
        
        warnings = []
        
        # Check duration compatibility
        duration_days = simulation_params.get('duration_days', 30)
        if duration_days > 60:
            warnings.append('Profile optimized for shorter durations (30 days)')
        
        # Check capital compatibility
        starting_capital = simulation_params.get('starting_capital', 100)
        min_capital = profile.get('metadata', {}).get('minimum_capital', 50)
        if starting_capital < min_capital:
            warnings.append(f'Recommended minimum capital: ${min_capital}')
        
        # Check market regime compatibility
        current_date = datetime.now()
        profile_market = profile.get('market_conditions', {}).get('market_regime', 'unknown')
        
        # Add market regime warning (simplified)
        if profile_market == 'bear_market':
            warnings.append('Profile optimized for bear market conditions')
        elif profile_market == 'bull_market':
            warnings.append('Profile optimized for bull market conditions')
        
        return {
            'compatible': True,
            'warnings': warnings,
            'profile_market': profile_market,
            'expected_return': profile.get('expected_performance', {}).get('monthly_return_range', 'Unknown')
        }

# Global calibration manager instance
calibration_manager = CalibrationManager()

def get_calibration_manager() -> CalibrationManager:
    """Get global calibration manager instance"""
    return calibration_manager