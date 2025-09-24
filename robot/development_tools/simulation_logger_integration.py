# Add this to your simulation completion code (e.g., in simulation engine or web routes)

from add_simulation_summary_logging import log_simulation_view_summary

def complete_simulation(simulation_id: int):
    """Complete simulation and log summary"""
    
    # ... existing simulation completion code ...
    
    # Update simulation status
    simulation.status = 'completed'
    simulation.completed_at = datetime.utcnow()
    session.commit()
    
    # Log comprehensive summary of what user will see
    log_simulation_view_summary(simulation_id)
    
    print(f"Simulation {simulation_id} completed and summary logged")

# Or add to web route that handles simulation completion
@app.route('/api/simulation/<int:sim_id>/complete', methods=['POST'])
def complete_simulation_route(sim_id):
    """Complete simulation via web API"""
    
    # ... existing completion logic ...
    
    # Log what user will see in the interface
    log_simulation_view_summary(sim_id)
    
    return jsonify({"status": "completed", "summary_logged": True})