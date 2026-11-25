#!/bin/bash
# Double-cliquez sur ce fichier pour lancer Fleet.cm.
# Compatible macOS. Ferme simplement cette fenetre de terminal pour arreter le logiciel.

cd "$(dirname "$0")"

echo "========================================"
echo "   Fleet.cm - demarrage en cours..."
echo "========================================"
echo ""

# Verifie que Python 3 est installe
if ! command -v python3 &> /dev/null; then
    echo "ERREUR : Python 3 n'est pas installe sur cet ordinateur."
    echo "Installez-le depuis https://www.python.org puis relancez ce fichier."
    read -p "Appuyez sur Entree pour fermer..."
    exit 1
fi

# Cree l'environnement virtuel au tout premier lancement seulement
if [ ! -d "venv" ]; then
    echo "Premiere installation, merci de patienter quelques instants..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip > /dev/null
    pip install -r requirements.txt
    echo ""
    echo "Installation terminee."
else
    source venv/bin/activate
fi

# Met a jour la base de donnees si necessaire (sans effacer les donnees existantes)
python manage.py migrate --noinput

# Charge les donnees de demonstration seulement au tout premier lancement
if [ ! -f ".premier_lancement_ok" ]; then
    python manage.py seed_demo
    touch .premier_lancement_ok
fi

echo ""
echo "Fleet.cm est pret. Ouverture du navigateur..."
echo "Pour ARRETER le logiciel : fermez simplement cette fenetre."
echo ""

# Ouvre automatiquement le navigateur sur la bonne page apres 2 secondes
( sleep 2 && open "http://127.0.0.1:8000" ) &

# Lance le serveur (cette ligne garde la fenetre active)
python manage.py runserver 127.0.0.1:8000
