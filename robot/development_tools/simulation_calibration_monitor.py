#!/usr/bin/env python3
"""
Simulation Calibration Monitor

Monitors real robot performance and automatically recalibrates simulations
when significant deviations are detected. Can be run as a scheduled task.
"""

from src.database import DatabaseManager, Simulation, TradingCycle
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from auto_calibrate_simulation import SimulationAutoCalibrator

load_dotenv()

class CalibrationMonitor:
    """Monitors and maintains simulation calibration"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.calibrator = SimulationAutoCalibrator()
        self.config = self._load_monitor_config()
        
    def _load_monitor_config(self):
        """Load monitoring configuration"""
        return {
            'check_interval_days': 7,  # Check weekly
            'recalibration_threshold': 1.0,  # 1% daily return difference triggers recalibration
            'min_cycles_for_check': 7,  # Need at least 7 cycles to check
            'max_deviation_days': 3,  # Alert if deviation persists for 3+ days
            'auto_recalibrate': True,  # Automatically recalibrate when needed
        }
    
    def run_monitoring_check(self):
        """Run a complete monitoring check"""
        
        print("🔍 SIMULATION CALIBRATION MONITORING")
        print("=" * 50)
        print(f"   Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Check Interval: {self.config['check_interval_days']} days")
        print(f"   Auto-Recalibrate: {'Enabled' if self.config['auto_recalibrate'] else 'Disabled'}")
        print()
        
        session = self.db_manager.get_session()
        
        try:
            # Get all active simulations
            simulations = session.query(Simulation).filter(
                Simulation.status == 'completed'
            ).all()
            
            print(f"📊 MONITORING {len(simulations)} SIMULATION(S):")
            print("-" * 40)
            
            monitoring_results = []
            
            for sim in simulations:
                result = self._check_simulation_calibration(session, sim)
                monitoring_results.append(result)
                
                # Display result
                status_icon = "✅" if result['status'] == 'good' else "⚠️" if result['status'] == 'warning' else "🔴"
                print(f"   {status_icon} SIM{sim.id}: {result['status'].upper()} - {result['message']}")
                
                # Auto-recalibrate if needed and enabled
                if (result['status'] == 'needs_recalibration' and 
                    self.config['auto_recalibrate']):
                    
                    print(f"      🔄 Auto-recalibrating SIM{sim.id}...")
                    recal_result = self.calibrator.auto_calibrate(sim.id)
                    
                    if recal_result.get('success'):
                        print(f"      ✅ Auto-recalibration successful")
                        result['recalibrated'] = True
                    else:
                        print(f"      ❌ Auto-recalibration failed")
                        result['recalibration_error'] = recal_result.get('error', 'Unknown error')
            
            # Generate summary report
            self._generate_monitoring_report(monitoring_results)
            
            return monitoring_results
            
        except Exception as e:
            print(f"❌ Error during monitoring: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            session.close()
    
    def _check_simulation_calibration(self, session, simulation):
        """Check if a simulation needs recalibration"""
        
        # Get recent real robot data
        cutoff_date = datetime.now() - timedelta(days=self.config['check_interval_days'])
        
        real_cycles = session.query(TradingCycle).filter(
            TradingCycle.cycle_date >= cutoff_date
        ).order_by(TradingCycle.cycle_date).all()
        
        if len(real_cycles) < self.config['min_cycles_for_check']:
            return {
                'simulation_id': simulation.id,
                'status': 'insufficient_data',
                'message': f'Need {self.config["min_cycles_for_check"] - len(real_cycles)} more real cycles',
                'real_cycles': len(real_cycles),
                'deviation': None
            }
        
        # Calculate recent real robot performance
        if len(real_cycles) >= 2:
            real_returns = []
            for i in range(1, len(real_cycles)):
                prev_value = real_cycles[i-1].total_value
                curr_value = real_cycles[i].total_value
                daily_return = (curr_value - prev_value) / prev_value
                real_returns.append(daily_return)
            
            avg_real_daily_return = sum(real_returns) / len(real_returns)
        else:
            avg_real_daily_return = 0
        
        # Calculate simulation's expected daily return
        sim_daily_return = ((simulation.final_total_value / simulation.starting_reserve) ** 
                           (1/simulation.duration_days) - 1)
        
        # Calculate deviation
        deviation = abs(sim_daily_return - avg_real_daily_return)
        deviation_pct = deviation * 100
        
        # Determine status
        if deviation_pct < self.config['recalibration_threshold']:
            status = 'good'
            message = f'Well calibrated (deviation: {deviation_pct:.2f}%)'
        elif deviation_pct < self.config['recalibration_threshold'] * 2:
            status = 'warning'
            message = f'Minor deviation detected ({deviation_pct:.2f}%)'
        else:
            status = 'needs_recalibration'
            message = f'Significant deviation ({deviation_pct:.2f}%) - recalibration needed'
        
        return {
            'simulation_id': simulation.id,
            'status': status,
            'message': message,
            'deviation': deviation_pct,
            'sim_daily_return': sim_daily_return * 100,
            'real_daily_return': avg_real_daily_return * 100,
            'real_cycles': len(real_cycles)
        }
    
    def _generate_monitoring_report(self, results):
        """Generate a summary monitoring report"""
        
        print(f"\n📋 MONITORING SUMMARY REPORT:")
        print("-" * 40)
        
        # Count statuses
        status_counts = {}
        total_deviations = []
        recalibrated_count = 0
        
        for result in results:
            status = result['status']
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if result.get('deviation') is not None:
                total_deviations.append(result['deviation'])
            
            if result.get('recalibrated'):
                recalibrated_count += 1
        
        # Display summary
        print(f"   Total Simulations Checked: {len(results)}")
        
        for status, count in status_counts.items():
            status_icon = {"good": "✅", "warning": "⚠️", "needs_recalibration": "🔴", "insufficient_data": "📊"}
            icon = status_icon.get(status, "❓")
            print(f"   {icon} {status.replace('_', ' ').title()}: {count}")
        
        if total_deviations:
            avg_deviation = sum(total_deviations) / len(total_deviations)
            max_deviation = max(total_deviations)
            print(f"   📊 Average Deviation: {avg_deviation:.2f}%")
            print(f"   📊 Maximum Deviation: {max_deviation:.2f}%")
        
        if recalibrated_count > 0:
            print(f"   🔄 Auto-Recalibrated: {recalibrated_count} simulation(s)")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        needs_recal = status_counts.get('needs_recalibration', 0)
        warnings = status_counts.get('warning', 0)
        insufficient = status_counts.get('insufficient_data', 0)
        
        if needs_recal > 0 and not self.config['auto_recalibrate']:
            print(f"   🔴 {needs_recal} simulation(s) need manual recalibration")
        
        if warnings > 0:
            print(f"   ⚠️  Monitor {warnings} simulation(s) with minor deviations")
        
        if insufficient > 0:
            print(f"   📊 Wait for more real data for {insufficient} simulation(s)")
        
        if needs_recal == 0 and warnings == 0:
            print(f"   ✅ All simulations are well calibrated")
        
        # Save report
        self._save_monitoring_report(results)
    
    def _save_monitoring_report(self, results):
        """Save monitoring report to file"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'config': self.config,
            'results': results,
            'summary': {
                'total_checked': len(results),
                'status_counts': {},
                'recalibrated_count': sum(1 for r in results if r.get('recalibrated'))
            }
        }
        
        # Count statuses for summary
        for result in results:
            status = result['status']
            report['summary']['status_counts'][status] = report['summary']['status_counts'].get(status, 0) + 1
        
        # Save to file
        report_file = f"monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"   📝 Report saved to {report_file}")
        except Exception as e:
            print(f"   ⚠️  Could not save report: {e}")
    
    def schedule_monitoring(self, interval_hours: int = 24):
        """Set up scheduled monitoring (placeholder for actual scheduling)"""
        
        print(f"📅 SCHEDULING MONITORING:")
        print(f"   Interval: Every {interval_hours} hours")
        print(f"   Next Check: {(datetime.now() + timedelta(hours=interval_hours)).strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print(f"💡 TO IMPLEMENT SCHEDULING:")
        print(f"   1. Use cron job: 0 */{interval_hours} * * * python simulation_calibration_monitor.py")
        print(f"   2. Use Windows Task Scheduler for Windows systems")
        print(f"   3. Use systemd timer for Linux systems")
        print(f"   4. Integrate with your application's scheduler")

def run_monitoring():
    """Run monitoring check"""
    monitor = CalibrationMonitor()
    return monitor.run_monitoring_check()

if __name__ == "__main__":
    run_monitoring()