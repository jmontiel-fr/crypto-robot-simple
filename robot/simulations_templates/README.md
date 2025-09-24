# 📊 Simulation Templates

This directory contains CSV templates for generating cryptocurrency trading simulations.

## Available Templates

### 🎯 **simulations_template.csv** (Default)
- **15 simulations** - Standard testing suite
- **Duration**: 7-90 days
- **Capital**: $25-$500
- **Profiles**: All 9 calibration profiles
- **Best for**: General testing and validation

### 🔬 **simulations_template_comprehensive.csv**
- **41 simulations** - Complete testing matrix
- **Duration**: 7, 14, 30 days
- **Capital**: $50, $100, $500
- **Profiles**: Conservative, Moderate, Aggressive, Final 1.2x
- **Best for**: Comprehensive analysis and comparison

### ⚡ **simulations_template_quick.csv**
- **9 simulations** - Rapid validation
- **Duration**: 7 days
- **Capital**: $100
- **Profiles**: All 9 calibration profiles
- **Best for**: Quick testing and development

### 🛡️ **simulations_template_usdc_protection.csv**
- **4 simulations** - USDC protection testing
- **Duration**: 30 days
- **Capital**: $100-$500
- **Profiles**: Conservative realistic
- **Best for**: Stable coin protection strategies

## Usage

### List Available Templates
```bash
python generate_simulations.py --list-templates
```

### Use Default Template
```bash
python generate_simulations.py --list
python generate_simulations.py
```

### Use Specific Template
```bash
python generate_simulations.py --csv simulations_templates/simulations_template_comprehensive.csv
```

### Create Custom Template
```bash
python generate_simulations.py --create-template --template-output simulations_templates/my_custom.csv
```

## CSV Format

All templates use this format:

```csv
simulation_name,start_date,duration_days,cycle_duration_minutes,starting_capital,strategy,calibration_profile,data_source
My Simulation,2025-02-01,30,1440,100,daily_rebalance,final_1_2x_realistic,binance_historical
```

### Required Fields
- `simulation_name`: Unique identifier
- `start_date`: YYYY-MM-DD format
- `duration_days`: 1-365 days
- `starting_capital`: Amount in USD

### Optional Fields (with defaults)
- `cycle_duration_minutes`: 1440 (24 hours)
- `strategy`: daily_rebalance
- `calibration_profile`: final_1_2x_realistic
- `data_source`: binance_historical

## Calibration Profiles

- **`final_1_2x_realistic`**: 19.5-20.5% return (recommended)
- **`conservative_realistic`**: 15-35% return (low risk)
- **`moderate_realistic`**: 35-65% return (balanced)
- **`aggressive_realistic`**: 65-100% return (high risk)
- **`bear_market_defensive`**: 5-25% return (defensive)
- **`high_volatility_scalping`**: 45-75% return (volatile markets)
- **`precise_1_2x_realistic`**: 18-22% return (precise 1.2x)
- **`target_1_2x_realistic`**: 18-22% return (target 1.2x)
- **`none`**: Original performance (no calibration)

---

*For complete documentation, see [SIMULATOR_COMPLETE_GUIDE.md](../SIMULATOR_COMPLETE_GUIDE.md)*