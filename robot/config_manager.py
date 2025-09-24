#!/usr/bin/env python3
"""
Engine Configuration Manager
Tool to easily configure and test engine parameters
"""
import os
import sys
from dotenv import load_dotenv, set_key
from datetime import datetime

def load_current_config():
    """Load current configuration from .env"""
    load_dotenv()
    
    return {
        'cycle_duration': int(os.getenv('CYCLE_DURATION', 1440)),
        'portfolio_size': int(os.getenv('PORTFOLIO_SIZE', 10)),
        'allocation_percentage': float(os.getenv('ALLOCATION_PERCENTAGE', 0.8))
    }

def save_config(config):
    """Save configuration to .env file"""
    env_file = '.env'
    
    set_key(env_file, 'CYCLE_DURATION', str(config['cycle_duration']))
    set_key(env_file, 'PORTFOLIO_SIZE', str(config['portfolio_size']))
    set_key(env_file, 'ALLOCATION_PERCENTAGE', str(config['allocation_percentage']))
    
    print("✅ Configuration saved to .env")

def display_config(config):
    """Display current configuration"""
    print("📋 CURRENT ENGINE CONFIGURATION")
    print("=" * 50)
    
    # Cycle settings
    hours = config['cycle_duration'] / 60
    print(f"🔄 Cycle Duration:")
    print(f"   {config['cycle_duration']} minutes ({hours:.1f} hours)")
    
    # No restart settings
    
    # Portfolio settings
    print(f"\\n💼 Portfolio Settings:")
    print(f"   Portfolio Size: {config['portfolio_size']} positions")
    print(f"   Allocation: {config['allocation_percentage']*100:.0f}% crypto, {(1-config['allocation_percentage'])*100:.0f}% BNB")

def get_preset_configurations():
    """Get preset configurations for different strategies"""
    return {
        'aggressive_daily': {
            'name': 'Aggressive Daily (24h cycles)',
            'cycle_duration': 1440,
            'portfolio_size': 10,
            'allocation_percentage': 0.8
        },
        'optimal_21day': {
            'name': 'Optimal 21-Day (24h cycles)',
            'cycle_duration': 1440,
            'portfolio_size': 10,
            'allocation_percentage': 0.8
        },
        'conservative_monthly': {
            'name': 'Conservative Monthly (24h cycles)',
            'cycle_duration': 1440,
            'portfolio_size': 10,
            'allocation_percentage': 0.8
        },
        'high_frequency': {
            'name': 'High Frequency (4h cycles)',
            'cycle_duration': 240,
            'portfolio_size': 10,
            'allocation_percentage': 0.8
        },
        'low_frequency': {
            'name': 'Low Frequency (3-day cycles)',
            'cycle_duration': 4320,
            'portfolio_size': 10,
            'allocation_percentage': 0.8
        }
    }

def interactive_config():
    """Interactive configuration setup"""
    print("🛠️  INTERACTIVE ENGINE CONFIGURATION")
    print("=" * 50)
    
    current_config = load_current_config()
    
    print("\\n1. Choose from presets or customize:")
    print("   1) Aggressive Daily")
    print("   2) Optimal 21-Day (recommended)")
    print("   3) Conservative Monthly")
    print("   4) High Frequency")
    print("   5) Low Frequency")
    print("   6) Custom configuration")
    print("   7) Show current config and exit")
    
    choice = input("\\nSelect option (1-7): ")
    
    if choice == '7':
        display_config(current_config)
        return
    
    presets = get_preset_configurations()
    preset_keys = ['aggressive_daily', 'optimal_21day', 'conservative_monthly', 'high_frequency', 'low_frequency']

    if choice in ['1', '2', '3', '4', '5']:
        preset_key = preset_keys[int(choice) - 1]
        preset = presets[preset_key]

        print(f"\n📋 Selected: {preset['name']}")

        new_config = current_config.copy()
        new_config.update({
            'cycle_duration': preset['cycle_duration'],
            'portfolio_size': preset['portfolio_size'],
            'allocation_percentage': preset['allocation_percentage']
        })
        
    elif choice == '6':
        print("\n🛠️  CUSTOM CONFIGURATION")
        new_config = current_config.copy()

        # Cycle duration
        print(f"\nCycle Duration (current: {current_config['cycle_duration']} minutes)")
        cycle_input = input(f"Enter new cycle duration in minutes (or press Enter to keep {current_config['cycle_duration']}): ")
        if cycle_input.strip():
            new_config['cycle_duration'] = int(cycle_input)

        # Portfolio size
        print(f"\nPortfolio Size (current: {current_config['portfolio_size']})")
        size_input = input(f"Enter portfolio size (or press Enter to keep {current_config['portfolio_size']}): ")
        if size_input.strip():
            new_config['portfolio_size'] = int(size_input)

        # Allocation percentage
        print(f"\nAllocation Percentage (current: {current_config['allocation_percentage']*100:.0f}%)")
        alloc_input = input(f"Enter allocation percentage as decimal (or press Enter to keep {current_config['allocation_percentage']}): ")
        if alloc_input.strip():
            new_config['allocation_percentage'] = float(alloc_input)
    
    else:
        print("Invalid choice")
        return
    
    # Show new configuration
    print("\\n📋 NEW CONFIGURATION:")
    display_config(new_config)
    
    # Confirm save
    save_confirm = input("\\nSave this configuration? (y/n): ")
    if save_confirm.lower() in ['y', 'yes']:
        save_config(new_config)
        print("\\n🎯 Configuration updated!")
        print("   You can now run: python parameterized_engine.py")
    else:
        print("Configuration not saved")

def test_configuration():
    """Test current configuration parameters"""
    config = load_current_config()
    
    print("🧪 CONFIGURATION TEST")
    print("=" * 50)
    
    display_config(config)
    
    # Only show cycle duration, portfolio size, allocation
    cycle_hours = config['cycle_duration'] / 60
    print("\n⏰ TIMING ANALYSIS:")
    print(f"   Each cycle: {cycle_hours:.1f} hours")
    print(f"   Cycles per day: {24 / cycle_hours:.1f}")
    print("\n✅ Configuration test complete")

def main():
    """Main configuration manager"""
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            test_configuration()
        elif sys.argv[1] == 'show':
            display_config(load_current_config())
        else:
            print("Usage: python config_manager.py [test|show]")
    else:
        interactive_config()

if __name__ == "__main__":
    main()
