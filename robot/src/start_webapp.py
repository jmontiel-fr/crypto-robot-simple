#!/usr/bin/env python3
"""
Script de démarrage de l'application web du crypto trading robot
avec toutes les nouvelles fonctionnalités (Socket.IO activé)
"""

import sys
import os

# Ajouter le répertoire parent (racine du projet) au PYTHONPATH
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main():
    """Démarrer l'application web"""
    try:
        print("Démarrage de l'application Crypto Trading Robot")
        print("=" * 50)

        # Import de l'application complète (avec Socket.IO)
        from src.web_app import app, socketio

        print("✅ Application chargée avec succès")
        print("\n📋 Fonctionnalités disponibles:")
        print("   • Dashboard principal avec statut temps réel")
        print("   • Bouton Freeze/Unfreeze Robot")
        print("   • Simulateur de trading et historique")
        print("   • Historiques de portfolio et réserves")

        print("\n🌐 Interface web:")
        print("   • Dashboard principal: http://localhost:5000")
        print("   • Simulateur: http://localhost:5000/simulator")

        print("\n🎯 Démarrage du serveur web...")
        print("   Appuyez sur Ctrl+C pour arrêter")
        print("=" * 50)

        # Démarrer l'application avec Socket.IO (sans reloader pour conserver les threads)
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False,
        )
        return True

    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("\n💡 Solutions possibles:")
        print("   1. Vérifiez que vous êtes dans le bon répertoire")
        print("   2. Installez les dépendances: pip install -r requirements.txt")
        print("   3. Activez l'environnement virtuel si nécessaire")
        return False

    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        return False


if __name__ == "__main__":
    main()
