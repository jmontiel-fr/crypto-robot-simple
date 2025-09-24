#!/usr/bin/env python3
"""
Create Calibration Profile from Real Robot Data

This script analyzes real robot performance and creates a calibration profile
that can be saved and reused for future simulations.
"""

from src.database import DatabaseManager, TradingCycle, Portfolio
import json
import os
import statistics
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class CalibrationProfileCreator:
    """Creates calibration profiles from real robot data"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.profiles_dir = "calibration_profiles"
        self._ensure_profiles_directory()
    
    def _ensure_profiles_directory(self):
        """Ensure calibration profiles directory exists"""
        if not os.path.exists(self.profiles_dir):
            os.makedirs(self.profiles_dir)
            print(f"📁 Created calibration profiles directory: {self.profiles_dir}")
    
    def create_profile_from_robot_data(self, profile_name: str, analysis_days: int = 14):
        """
        Create calibration profile from real robot trading data
        
        Args:
            profile_name: Name for the calibration profile
            analysis_days: Number of recent days to analyze
        """
        
        print("🔧 CREATING CALIBRATION PROFILE FROM ROBOT DATA")
        print("=" * 55)
        print(f"   Profile Name: {profile_name}")
        print(f"   Analysis Period: Last {analysis_days} days")
        print()
        
        session = self.db_manager.get_session()
        
        try:
            # Get real robot data
            robot_data = self._collect_robot_data(session, analysis_days)
            
            if not robot_data['sufficient_data']:
                return self._handle_insufficient_data(robot_data, profile_name)
            
            # Analyze performance
            performance_analysis = self._analyze_robot_performance(robot_data)
            
            # Calculate calibration parameters
            calibration_params = self._calculate_calibration_parameters(performance_analysis)
            
            # Detect market conditions
            market_conditions = self._detect_market_conditions(performance_analysis)
            
            # Create profile structure
            profile = self._create_profile_structure(
                profile_name, robot_data, performance_analysis, 
                calibration_params, market_conditions
            )
            
            # Save profile
            profile_path = self._save_profile(profile)
            
            # Validate profile
            validation_results = self._validate_profile(profile)
            
            print(f"✅ CALIBRATION PROFILE CREATED SUCCESSFULLY!")
            print(f"   Profile saved to: {profile_path}")
            print(f"   Quality rating: {validation_results['quality_rating']}")
            print(f"   Expected monthly return: {validation_results['expected_monthly_return']}")
            
            return {
                'success': True,
                'profile_path': profile_path,
                'profile': profile,
                'validation': validation_results
            }
            
        except Exception as e:
            print(f"❌ Error creating calibration profile: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
        finally:
            session.close()
    
    def _collect_robot_data(self, session, analysis_days: int):
        """Collect real robot trading data"""
        
        cutoff_date = datetime.now() - timedelta(days=analysis_days)
        
        # Get trading cycles
        trading_cycles = session.query(TradingCycle).filter(
            TradingCycle.cycle_date >= cutoff_date
        ).order_by(TradingCycle.cycle_date).all()
        
        # Get portfolio data
        portfolio = session.query(Portfolio).first()
        
        print(f"📊 ROBOT DATA COLLECTION:")
        print(f"   Trading cycles found: {len(trading_cycles)}")
        print(f"   Date range: {cutoff_date.strftime('%Y-%m-%d')} to now")
        
        # CRITICAL VALIDATION: Check if data is from real trading
        self._validate_real_trading_data(trading_cycles)
        
        sufficient_data = len(trading_cycles) >= 7
        
        if sufficient_data:
            print(f"   ✅ Sufficient data for profile creation")
        else:
            print(f"   ❌ Insufficient data - need {7 - len(trading_cycles)} more cycles")
        
        return {
            'trading_cycles': trading_cycles,
            'portfolio': portfolio,
            'sufficient_data': sufficient_data,
            'analysis_period': analysis_days,
            'start_date': cutoff_date,
            'end_date': datetime.now()
        }
    
    def _validate_real_trading_data(self, trading_cycles):
        """Validate that data comes from real trading, not dry-run or simulation"""
        
        print(f"\n⚠️  VALIDATING DATA SOURCE:")
        print("-" * 30)
        
        # Check environment variables
        import os
        dry_run_mode = os.getenv('ROBOT_DRY_RUN', 'true').lower() == 'true'
        calibration_enabled = os.getenv('ENABLE_CALIBRATION', 'true').lower() == 'true'
        
        if dry_run_mode:
            print(f"   ❌ ERROR: ROBOT_DRY_RUN=true detected!")
            print(f"   Dry-run data cannot be used for calibration (circular logic)")
            print(f"   Set ROBOT_DRY_RUN=false and run live trading to collect real data")
            raise ValueError("Cannot create calibration profile from dry-run data")
        
        if calibration_enabled:
            print(f"   ⚠️  WARNING: ENABLE_CALIBRATION=true detected!")
            print(f"   This means recent data may already be calibrated")
            print(f"   For best results, disable calibration during data collection")
            print(f"   Set ENABLE_CALIBRATION=false and collect fresh real trading data")
            
            # Ask user if they want to continue
            response = input(f"\n   Continue with potentially calibrated data? (y/N): ").lower()
            if response != 'y':
                raise ValueError("Calibration cancelled - collect fresh uncalibrated data")
        
        # Check for simulation data patterns (unrealistic returns)
        if trading_cycles:
            returns = []
            for i in range(1, len(trading_cycles)):
                prev_value = trading_cycles[i-1].total_value
                curr_value = trading_cycles[i].total_value
                if prev_value > 0:
                    daily_return = (curr_value - prev_value) / prev_value
                    returns.append(abs(daily_return))
            
            if returns:
                avg_abs_return = sum(returns) / len(returns)
                if avg_abs_return > 0.10:  # >10% average daily return is suspicious
                    print(f"   ⚠️  WARNING: Suspiciously high returns detected!")
                    print(f"   Average daily return: {avg_abs_return:.1%}")
                    print(f"   This may indicate simulation or uncalibrated data")
                    
                    response = input(f"   Continue anyway? (y/N): ").lower()
                    if response != 'y':
                        raise ValueError("Calibration cancelled - data appears unrealistic")
        
        print(f"   ✅ Data source validation passed")
        print(f"   Using real trading data for calibration")
    
    def _analyze_robot_performance(self, robot_data):
        """Analyze robot performance patterns"""
        
        print(f"\n🔍 ANALYZING ROBOT PERFORMANCE:")
        print("-" * 35)
        
        cycles = robot_data['trading_cycles']
        
        # Calculate daily returns
        daily_returns = []
        trading_costs = []
        portfolio_values = []
        
        for i, cycle in enumerate(cycles[1:], 1):
            prev_cycle = cycles[i-1]
            
            # Daily return
            daily_return = (cycle.total_value - prev_cycle.total_value) / prev_cycle.total_value
            daily_returns.append(daily_return)
            
            # Trading costs (estimate from actions)
            actions = cycle.actions_taken or []
            cost = len(actions) * float(os.getenv('TRADING_FEE', '0.001')) * cycle.total_value
            trading_costs.append(cost)
            
            portfolio_values.append(cycle.total_value)
        
        # Calculate statistics
        if daily_returns:
            avg_daily_return = statistics.mean(daily_returns)
            daily_return_std = statistics.stdev(daily_returns) if len(daily_returns) > 1 else 0
            max_daily_return = max(daily_returns)
            min_daily_return = min(daily_returns)
            positive_days = sum(1 for r in daily_returns if r > 0)
            positive_ratio = positive_days / len(daily_returns)
        else:
            avg_daily_return = daily_return_std = max_daily_return = min_daily_return = positive_ratio = 0
        
        avg_trading_cost = statistics.mean(trading_costs) if trading_costs else 0
        
        # Calculate total performance
        if portfolio_values:
            total_return = (portfolio_values[-1] - portfolio_values[0]) / portfolio_values[0]
        else:
            total_return = 0
        
        analysis = {
            'avg_daily_return': avg_daily_return,
            'daily_return_std': daily_return_std,
            'max_daily_return': max_daily_return,
            'min_daily_return': min_daily_return,
            'positive_days_ratio': positive_ratio,
            'avg_trading_cost': avg_trading_cost,
            'total_return': total_return,
            'total_cycles': len(daily_returns),
            'daily_returns': daily_returns,
            'portfolio_values': portfolio_values
        }
        
        print(f"   Average Daily Return: {avg_daily_return*100:+.2f}%")
        print(f"   Daily Volatility: {daily_return_std*100:.2f}%")
        print(f"   Positive Days: {positive_days}/{len(daily_returns)} ({positive_ratio*100:.0f}%)")
        print(f"   Max Daily Return: {max_daily_return*100:+.2f}%")
        print(f"   Min Daily Return: {min_daily_return*100:+.2f}%")
        print(f"   Total Return: {total_return*100:+.1f}%")
        print(f"   Avg Trading Cost: ${avg_trading_cost:.2f}")
        
        return analysis
    
    def _calculate_calibration_parameters(self, analysis):
        """Calculate optimal calibration parameters from analysis"""
        
        print(f"\n⚙️  CALCULATING CALIBRATION PARAMETERS:")
        print("-" * 40)
        
        # Market timing efficiency (based on positive day ratio)
        timing_efficiency = 0.4 + (analysis['positive_days_ratio'] * 0.5)
        timing_efficiency = max(0.4, min(0.9, timing_efficiency))
        
        # Daily slippage (based on volatility)
        daily_slippage = analysis['daily_return_std'] * 0.3
        daily_slippage = max(0.001, min(0.01, daily_slippage))
        
        # Trading fee (from environment)
        trading_fee = float(os.getenv('TRADING_FEE', '0.001'))
        
        # Volatility drag (based on return volatility)
        volatility_drag = analysis['daily_return_std'] * 0.2
        volatility_drag = max(0.001, min(0.005, volatility_drag))
        
        # Daily return cap (based on observed maximum + buffer)
        max_daily_return = analysis['max_daily_return'] * 1.1
        max_daily_return = max(0.02, min(0.08, max_daily_return))
        
        # Daily return floor
        min_daily_return = analysis['min_daily_return'] * 1.1
        min_daily_return = max(-0.08, min(-0.02, min_daily_return))
        
        params = {
            'market_timing_efficiency': timing_efficiency,
            'daily_slippage': daily_slippage,
            'trading_fee': trading_fee,
            'volatility_drag': volatility_drag,
            'max_daily_return': max_daily_return,
            'min_daily_return': min_daily_return
        }
        
        print(f"   Market Timing Efficiency: {timing_efficiency*100:.0f}%")
        print(f"   Daily Slippage: {daily_slippage*100:.2f}%")
        print(f"   Trading Fee: {trading_fee*100:.1f}%")
        print(f"   Volatility Drag: {volatility_drag*100:.2f}%")
        print(f"   Max Daily Return: {max_daily_return*100:.1f}%")
        print(f"   Min Daily Return: {min_daily_return*100:.1f}%")
        
        return params
    
    def _detect_market_conditions(self, analysis):
        """Detect market conditions from performance data"""
        
        avg_return = analysis['avg_daily_return']
        volatility = analysis['daily_return_std']
        positive_ratio = analysis['positive_days_ratio']
        
        # Determine market regime
        if avg_return > 0.02 and positive_ratio > 0.7:
            market_regime = "bull_market"
        elif avg_return < -0.01 and positive_ratio < 0.4:
            market_regime = "bear_market"
        else:
            market_regime = "sideways_market"
        
        # Determine volatility level
        if volatility > 0.04:
            volatility_level = "high"
        elif volatility > 0.02:
            volatility_level = "medium"
        else:
            volatility_level = "low"
        
        return {
            'market_regime': market_regime,
            'volatility_level': volatility_level,
            'trend_strength': abs(avg_return) / volatility if volatility > 0 else 0
        }
    
    def _create_profile_structure(self, name, robot_data, analysis, params, conditions):
        """Create the complete profile structure"""
        
        profile = {
            'profile_name': name,
            'created_date': datetime.now().isoformat(),
            'version': '1.0',
            'based_on_data': {
                'start_date': robot_data['start_date'].isoformat(),
                'end_date': robot_data['end_date'].isoformat(),
                'analysis_days': robot_data['analysis_period'],
                'real_cycles': len(robot_data['trading_cycles']),
                'market_conditions': conditions['market_regime']
            },
            'performance_analysis': {
                'avg_daily_return': analysis['avg_daily_return'],
                'daily_return_std': analysis['daily_return_std'],
                'max_daily_return': analysis['max_daily_return'],
                'min_daily_return': analysis['min_daily_return'],
                'positive_days_ratio': analysis['positive_days_ratio'],
                'avg_trading_cost': analysis['avg_trading_cost'],
                'total_return': analysis['total_return'],
                'total_cycles': analysis['total_cycles']
            },
            'calibration_parameters': params,
            'market_conditions': conditions,
            'metadata': {
                'robot_version': os.getenv('STRATEGY_NAME', 'daily_rebalance'),
                'portfolio_size': int(os.getenv('PORTFOLIO_SIZE', '10')),
                'starting_capital': float(os.getenv('STARTING_CAPITAL', '100')),
                'trading_fee_env': float(os.getenv('TRADING_FEE', '0.001')),
                'data_quality': 'high' if analysis['total_cycles'] >= 14 else 'medium'
            }
        }
        
        return profile
    
    def _save_profile(self, profile):
        """Save calibration profile to file"""
        
        filename = f"{profile['profile_name']}.json"
        filepath = os.path.join(self.profiles_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(profile, f, indent=2)
            
            print(f"💾 Profile saved to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error saving profile: {e}")
            raise
    
    def _validate_profile(self, profile):
        """Validate the created profile"""
        
        params = profile['calibration_parameters']
        analysis = profile['performance_analysis']
        
        # Calculate expected monthly return
        daily_return = analysis['avg_daily_return']
        timing_eff = params['market_timing_efficiency']
        costs = params['daily_slippage'] + params['volatility_drag'] + (params['trading_fee'] * 2)
        
        net_daily_return = (daily_return * timing_eff) - costs
        monthly_return = ((1 + net_daily_return) ** 30 - 1) * 100
        
        # Quality rating
        if analysis['total_cycles'] >= 20 and analysis['daily_return_std'] < 0.05:
            quality = "excellent"
        elif analysis['total_cycles'] >= 14 and analysis['daily_return_std'] < 0.08:
            quality = "good"
        elif analysis['total_cycles'] >= 7:
            quality = "fair"
        else:
            quality = "poor"
        
        return {
            'quality_rating': quality,
            'expected_monthly_return': f"{monthly_return:.1f}%",
            'data_cycles': analysis['total_cycles'],
            'volatility_level': profile['market_conditions']['volatility_level']
        }
    
    def _handle_insufficient_data(self, robot_data, profile_name):
        """Handle case with insufficient robot data"""
        
        print(f"\n⚠️  INSUFFICIENT DATA FOR PROFILE CREATION")
        print("-" * 45)
        
        cycles_needed = 7 - len(robot_data['trading_cycles'])
        
        print(f"   Profile Name: {profile_name}")
        print(f"   Current Cycles: {len(robot_data['trading_cycles'])}")
        print(f"   Minimum Required: 7")
        print(f"   Additional Cycles Needed: {cycles_needed}")
        print()
        
        print(f"📋 RECOMMENDATIONS:")
        print(f"   1. Continue running robot for {cycles_needed} more days")
        print(f"   2. Ensure robot is in active trading mode")
        print(f"   3. Check that trading cycles are being recorded")
        print(f"   4. Try again once sufficient data is collected")
        
        # Create placeholder profile for future use
        placeholder_profile = {
            'profile_name': f"{profile_name}_placeholder",
            'status': 'insufficient_data',
            'created_date': datetime.now().isoformat(),
            'cycles_needed': cycles_needed,
            'current_cycles': len(robot_data['trading_cycles'])
        }
        
        placeholder_path = os.path.join(self.profiles_dir, f"{profile_name}_placeholder.json")
        with open(placeholder_path, 'w') as f:
            json.dump(placeholder_profile, f, indent=2)
        
        print(f"   📝 Placeholder saved to: {placeholder_path}")
        
        return {
            'success': False,
            'reason': 'insufficient_data',
            'cycles_needed': cycles_needed,
            'placeholder_path': placeholder_path
        }

def create_calibration_profile(profile_name: str, analysis_days: int = 14):
    """Create calibration profile from robot data"""
    
    creator = CalibrationProfileCreator()
    return creator.create_profile_from_robot_data(profile_name, analysis_days)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Create calibration profile from robot data')
    parser.add_argument('--name', required=True, help='Name for the calibration profile')
    parser.add_argument('--days', type=int, default=14, help='Number of days to analyze (default: 14)')
    
    args = parser.parse_args()
    
    result = create_calibration_profile(args.name, args.days)
    
    if result['success']:
        print(f"\n🎉 SUCCESS: Calibration profile '{args.name}' created!")
    else:
        print(f"\n❌ FAILED: Could not create calibration profile")
        if 'reason' in result:
            print(f"   Reason: {result['reason']}")