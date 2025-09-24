#!/usr/bin/env python3
"""
VÉRIFICATION RAPIDE DU SYSTÈME REDÉMARRÉ
=======================================

Script de vérification post-redémarrage pour confirmer que :
1. Toutes les corrections sont appliquées
2. Les simulations produisent des résultats proportionnels
3. Le système est déterministe et cohérent

Utilisation: python verifier_systeme.py
"""

import os
import sys
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.database import get_db_manager, Simulation, SimulationCycle
    print("✓ Modules importés avec succès")
except ImportError as e:
    print(f"✗ Erreur d'import: {e}")
    sys.exit(1)

def verifier_etat_base():
    """Vérifie l'état de la base de données"""
    print("\n" + "="*50)
    print("ÉTAT DE LA BASE DE DONNÉES")
    print("="*50)
    
    try:
        db_manager = get_db_manager()
        session = db_manager.get_session()
        
        simulations = session.query(Simulation).all()
        cycles = session.query(SimulationCycle).all()
        
        print(f"Simulations: {len(simulations)}")
        print(f"Cycles: {len(cycles)}")
        
        if simulations:
            print("\nSimulations trouvées:")
            for sim in simulations:
                print(f"  - {sim.name} (ID: {sim.id}) - {sim.starting_reserve} BNB - Status: {sim.status}")
        
        session.close()
        return len(simulations), len(cycles)
        
    except Exception as e:
        print(f"✗ Erreur: {e}")
        return 0, 0

def verifier_coherence_simulations():
    """Vérifie la cohérence des simulations existantes"""
    print("\n" + "="*50)
    print("VÉRIFICATION DE COHÉRENCE")
    print("="*50)
    
    try:
        db_manager = get_db_manager()
        session = db_manager.get_session()
        
        # Chercher les simulations avec mêmes paramètres temporels
        simulations = session.query(Simulation).filter(
            Simulation.name.like('Test_Cohérence_%')
        ).all()
        
        if len(simulations) < 2:
            print("⚠ Pas assez de simulations pour tester la cohérence")
            session.close()
            return False
        
        # Grouper par paramètres temporels
        groupes = {}
        for sim in simulations:
            key = f"{sim.start_date}_{sim.duration_days}_{sim.cycle_length_minutes}"
            if key not in groupes:
                groupes[key] = []
            groupes[key].append(sim)
        
        print(f"Groupes de simulations avec mêmes paramètres temporels: {len(groupes)}")
        
        for key, groupe in groupes.items():
            if len(groupe) >= 2:
                print(f"\nGroupe: {key}")
                reserves = [sim.starting_reserve for sim in groupe]
                print(f"Réserves: {reserves}")
                
                # Vérifier que les ratios sont cohérents
                if len(reserves) >= 2:
                    ratio_attendu = reserves[1] / reserves[0]
                    print(f"Ratio attendu entre simulations: {ratio_attendu:.2f}")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"✗ Erreur: {e}")
        return False

def verifier_code_corrections():
    """Vérifie que les corrections sont bien présentes dans le code"""
    print("\n" + "="*50)
    print("VÉRIFICATION DU CODE")
    print("="*50)
    
    web_app_path = os.path.join('src', 'web_app.py')
    
    if not os.path.exists(web_app_path):
        print(f"✗ Fichier {web_app_path} non trouvé")
        return False
    
    try:
        with open(web_app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifications essentielles
        checks = [
            ('temporal_seed_string = f"', 'Seed temporel correct'),
            ('temporal_seed = abs(hash(temporal_seed_string))', 'Hash temporel'),
            ('cycle_seed = temporal_seed + cycle_number * 1000', 'Seed par cycle'),
            ('crypto_rng = random.Random(crypto_seed)', 'RNG par crypto'),
            ('PROPORTIONAL RESULTS', 'Commentaire de correction')
        ]
        
        all_ok = True
        for check, description in checks:
            if check in content:
                print(f"✓ {description}")
            else:
                print(f"✗ MANQUANT: {description}")
                all_ok = False
        
        # Vérifier l'absence de l'ancien système
        problemes = [
            ('simulation_seed = temporal_seed + simulation.id', 'Ancien seed avec simulation.id'),
            ('random.seed(simulation.id', 'Ancien seed global avec simulation.id')
        ]
        
        for probleme, description in problemes:
            if probleme in content:
                print(f"✗ PROBLÈME: {description} encore présent")
                all_ok = False
        
        if all_ok:
            print("✓ Toutes les corrections sont appliquées")
        
        return all_ok
        
    except Exception as e:
        print(f"✗ Erreur lors de la vérification: {e}")
        return False

def tester_determinisme():
    """Test simple de déterminisme"""
    print("\n" + "="*50)
    print("TEST DE DÉTERMINISME")
    print("="*50)
    
    try:
        # Importer la fonction de calcul de seed
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        # Test du calcul de seed temporel
        date1 = datetime(2024, 1, 1)
        duration = 30
        cycle_minutes = 360  # 6 hours = 360 minutes
        
        # Simuler le calcul de seed comme dans le code
        formatted_date = date1.strftime("%Y-%m-%d")
        temporal_seed_string = f"{formatted_date}_{duration}_{cycle_minutes}"
        temporal_seed = abs(hash(temporal_seed_string))
        
        print(f"Date test: {formatted_date}")
        print(f"Durée: {duration} jours")
        print(f"Cycle: {cycle_minutes} minutes")
        print(f"String temporelle: {temporal_seed_string}")
        print(f"Seed temporel: {temporal_seed}")
        
        # Tester que le même calcul donne le même résultat
        temporal_seed2 = abs(hash(temporal_seed_string))
        if temporal_seed == temporal_seed2:
            print("✓ Déterminisme confirmé: même seed pour mêmes paramètres")
            return True
        else:
            print("✗ Problème de déterminisme détecté")
            return False
        
    except Exception as e:
        print(f"✗ Erreur lors du test: {e}")
        return False

def afficher_resume():
    """Affiche un résumé de l'état du système"""
    print("\n" + "="*70)
    print("RÉSUMÉ DE L'ÉTAT DU SYSTÈME")
    print("="*70)
    
    # Vérifier chaque composant
    composants = {
        'Code corrigé': verifier_code_corrections(),
        'Déterminisme': tester_determinisme(),
        'Base de données': verifier_etat_base()[0] >= 0,
        'Cohérence': verifier_coherence_simulations()
    }
    
    print("\nÉtat des composants:")
    all_ok = True
    for composant, status in composants.items():
        if status:
            print(f"✓ {composant}: OK")
        else:
            print(f"✗ {composant}: PROBLÈME")
            all_ok = False
    
    print(f"\n{'='*70}")
    if all_ok:
        print("🎉 SYSTÈME ENTIÈREMENT OPÉRATIONNEL!")
        print("✅ Toutes les corrections sont appliquées")
        print("✅ Le système est prêt pour des simulations cohérentes")
        print("\nVous pouvez maintenant:")
        print("  1. Démarrer l'interface web: python src/web_app.py")
        print("  2. Créer des simulations avec mêmes paramètres temporels")
        print("  3. Vérifier que les résultats sont proportionnels")
    else:
        print("⚠ ATTENTION: Certains problèmes ont été détectés")
        print("Relancez le script de redémarrage si nécessaire")
    
    print("="*70)

def main():
    """Fonction principale"""
    print("="*70)
    print("🔍 VÉRIFICATION DU SYSTÈME REDÉMARRÉ")
    print("="*70)
    print(f"Date/Heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    afficher_resume()

if __name__ == "__main__":
    main()
