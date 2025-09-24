#!/usr/bin/env python3
"""
Modern Simulation Generator with Calibration Profile Support

Generates multiple simulations from CSV templates with support for:
- Calibration profiles for realistic performance
- Modern daily rebalance strategy
- Flexible parameter configuration
- Batch simulation creation
"""

import os
import sys
import csv
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import get_db_manager, Simulation
from calibration_manager import get_calibration_manager

class ModernSimulationGenerator:
    """Modern simulation generator with calibration support"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.calibration_manager = get_calibration_manager()
        self.templates_dir = "simulations_templates"
        
    def load_simulations_from_csv(self, csv_file: str) -> List[Dict]:
        """Load simulation configurations from CSV file"""
        
        simulations = []
        
        if not os.path.exists(csv_file):
            print(f"❌ CSV file not found: {csv_file}")
            return simulations
        
        try:
            with open(csv_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        # Parse and validate simulation data
                        sim_data = self._parse_simulation_row(row, row_num)
                        if sim_data:
                            simulations.append(sim_data)
                    except Exception as e:
                        print(f"⚠️  Row {row_num}: Error parsing - {e}")
                        continue
            
            print(f"📊 Loaded {len(simulations)} valid simulations from {csv_file}")
            return simulations
            
        except Exception as e:
            print(f"❌ Error reading CSV file: {e}")
            return []
    
    def _parse_simulation_row(self, row: Dict, row_num: int) -> Optional[Dict]:
        """Parse and validate a single simulation row"""
        
        # Required fields
        required_fields = ['simulation_name', 'start_date', 'duration_days', 'starting_capital']
        for field in required_fields:
            if not row.get(field, '').strip():
                print(f"⚠️  Row {row_num}: Missing required field '{field}'")
                return None
        
        try:
            # Parse dates
            start_date = datetime.strptime(row['start_date'].strip(), '%Y-%m-%d')
            
            # Parse numeric values
            duration_days = int(row['duration_days'])
            starting_capital = float(row['starting_capital'])
            
            # Optional fields with defaults
            cycle_duration = int(row.get('cycle_duration_minutes', '1440'))  # 24 hours default
            strategy = row.get('strategy', 'daily_rebalance').strip()
            calibration_profile = row.get('calibration_profile', 'final_1_2x_realistic').strip()
            data_source = row.get('data_source', 'binance_historical').strip()
            
            # Validate calibration profile
            if calibration_profile and calibration_profile != 'none':
                available_profiles = [p['name'] for p in self.calibration_manager.get_available_profiles()]
                # Add new 1.2x calibration profiles
                default_profiles = ['conservative_realistic', 'moderate_realistic', 'aggressive_realistic', 
                                  'final_1_2x_realistic', 'target_1_2x_realistic', 'precise_1_2x_realistic']
                if calibration_profile not in available_profiles and calibration_profile not in default_profiles:
                    print(f"⚠️  Row {row_num}: Unknown calibration profile '{calibration_profile}', using 'final_1_2x_realistic'")
                    calibration_profile = 'final_1_2x_realistic'
            
            return {
                'simulation_name': row['simulation_name'].strip(),
                'start_date': start_date,
                'duration_days': duration_days,
                'cycle_duration_minutes': cycle_duration,
                'starting_capital': starting_capital,
                'strategy': strategy,
                'calibration_profile': calibration_profile,
                'data_source': data_source,
                'row_number': row_num
            }
            
        except ValueError as e:
            print(f"⚠️  Row {row_num}: Invalid data format - {e}")
            return None
        except Exception as e:
            print(f"⚠️  Row {row_num}: Parsing error - {e}")
            return None
    
    def list_simulations(self, csv_file: str):
        """List simulations from CSV without creating them"""
        
        simulations = self.load_simulations_from_csv(csv_file)
        
        if not simulations:
            print("❌ No valid simulations found")
            return
        
        print(f"\n📊 Found {len(simulations)} simulations in {csv_file}:")
        print("-" * 120)
        print(f"{'#':<3} {'Name':<30} {'Start Date':<12} {'Duration':<8} {'Capital':<10} {'Profile':<20} {'Strategy':<15}")
        print("-" * 120)
        
        for i, sim in enumerate(simulations, 1):
            print(f"{i:<3} {sim['simulation_name'][:29]:<30} {sim['start_date'].strftime('%Y-%m-%d'):<12} "
                  f"{sim['duration_days']:<8} ${sim['starting_capital']:<9.0f} {sim['calibration_profile']:<20} {sim['strategy']:<15}")
        
        print("-" * 120)
        
        # Show calibration profile summary
        profiles_used = set(sim['calibration_profile'] for sim in simulations)
        print(f"\n📋 Calibration Profiles Used:")
        for profile in sorted(profiles_used):
            count = sum(1 for sim in simulations if sim['calibration_profile'] == profile)
            profile_info = self.calibration_manager.get_profile_summary(profile)
            print(f"   • {profile}: {count} simulations ({profile_info['expected_return']})")
    
    def create_simulations(self, csv_file: str, dry_run: bool = False):
        """Create simulations from CSV file"""
        
        simulations = self.load_simulations_from_csv(csv_file)
        
        if not simulations:
            print("❌ No valid simulations to create")
            return
        
        if dry_run:
            print(f"\n🔍 DRY RUN MODE - No simulations will be created")
            self.list_simulations(csv_file)
            return
        
        print(f"\n🚀 Creating {len(simulations)} simulations...")
        
        session = self.db_manager.get_session()
        created_count = 0
        skipped_count = 0
        
        try:
            for sim_data in simulations:
                try:
                    # Check if simulation already exists
                    existing = session.query(Simulation).filter_by(
                        name=sim_data['simulation_name']
                    ).first()
                    
                    if existing:
                        print(f"⚠️  Skipped: '{sim_data['simulation_name']}' already exists")
                        skipped_count += 1
                        continue
                    
                    # Create new simulation
                    new_simulation = Simulation(
                        name=sim_data['simulation_name'],
                        start_date=sim_data['start_date'],
                        duration_days=sim_data['duration_days'],
                        cycle_length_minutes=sim_data['cycle_duration_minutes'],
                        starting_reserve=sim_data['starting_capital'],
                        data_source=sim_data['data_source'],
                        calibration_profile=sim_data['calibration_profile'],
                        status='pending',
                        created_at=datetime.now()
                    )
                    
                    session.add(new_simulation)
                    session.commit()
                    
                    print(f"✅ Created: '{sim_data['simulation_name']}' (Profile: {sim_data['calibration_profile']})")
                    created_count += 1
                    
                except Exception as e:
                    print(f"❌ Failed to create '{sim_data['simulation_name']}': {e}")
                    session.rollback()
                    continue
            
            print(f"\n📊 SUMMARY:")
            print(f"   ✅ Created: {created_count} simulations")
            print(f"   ⚠️  Skipped: {skipped_count} simulations (already exist)")
            print(f"   📋 Total: {len(simulations)} simulations processed")
            
        finally:
            session.close()
    
    def create_template_csv(self, output_file: str = 'simulations_templates/simulations_template_new.csv'):
        """Create a new template CSV with modern parameters"""
        
        # Get available calibration profiles
        available_profiles = self.calibration_manager.get_available_profiles()
        profile_names = [p['name'] for p in available_profiles]
        if not profile_names:
            profile_names = ['final_1_2x_realistic', 'conservative_realistic', 'moderate_realistic', 'aggressive_realistic']
        
        # Template data with 1.2x performance targets
        template_data = [
            {
                'simulation_name': '1.2x Performance Target - 30 Days',
                'start_date': '2025-02-01',
                'duration_days': 30,
                'cycle_duration_minutes': 1440,
                'starting_capital': 100,
                'strategy': 'daily_rebalance',
                'calibration_profile': 'final_1_2x_realistic',
                'data_source': 'binance_historical'
            },
            {
                'simulation_name': '1.2x Performance Target - 60 Days',
                'start_date': '2025-02-01',
                'duration_days': 60,
                'cycle_duration_minutes': 1440,
                'starting_capital': 200,
                'strategy': 'daily_rebalance',
                'calibration_profile': 'final_1_2x_realistic',
                'data_source': 'binance_historical'
            },
            {
                'simulation_name': '1.2x Performance Target - High Capital',
                'start_date': '2025-02-01',
                'duration_days': 30,
                'cycle_duration_minutes': 1440,
                'starting_capital': 500,
                'strategy': 'daily_rebalance',
                'calibration_profile': 'final_1_2x_realistic',
                'data_source': 'binance_historical'
            },
            {
                'simulation_name': 'Conservative 1.2x - Low Risk',
                'start_date': '2025-02-01',
                'duration_days': 30,
                'cycle_duration_minutes': 1440,
                'starting_capital': 100,
                'strategy': 'daily_rebalance',
                'calibration_profile': 'conservative_realistic',
                'data_source': 'binance_historical'
            },
            {
                'simulation_name': 'Moderate 1.2x - Balanced Risk',
                'start_date': '2025-02-01',
                'duration_days': 30,
                'cycle_duration_minutes': 1440,
                'starting_capital': 100,
                'strategy': 'daily_rebalance',
                'calibration_profile': 'moderate_realistic',
                'data_source': 'binance_historical'
            },
            {
                'simulation_name': 'Short Term 1.2x Test',
                'start_date': '2025-02-01',
                'duration_days': 7,
                'cycle_duration_minutes': 1440,
                'starting_capital': 50,
                'strategy': 'daily_rebalance',
                'calibration_profile': 'final_1_2x_realistic',
                'data_source': 'binance_historical'
            }
        ]
        
        # Write CSV file
        fieldnames = ['simulation_name', 'start_date', 'duration_days', 'cycle_duration_minutes', 
                     'starting_capital', 'strategy', 'calibration_profile', 'data_source']
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(template_data)
            
            print(f"✅ Created template CSV: {output_file}")
            print(f"📊 Contains {len(template_data)} example simulations")
            print(f"📋 Available calibration profiles: {', '.join(profile_names)}")
            
        except Exception as e:
            print(f"❌ Error creating template: {e}")

    def list_available_templates(self):
        """List all available CSV templates"""
        
        print("📋 AVAILABLE SIMULATION TEMPLATES")
        print("=" * 50)
        
        if not os.path.exists(self.templates_dir):
            print(f"❌ Templates directory not found: {self.templates_dir}")
            return
        
        templates = [f for f in os.listdir(self.templates_dir) if f.endswith('.csv')]
        
        if not templates:
            print(f"❌ No CSV templates found in {self.templates_dir}")
            return
        
        print(f"📊 Found {len(templates)} templates in {self.templates_dir}/:")
        print()
        
        for i, template in enumerate(sorted(templates), 1):
            template_path = os.path.join(self.templates_dir, template)
            
            # Get simulation count
            try:
                simulations = self.load_simulations_from_csv(template_path)
                sim_count = len(simulations)
                
                # Get profile summary
                if simulations:
                    profiles = set(sim['calibration_profile'] for sim in simulations)
                    profile_summary = f"{len(profiles)} profiles"
                else:
                    profile_summary = "No valid simulations"
                
                print(f"   {i:2}. {template}")
                print(f"       📊 {sim_count} simulations, {profile_summary}")
                print(f"       📁 {self.templates_dir}/{template}")
                print()
                
            except Exception as e:
                print(f"   {i:2}. {template}")
                print(f"       ❌ Error reading template: {e}")
                print()
        
        print("💡 Usage Examples:")
        print(f"   python generate_simulations.py --csv {self.templates_dir}/simulations_template.csv")
        print(f"   python generate_simulations.py --list --csv {self.templates_dir}/simulations_template_comprehensive.csv")

    def create_and_run_quick(self):
        """Create quick template and run simulations immediately"""
        print("🎯 QUICK SIMULATION LAUNCHER")
        print("=" * 40)
        
        # Create quick template
        template_file = "simulations_templates/simulations_template_auto_quick.csv"
        quick_template = [
            {
                'simulation_name': 'Quick Test - 7 Days',
                'start_date': '2025-02-01',
                'duration_days': 7,
                'cycle_duration_minutes': 1440,
                'starting_capital': 100,
                'strategy': 'daily_rebalance',
                'calibration_profile': 'final_1_2x_realistic',
                'data_source': 'binance_historical'
            },
            {
                'simulation_name': 'Quick Test - 14 Days',
                'start_date': '2024-12-01',
                'duration_days': 14,
                'cycle_duration_minutes': 1440,
                'starting_capital': 100,
                'strategy': 'daily_rebalance',
                'calibration_profile': 'final_1_2x_realistic',
                'data_source': 'binance_historical'
            },
            {
                'simulation_name': 'Quick Test - 21 Days',
                'start_date': '2024-11-01',
                'duration_days': 21,
                'cycle_duration_minutes': 1440,
                'starting_capital': 100,
                'strategy': 'daily_rebalance',
                'calibration_profile': 'final_1_2x_realistic',
                'data_source': 'binance_historical'
            }
        ]
        
        # Write template
        fieldnames = ['simulation_name', 'start_date', 'duration_days', 'cycle_duration_minutes', 
                     'starting_capital', 'strategy', 'calibration_profile', 'data_source']
        
        try:
            with open(template_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(quick_template)
            
            print(f"✅ Created quick template: {template_file}")
            
            # Run simulations
            print("\n🚀 Running simulations...")
            self.create_simulations(template_file)
            
            # Launch simulations
            print("\n🎮 Launching simulation execution...")
            self.launch_simulations()
            
            # Clean up
            try:
                os.remove(template_file)
                print(f"🧹 Cleaned up template: {template_file}")
            except:
                pass
                
        except Exception as e:
            print(f"❌ Error in quick launch: {e}")
    
    def create_and_run_comprehensive(self):
        """Create comprehensive template and run simulations"""
        print("🎯 COMPREHENSIVE SIMULATION LAUNCHER")
        print("=" * 50)
        
        template_file = "simulations_templates/simulations_template_auto_comprehensive.csv"
        comprehensive_template = [
            {
                'simulation_name': 'Comprehensive - Recent Bull',
                'start_date': '2025-02-01',
                'duration_days': 7,
                'cycle_duration_minutes': 1440,
                'starting_capital': 100,
                'strategy': 'daily_rebalance',
                'calibration_profile': 'final_1_2x_realistic',
                'data_source': 'binance_historical'
            },
            {
                'simulation_name': 'Comprehensive - Winter Rally',
                'start_date': '2024-12-15',
                'duration_days': 10,
                'cycle_duration_minutes': 1440,
                'starting_capital': 150,
                'strategy': 'daily_rebalance',
                'calibration_profile': 'moderate_realistic',
                'data_source': 'binance_historical'
            },
            {
                'simulation_name': 'Comprehensive - December Test',
                'start_date': '2024-12-01',
                'duration_days': 14,
                'cycle_duration_minutes': 1440,
                'starting_capital': 200,
                'strategy': 'daily_rebalance',
                'calibration_profile': 'final_1_2x_realistic',
                'data_source': 'binance_historical'
            },
            {
                'simulation_name': 'Comprehensive - November Test',
                'start_date': '2024-11-15',
                'duration_days': 14,
                'cycle_duration_minutes': 1440,
                'starting_capital': 200,
                'strategy': 'daily_rebalance',
                'calibration_profile': 'aggressive_realistic',
                'data_source': 'binance_historical'
            },
            {
                'simulation_name': 'Comprehensive - Stress Test',
                'start_date': '2024-11-01',
                'duration_days': 21,
                'cycle_duration_minutes': 1440,
                'starting_capital': 300,
                'strategy': 'daily_rebalance',
                'calibration_profile': 'final_1_2x_realistic',
                'data_source': 'binance_historical'
            },
            {
                'simulation_name': 'Comprehensive - Extended Test',
                'start_date': '2024-10-15',
                'duration_days': 30,
                'cycle_duration_minutes': 1440,
                'starting_capital': 500,
                'strategy': 'daily_rebalance',
                'calibration_profile': 'conservative_realistic',
                'data_source': 'binance_historical'
            }
        ]
        
        # Write and run
        fieldnames = ['simulation_name', 'start_date', 'duration_days', 'cycle_duration_minutes', 
                     'starting_capital', 'strategy', 'calibration_profile', 'data_source']
        
        try:
            with open(template_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(comprehensive_template)
            
            print(f"✅ Created comprehensive template: {template_file}")
            print("\n🚀 Running simulations...")
            self.create_simulations(template_file)
            
            print("\n🎮 Launching simulation execution...")
            self.launch_simulations()
            
            # Clean up
            try:
                os.remove(template_file)
                print(f"🧹 Cleaned up template: {template_file}")
            except:
                pass
                
        except Exception as e:
            print(f"❌ Error in comprehensive launch: {e}")
    
    def launch_simulations(self):
        """Launch pending simulations"""
        try:
            import subprocess
            
            # Check if we have the simulation runner
            if os.path.exists("run_pending_simulations.py"):
                print("🚀 Starting simulation execution...")
                result = subprocess.run([sys.executable, "run_pending_simulations.py"], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ Simulations launched successfully!")
                    if result.stdout:
                        print(result.stdout)
                else:
                    print("⚠️ Simulation launch had issues:")
                    if result.stderr:
                        print(result.stderr)
            else:
                print("ℹ️ Simulation runner not found. Simulations created but not launched.")
                print("   Run 'python run_pending_simulations.py' to execute them.")
                
        except Exception as e:
            print(f"⚠️ Could not launch simulations: {e}")
            print("   Simulations created successfully. Launch manually if needed.")

def main():
    parser = argparse.ArgumentParser(description='Modern Simulation Generator with Calibration Support')
    parser.add_argument('--csv', default='simulations_templates/simulations_template.csv', 
                       help='CSV file with simulation configurations')
    parser.add_argument('--list', action='store_true',
                       help='List simulations without creating them')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be created without actually creating')
    parser.add_argument('--create-template', action='store_true',
                       help='Create a new template CSV file')
    parser.add_argument('--template-output', default='simulations_templates/simulations_template_new.csv',
                       help='Output file for new template')
    parser.add_argument('--quick', action='store_true',
                       help='Create quick template and run simulations immediately')
    parser.add_argument('--comprehensive', action='store_true',
                       help='Create comprehensive template and run simulations immediately')
    parser.add_argument('--launch', action='store_true',
                       help='Launch pending simulations after creating them')
    parser.add_argument('--list-templates', action='store_true',
                       help='List all available CSV templates')
    
    args = parser.parse_args()
    
    generator = ModernSimulationGenerator()
    
    if args.list_templates:
        generator.list_available_templates()
    elif args.quick:
        generator.create_and_run_quick()
    elif args.comprehensive:
        generator.create_and_run_comprehensive()
    elif args.create_template:
        generator.create_template_csv(args.template_output)
    elif args.list:
        generator.list_simulations(args.csv)
    elif args.dry_run:
        generator.create_simulations(args.csv, dry_run=True)
    else:
        generator.create_simulations(args.csv, dry_run=False)
        # Always launch simulations after creating them (unless it's a dry run)
        generator.launch_simulations()

if __name__ == '__main__':
    main()