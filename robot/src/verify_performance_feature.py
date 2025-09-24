#!/usr/bin/env python3
"""
Verify Performance Percentage Feature
"""
from src.database import get_db_manager, Simulation

def verify_feature():
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    try:
        # Get the latest simulation
        sim = session.query(Simulation).order_by(Simulation.id.desc()).first()
        
        if not sim:
            print("❌ No simulations found")
            return
        
        print(f"✅ Found simulation: {sim.name} (ID: {sim.id})")
        print(f"📊 Status: {sim.status}")
        
        if sim.final_total_value and sim.starting_reserve:
            roi = ((sim.final_total_value / sim.starting_reserve - 1) * 100)
            print(f"💰 Final ROI: {roi:+.2f}%")
        
        cycles = sim.simulation_cycles
        print(f"🔄 Total cycles: {len(cycles)}")
        
        if cycles:
            cycle = cycles[-1]  # Last cycle
            print(f"\n🔍 Last cycle portfolio breakdown:")
            
            if cycle.portfolio_breakdown:
                count = 0
                for crypto_name, data in cycle.portfolio_breakdown.items():
                    if count >= 5:
                        break
                    
                    if isinstance(data, dict) and 'value' in data:
                        value = data['value']
                        performance = data.get('performance', 0)
                        perf_sign = '+' if performance >= 0 else ''
                        color = '🟢' if performance >= 0 else '🔴'
                        print(f"   {crypto_name}: {value:.6f} BNB {color} {perf_sign}{performance*100:.2f}%")
                    else:
                        print(f"   {crypto_name}: {data:.6f} BNB (old format)")
                    count += 1
            
            print(f"\n🌐 Test the interactive feature at:")
            print(f"   Portfolio view: http://localhost:5000/simulation/{sim.id}/history")
            print(f"   Combined view: http://localhost:5000/simulation/{sim.id}/combined")
            print(f"\n   💡 Click any point on the portfolio chart to see the enhanced popup!")
            print(f"      Each crypto will show: Value + Portfolio % + Performance %")
        
    finally:
        session.close()

if __name__ == "__main__":
    print("🧪 VERIFYING PERFORMANCE PERCENTAGE FEATURE")
    print("=" * 50)
    verify_feature()
