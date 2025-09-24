#!/usr/bin/env python3
"""
Create Default Calibration Profiles

This script creates a set of default calibration profiles that can be used
immediately without needing real robot data. These are based on typical
crypto trading scenarios.
"""

import json
import os
from datetime import datetime, timedelta

def create_default_profiles():
    """Create default calibration profiles"""
    
    print("🔧 CREATING DEFAULT CALIBRATION PROFILES")
    print("=" * 50)
    
    profiles_dir = "calibration_profiles"
    if not os.path.exists(profiles_dir):
        os.makedirs(profiles_dir)
        print(f"📁 Created directory: {profiles_dir}")
    
    # Define default profiles
    profiles = [
        {
            'name': 'conservative_realistic',
            'description': 'Conservative crypto trading with strong risk management',
            'market_regime': 'sideways_market',
            'volatility_level': 'low',
            'expected_monthly_return': '15-35%',
            'risk_level': 'low',
            'parameters': {
                'market_timing_efficiency': 0.60,
                'daily_slippage': 0.006,
                'trading_fee': 0.001,
                'volatility_drag': 0.003,
                'max_daily_return': 0.025,
                'min_daily_return': -0.03
            },
            'performance_analysis': {
                'avg_daily_return': 0.008,
                'daily_return_std': 0.015,
                'max_daily_return': 0.025,
                'min_daily_return': -0.025,
                'positive_days_ratio': 0.65,
                'avg_trading_cost': 8.50,
                'total_return': 0.25,
                'total_cycles': 30
            }
        },
        {
            'name': 'moderate_realistic',
            'description': 'Balanced crypto trading with moderate risk',
            'market_regime': 'bull_market',
            'volatility_level': 'medium',
            'expected_monthly_return': '35-65%',
            'risk_level': 'medium',
            'parameters': {
                'market_timing_efficiency': 0.70,
                'daily_slippage': 0.004,
                'trading_fee': 0.001,
                'volatility_drag': 0.002,
                'max_daily_return': 0.035,
                'min_daily_return': -0.04
            },
            'performance_analysis': {
                'avg_daily_return': 0.015,
                'daily_return_std': 0.025,
                'max_daily_return': 0.045,
                'min_daily_return': -0.035,
                'positive_days_ratio': 0.73,
                'avg_trading_cost': 10.20,
                'total_return': 0.50,
                'total_cycles': 30
            }
        },
        {
            'name': 'aggressive_realistic',
            'description': 'Aggressive crypto trading in favorable conditions',
            'market_regime': 'bull_market',
            'volatility_level': 'high',
            'expected_monthly_return': '65-100%',
            'risk_level': 'high',
            'parameters': {
                'market_timing_efficiency': 0.80,
                'daily_slippage': 0.003,
                'trading_fee': 0.001,
                'volatility_drag': 0.001,
                'max_daily_return': 0.045,
                'min_daily_return': -0.05
            },
            'performance_analysis': {
                'avg_daily_return': 0.025,
                'daily_return_std': 0.035,
                'max_daily_return': 0.065,
                'min_daily_return': -0.045,
                'positive_days_ratio': 0.80,
                'avg_trading_cost': 12.80,
                'total_return': 0.85,
                'total_cycles': 30
            }
        },
        {
            'name': 'bear_market_defensive',
            'description': 'Defensive trading during bear market conditions',
            'market_regime': 'bear_market',
            'volatility_level': 'high',
            'expected_monthly_return': '5-25%',
            'risk_level': 'low',
            'parameters': {
                'market_timing_efficiency': 0.50,
                'daily_slippage': 0.008,
                'trading_fee': 0.001,
                'volatility_drag': 0.004,
                'max_daily_return': 0.020,
                'min_daily_return': -0.06
            },
            'performance_analysis': {
                'avg_daily_return': 0.005,
                'daily_return_std': 0.030,
                'max_daily_return': 0.035,
                'min_daily_return': -0.055,
                'positive_days_ratio': 0.55,
                'avg_trading_cost': 7.20,
                'total_return': 0.15,
                'total_cycles': 30
            }
        },
        {
            'name': 'high_volatility_scalping',
            'description': 'High-frequency trading in volatile conditions',
            'market_regime': 'sideways_market',
            'volatility_level': 'high',
            'expected_monthly_return': '45-75%',
            'risk_level': 'high',
            'parameters': {
                'market_timing_efficiency': 0.75,
                'daily_slippage': 0.005,
                'trading_fee': 0.001,
                'volatility_drag': 0.002,
                'max_daily_return': 0.040,
                'min_daily_return': -0.045
            },
            'performance_analysis': {
                'avg_daily_return': 0.018,
                'daily_return_std': 0.032,
                'max_daily_return': 0.055,
                'min_daily_return': -0.042,
                'positive_days_ratio': 0.70,
                'avg_trading_cost': 15.60,
                'total_return': 0.60,
                'total_cycles': 30
            }
        }
    ]
    
    created_profiles = []
    
    for profile_config in profiles:
        profile = create_profile_structure(profile_config)
        
        # Save profile
        filename = f"{profile_config['name']}.json"
        filepath = os.path.join(profiles_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(profile, f, indent=2)
            
            created_profiles.append(profile_config['name'])
            
            print(f"✅ Created: {profile_config['name']}")
            print(f"   Description: {profile_config['description']}")
            print(f"   Expected Return: {profile_config['expected_monthly_return']}")
            print(f"   Risk Level: {profile_config['risk_level']}")
            print(f"   File: {filepath}")
            print()
            
        except Exception as e:
            print(f"❌ Error creating {profile_config['name']}: {e}")
    
    print(f"🎉 CREATED {len(created_profiles)} DEFAULT PROFILES:")
    for name in created_profiles:
        print(f"   - {name}")
    
    print(f"\n💡 USAGE EXAMPLES:")
    print(f"   # Apply conservative profile to simulation")
    print(f"   python apply_calibration_profile.py --profile conservative_realistic")
    print(f"   ")
    print(f"   # Run fresh simulation with moderate profile")
    print(f"   python run_calibrated_simulation.py --profile moderate_realistic")
    print(f"   ")
    print(f"   # List all available profiles")
    print(f"   python apply_calibration_profile.py --list")
    
    return created_profiles

def create_profile_structure(config):
    """Create complete profile structure from config"""
    
    base_date = datetime.now() - timedelta(days=30)
    
    profile = {
        'profile_name': config['name'],
        'created_date': datetime.now().isoformat(),
        'version': '1.0',
        'profile_type': 'default',
        'description': config['description'],
        'based_on_data': {
            'start_date': base_date.isoformat(),
            'end_date': datetime.now().isoformat(),
            'analysis_days': 30,
            'real_cycles': 30,
            'market_conditions': config['market_regime'],
            'data_source': 'synthetic_realistic'
        },
        'performance_analysis': config['performance_analysis'],
        'calibration_parameters': config['parameters'],
        'market_conditions': {
            'market_regime': config['market_regime'],
            'volatility_level': config['volatility_level'],
            'trend_strength': abs(config['performance_analysis']['avg_daily_return']) / config['performance_analysis']['daily_return_std']
        },
        'expected_performance': {
            'monthly_return_range': config['expected_monthly_return'],
            'risk_level': config['risk_level'],
            'win_rate': config['performance_analysis']['positive_days_ratio'] * 100,
            'max_drawdown_estimate': abs(config['performance_analysis']['min_daily_return']) * 100
        },
        'metadata': {
            'robot_version': 'daily_rebalance_v1.0',
            'portfolio_size': 10,
            'starting_capital': 100.0,
            'trading_fee_env': 0.001,
            'data_quality': 'synthetic_high',
            'profile_category': 'default',
            'suitable_for': get_suitable_conditions(config),
            'not_suitable_for': get_unsuitable_conditions(config)
        },
        'usage_notes': {
            'best_market_conditions': config['market_regime'],
            'recommended_duration': '7-30 days',
            'minimum_capital': 50.0,
            'experience_level': get_experience_level(config['risk_level']),
            'monitoring_frequency': get_monitoring_frequency(config['risk_level'])
        }
    }
    
    return profile

def get_suitable_conditions(config):
    """Get suitable market conditions for profile"""
    
    conditions = []
    
    if config['market_regime'] == 'bull_market':
        conditions.extend(['rising_markets', 'positive_momentum', 'high_volume'])
    elif config['market_regime'] == 'bear_market':
        conditions.extend(['falling_markets', 'defensive_trading', 'capital_preservation'])
    else:
        conditions.extend(['sideways_markets', 'range_trading', 'volatility_harvesting'])
    
    if config['volatility_level'] == 'high':
        conditions.extend(['high_volatility', 'active_trading'])
    elif config['volatility_level'] == 'low':
        conditions.extend(['stable_markets', 'conservative_approach'])
    
    return conditions

def get_unsuitable_conditions(config):
    """Get unsuitable market conditions for profile"""
    
    conditions = []
    
    if config['risk_level'] == 'low':
        conditions.extend(['extreme_volatility', 'margin_trading', 'high_leverage'])
    elif config['risk_level'] == 'high':
        conditions.extend(['stable_markets', 'low_volatility', 'conservative_goals'])
    
    if config['market_regime'] == 'bull_market':
        conditions.extend(['bear_markets', 'sustained_downtrends'])
    elif config['market_regime'] == 'bear_market':
        conditions.extend(['bull_markets', 'aggressive_growth_goals'])
    
    return conditions

def get_experience_level(risk_level):
    """Get recommended experience level"""
    
    levels = {
        'low': 'beginner_to_intermediate',
        'medium': 'intermediate',
        'high': 'advanced'
    }
    
    return levels.get(risk_level, 'intermediate')

def get_monitoring_frequency(risk_level):
    """Get recommended monitoring frequency"""
    
    frequencies = {
        'low': 'weekly',
        'medium': 'daily',
        'high': 'multiple_times_daily'
    }
    
    return frequencies.get(risk_level, 'daily')

if __name__ == "__main__":
    create_default_profiles()