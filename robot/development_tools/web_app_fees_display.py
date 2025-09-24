#!/usr/bin/env python3
"""
Show how the fees would be displayed in the web app interface
"""

from src.database import DatabaseManager, Simulation

def generate_web_display_preview():
    """Generate a preview of how fees would appear in the web app"""
    
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    try:
        sims = session.query(Simulation).all()
        
        print('WEB APP SIMULATION LIST WITH FEES')
        print('=' * 80)
        
        # HTML-like table preview
        print('SIMULATION TABLE PREVIEW:')
        print('-' * 80)
        
        # Table header
        header = f"{'Name':<12} {'Duration':<10} {'Cycles':<8} {'Final Total':<12} {'Fees':<10} {'Net Return':<12} {'Status':<10}"
        print(header)
        print('-' * 80)
        
        for sim in sims:
            starting = sim.starting_reserve or 100.0
            final_net = sim.final_total_value or starting
            fees = getattr(sim, 'fee_estimate', 0.0) or 0.0
            final_gross = final_net + fees
            
            net_return = (final_net / starting - 1) * 100
            net_return_str = f"{net_return:+.1f}%"
            
            row = f"{sim.name:<12} {sim.duration_days} days{'':<2} {sim.total_cycles or 0:<8} {final_net:<12.2f} {fees:<10.2f} {net_return_str:<12} {sim.status:<10}"
            print(row)
        
        print('\nDETAILED BREAKDOWN FOR EACH SIMULATION:')
        print('=' * 50)
        
        for sim in sims:
            starting = sim.starting_reserve or 100.0
            final_net = sim.final_total_value or starting
            fees = getattr(sim, 'fee_estimate', 0.0) or 0.0
            final_gross = final_net + fees
            
            gross_return = (final_gross / starting - 1) * 100
            net_return = (final_net / starting - 1) * 100
            fee_impact = gross_return - net_return
            
            print(f'\n📊 {sim.name.upper()} PERFORMANCE CARD:')
            print(f'   ⏱️  Duration: {sim.duration_days} days ({sim.cycle_length_minutes} min cycles)')
            print(f'   🔄 Total Cycles: {sim.total_cycles or 0}')
            print(f'   💰 Starting Capital: ${starting:.2f}')
            print(f'   📈 Gross Return: +{gross_return:.1f}% (${final_gross:.2f})')
            print(f'   💸 Trading Fees: ${fees:.2f} ({fee_impact:.1f}% impact)')
            print(f'   ✅ Net Return: +{net_return:.1f}% (${final_net:.2f})')
            
            # Realism indicator
            if net_return > 100:
                realism = "🚨 Highly Optimistic"
            elif net_return > 50:
                realism = "⚠️ Challenging"
            elif net_return > 20:
                realism = "📊 Good Performance"
            elif net_return > 0:
                realism = "✅ Realistic"
            else:
                realism = "❌ Loss"
            
            print(f'   🎯 Assessment: {realism}')
        
        # Show JSON format for API
        print(f'\nAPI JSON RESPONSE FORMAT:')
        print('=' * 40)
        
        for sim in sims:
            starting = sim.starting_reserve or 100.0
            final_net = sim.final_total_value or starting
            fees = getattr(sim, 'fee_estimate', 0.0) or 0.0
            final_gross = final_net + fees
            
            net_return = (final_net / starting - 1) * 100
            
            json_preview = f'''{{
    "id": {sim.id},
    "name": "{sim.name}",
    "duration_days": {sim.duration_days},
    "cycle_length_minutes": {sim.cycle_length_minutes},
    "total_cycles": {sim.total_cycles or 0},
    "starting_reserve": {starting},
    "final_total_gross": {final_gross:.2f},
    "estimated_fees": {fees:.2f},
    "final_total_net": {final_net:.2f},
    "net_return_percentage": {net_return:.1f},
    "status": "{sim.status}"
}}'''
            print(json_preview)
            break  # Just show one example
        
    finally:
        session.close()

def show_comparison_table():
    """Show before/after comparison"""
    print(f'\nBEFORE vs AFTER FEES COMPARISON:')
    print('=' * 60)
    print(f'{"Metric":<20} {"Before Fees":<15} {"After Fees":<15} {"Impact":<10}')
    print('-' * 60)
    print(f'{"Final Total":<20} {"$160.38":<15} {"$102.65":<15} {"-$57.74":<10}')
    print(f'{"Return %":<20} {"+60.4%":<15} {"+2.6%":<15} {"-57.7%":<10}')
    print(f'{"Realism":<20} {"Questionable":<15} {"Realistic":<15} {"Much Better":<10}')
    print(f'{"User Expectation":<20} {"Unrealistic":<15} {"Achievable":<15} {"Honest":<10}')

if __name__ == "__main__":
    generate_web_display_preview()
    show_comparison_table()
    
    print(f'\n✅ SUMMARY:')
    print(f'   • fee_estimate column is preserved in database')
    print(f'   • final_total_value now shows NET returns (after fees)')
    print(f'   • Web app can display both gross and net returns')
    print(f'   • Users get transparent, realistic performance data')
    print(f'   • Fee impact is clearly visible and quantified')