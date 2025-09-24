# 🛠️ Development Tools

This folder contains development, experimental, and utility scripts that are not part of the core simulation system.

## 📁 Contents

### 🔧 Calibration Tools
- **`auto_calibrate_simulation.py`** - Auto-calibrates simulation constraints using real robot trading data
- **`create_calibration_profile.py`** - Creates custom calibration profiles from robot data
- **`create_default_calibration_profiles.py`** - Sets up default calibration profiles
- **`create_exact_1_2x_calibration.py`** - Creates precise 1.2x performance calibration
- **`create_final_1_2x_calibration.py`** - Final 1.2x calibration implementation
- **`create_precise_1_2x_calibration.py`** - Precise 1.2x calibration tuning
- **`create_target_1_2x_calibration.py`** - Target-based 1.2x calibration

### 🚀 Strategy Development
- **`create_advanced_rebalancing_engine.py`** - Advanced rebalancing strategy with volatility modes
- **`implement_realistic_sim1_factors.py`** - Implements realistic factors for simulation 1
- **`create_usdc_protection_template.py`** - Creates USDC protection strategy templates

### 🔍 Monitoring & Analysis
- **`simulation_calibration_monitor.py`** - Monitors simulation calibration performance
- **`simulation_logger_integration.py`** - Integrates advanced logging for simulations
- **`web_app_fees_display.py`** - Web interface for displaying trading fees

### 🌐 Infrastructure Tools
- **`generate_ec2_ssl_cert.py`** - Generates SSL certificates for EC2 deployment
- **`generate_ssl_cert.py`** - General SSL certificate generation
- **`migrate_database_schema.py`** - Database schema migration utilities

## ⚠️ Usage Notes

These tools are:
- **Experimental** - May require specific setup or data
- **Development-focused** - Not needed for normal simulation operations
- **Advanced** - Require understanding of the underlying system
- **Optional** - Core simulation system works without them

## 🎯 Core System

For normal simulation operations, use the main project files:
- `generate_simulations.py` - Main simulation generator
- `run_pending_simulations.py` - Simulation execution
- `app.py` - Web interface
- Templates in `simulations_templates/`

## 🧹 Project Cleanup

These tools were moved here during project cleanup to maintain a clean, production-ready main directory structure.

---

*These tools are preserved for development and experimentation but are not required for core functionality.*