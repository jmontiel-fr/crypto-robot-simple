# 🚀 Crypto Trading Simulator - Complete Guide

## Overview

The Crypto Trading Simulator is a comprehensive backtesting system for cryptocurrency trading strategies with realistic 1.2x performance targets (20% returns). It features modern CSV-based simulation generation, calibration profiles, and automated execution.

## ⚡ Quick Start

### Instant Simulation Launch (Recommended)
```bash
# Quick test - 3 simulations (7, 14, 21 days) - Ready in seconds!
python generate_simulations.py --quick

# Comprehensive test - 6 simulations with different profiles and periods
python generate_simulations.py --comprehensive
```

That's it! The script automatically:
1. ✅ Creates optimized simulation templates
2. ✅ Validates all parameters
3. ✅ Creates simulations in database
4. ✅ Launches simulation execution
5. ✅ Cleans up temporary files

### Traditional CSV Approach
```bash
# List available templates
python generate_simulations.py --list-templates

# Use default template (simulations_templates/simulations_template.csv)
python generate_simulations.py --list
python generate_simulations.py

# Use specific templates
python generate_simulations.py --csv simulations_templates/simulations_template_comprehensive.csv

# Preview simulations first
python generate_simulations.py --list --csv simulations_templates/simulations_template.csv

# Validate without creating
python generate_simulations.py --dry-run --csv simulations_templates/simulations_template.csv
```

## 📊 Available Templates

### Built-in Templates (Auto-Generated)
- **Quick Template** (`--quick`): 3 simulations for rapid testing
- **Comprehensive Template** (`--comprehensive`): 6 simulations with multiple profiles

### CSV Templates (in `simulations_templates/` directory)
- **`simulations_template.csv`**: 15 standard simulations (7-90 days, $25-$500)
- **`simulations_template_comprehensive.csv`**: 41 comprehensive simulations (all combinations)
- **`simulations_template_quick.csv`**: 9 quick validation simulations
- **`simulations_template_usdc_protection.csv`**: 4 USDC protection simulations

### List Available Templates
```bash
# See all available templates
python generate_simulations.py --list-templates
```

### CSV Format
```csv
simulation_name,start_date,duration_days,cycle_duration_minutes,starting_capital,strategy,calibration_profile,data_source
1.2x Performance Target,2025-02-01,30,1440,100,daily_rebalance,final_1_2x_realistic,binance_historical
```

**Required Fields:**
- `simulation_name`: Unique identifier
- `start_date`: YYYY-MM-DD format
- `duration_days`: 1-365 days
- `starting_capital`: Amount in USD

**Optional Fields (with defaults):**
- `cycle_duration_minutes`: 1440 (24 hours)
- `strategy`: daily_rebalance
- `calibration_profile`: final_1_2x_realistic
- `data_source`: binance_historical

## ⚙️ Calibration Profiles

### Primary 1.2x Profile (Recommended)
- **`final_1_2x_realistic`**: 19.5% - 20.5% return (~$120 from $100)

### Risk-Based Profiles
- **`conservative_realistic`**: 15% - 35% return (Low risk)
- **`moderate_realistic`**: 35% - 65% return (Balanced)
- **`aggressive_realistic`**: 65% - 100% return (High risk)

### Market Condition Profiles
- **`bear_market_defensive`**: 5% - 25% return (Defensive)
- **`high_volatility_scalping`**: 45% - 75% return (Volatile markets)
- **`none`**: Original performance (No calibration)

### Profile Selection Guide
- **For Exact 1.2x Performance**: Use `final_1_2x_realistic` (19.5-20.5%)
- **For Maximum Returns**: Use `aggressive_realistic` (65-100%)
- **For Balanced Trading**: Use `moderate_realistic` (35-65%)
- **For Conservative Approach**: Use `conservative_realistic` (15-35%)

## 🛠️ Command Reference

### One-Stop Commands
| Command           | Description      | Simulations | Duration   |
| ----------------- | ---------------- | ----------- | ---------- |
| `--quick`         | Quick test suite | 3           | ~2 minutes |
| `--comprehensive` | Full test suite  | 6           | ~5 minutes |

### Traditional Commands
| Command                | Description                      |
| ---------------------- | -------------------------------- |
| `--list-templates`     | List all available CSV templates |
| `--csv FILE --launch`  | Create from CSV and auto-launch  |
| `--csv FILE`           | Create from CSV only             |
| `--list --csv FILE`    | Preview simulations              |
| `--dry-run --csv FILE` | Validate without creating        |
| `--create-template`    | Generate new template            |

### Running Simulations
```bash
# Run all pending simulations
python run_pending_simulations.py

# Run limited batch
python run_pending_simulations.py --max 10

# List pending simulations
python run_pending_simulations.py --list
```

## 📈 Expected Performance

### Returns by Profile (from $100 starting capital)

| Profile                    | Target Return | Final Value | Risk Level |
| -------------------------- | ------------- | ----------- | ---------- |
| `final_1_2x_realistic`     | 19.5% - 20.5% | ~$120       | Moderate   |
| `conservative_realistic`   | 15% - 35%     | $115 - $135 | Low        |
| `moderate_realistic`       | 35% - 65%     | $135 - $165 | Balanced   |
| `aggressive_realistic`     | 65% - 100%    | $165 - $200 | High       |
| `bear_market_defensive`    | 5% - 25%      | $105 - $125 | Defensive  |
| `high_volatility_scalping` | 45% - 75%     | $145 - $175 | High       |

### Time Estimates
- **Per Simulation**: ~2 minutes average
- **10 Simulations**: ~20 minutes
- **50 Simulations**: ~100 minutes (1.7 hours)

## 🌐 Web Interface

After running simulations, monitor progress at:
- **Simulator List**: `https://crypto-robot.local:5000/simulator-list`
- **Real-time Updates**: Auto-refresh every 10 seconds
- **Performance Metrics**: Detailed results with fee calculations

## 🔧 Troubleshooting

### Common Issues

| Issue                       | Solution                                   |
| --------------------------- | ------------------------------------------ |
| "No simulations created"    | Check CSV format and required fields       |
| "Simulation already exists" | Use unique names or delete existing ones   |
| "Launch failed"             | Ensure `run_pending_simulations.py` exists |
| "Template not found"        | Use `--create-template` to generate one    |

### Validation Errors
- **Date format**: Must be YYYY-MM-DD
- **Duration**: 1-365 days maximum
- **Capital**: Must be positive number
- **Profile**: Must be valid calibration profile

### Debugging Steps
```bash
# 1. List available templates
python generate_simulations.py --list-templates

# 2. Validate template format
python generate_simulations.py --list --csv simulations_templates/your_template.csv

# 3. Test with dry run
python generate_simulations.py --dry-run --csv simulations_templates/your_template.csv

# 4. Check database connection
python -c "from src.database import get_db_manager; print(get_db_manager().get_database_info())"
```

## 💡 Best Practices

1. **Start Small**: Use `--quick` for initial testing
2. **Validate First**: Use `--dry-run` for new templates
3. **Monitor Resources**: Don't run too many simulations simultaneously
4. **Clean Names**: Use descriptive, unique simulation names
5. **Regular Testing**: Use `--quick` for regular validation

## 📊 Example Workflows

### Development Testing
```bash
# Quick validation during development
python generate_simulations.py --quick
```

### Performance Analysis
```bash
# Comprehensive testing for analysis
python generate_simulations.py --comprehensive
```

### Custom Scenarios
```bash
# Create custom template
python generate_simulations.py --create-template --template-output simulations_templates/my_tests.csv

# Edit simulations_templates/my_tests.csv with your scenarios

# Run custom simulations
python generate_simulations.py --csv simulations_templates/my_tests.csv --launch
```

### Preview Before Running
```bash
# Check what will be created
python generate_simulations.py --csv simulations_templates/my_template.csv --dry-run

# List simulations without creating
python generate_simulations.py --csv simulations_templates/my_template.csv --list
```

## 🗄️ Database Schema

### Simulation Table Fields
- `name` - Simulation identifier
- `start_date` - Start date
- `duration_days` - Length in days
- `cycle_length_minutes` - Trading cycle duration
- `starting_reserve` - Initial capital
- `calibration_profile` - Performance profile
- `data_source` - Price data source
- `status` - Current status (pending/running/completed)

## 📊 Data Sources

### Binance Historical (`binance_historical`) - Recommended
- Real historical price data from Binance
- High accuracy for realistic backtesting
- **Recommended for production simulations**

### Binance Live (`binance_api`)
- Live price data from Binance API
- Real-time simulation capability
- Requires active API connection

### Simulated (`simulated`)
- Generated synthetic price data
- Testing without market dependency
- Configurable volatility patterns

## 🎉 Ready to Start?

```bash
# Get started in 30 seconds!
python generate_simulations.py --quick
```

**The enhanced simulation generator handles everything automatically - from template creation to execution. Just run the command and watch your simulations come to life!**

---

*Complete Simulator Guide - All-in-One Documentation*
*Last Updated: February 2025*