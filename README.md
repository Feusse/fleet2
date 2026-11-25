# Fleet.cm — Plateforme SaaS de gestion et location de véhicules (V1)

Multi-tenant : chaque agence de location (Douala/Yaoundé, 5 à 20 véhicules) a son
propre espace isolé. Anti-double-réservation, contrats PDF, paiements
Orange Money / MTN MoMo (simulés), tableau de bord avec KPI, alertes
(assurance, vidange, retards).

## Stack

- Backend : Python + Django 4.2 + Django REST Framework + SQLite (V1 locale)
- Frontend : Django Templates + TailwindCSS (CDN) + HTMX
- PDF : ReportLab
- Compatible macOS Monterey 12.7.6, Python 3.10 / 3.11, Django 4.2 LTS

## Démarrage rapide (macOS, sans terminal)

Double-cliquez simplement sur **`Demarrer_Fleet.command`**.

Au tout premier lancement, il installe tout automatiquement (ça prend
quelques dizaines de secondes), puis ouvre le navigateur sur Fleet.cm. Les
lancements suivants sont quasi instantanés. Pour arrêter le logiciel, fermez
simplement la fenêtre de terminal qui s'est ouverte.

Si macOS refuse de l'ouvrir au premier essai ("développeur non identifié") :
clic droit sur le fichier → **Ouvrir** → confirmer. Ça ne sera demandé qu'une
seule fois.

## Installation manuelle (alternative, ou autres systèmes)

```bash
# 1. Créer et activer un environnement virtuel
python3 -m venv venv
source venv/bin/activate        # sur Windows : venv\Scripts\activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Appliquer les migrations
python manage.py migrate

# 4. Charger les données de démonstration
python manage.py seed_demo

# 5. Lancer le serveur
python manage.py runserver
```

Ouvrir : **http://127.0.0.1:8000**

## Connexion de démonstration

Après `seed_demo` :

- URL de connexion : http://127.0.0.1:8000/connexion/
- Utilisateur : `patron`
- Mot de passe : `demo1234`
- Agence : **Prestige Auto Douala**

Le seed crée 5 véhicules (Yaris, RAV4, Hilux, Elantra, Sportage), 3 clients,
et 2 réservations sur le même véhicule (une confirmée, une en devis) qui se
chevauchent — pour tester le blocage anti-double-réservation :
dans l'interface, ouvrez la réservation en "devis" et essayez de la confirmer
→ elle doit être refusée avec le message d'erreur indiquant la période déjà prise.

## Page publique de réservation

Chaque agence a une page publique accessible sans connexion :

```
http://127.0.0.1:8000/r/prestige-auto-douala/
```

Elle liste les véhicules disponibles et permet à un client de faire une
demande de réservation (créée comme "devis", à confirmer depuis l'interface
interne).

## Admin Django

```
http://127.0.0.1:8000/admin/
```

Utilisable avec le compte `patron` (is_staff=True) pour inspecter/éditer les
données brutes de son propre tenant, ou créer un superuser dédié :

```bash
python manage.py createsuperuser
```

## Arborescence du projet

```
fleetcm/
├── manage.py
├── requirements.txt
├── db.sqlite3                  (créé après migrate)
├── config/                     # settings, urls, wsgi/asgi
├── tenants/                    # Tenant, User, auth, middleware, décorateur
│   ├── models.py                 Tenant + User (AUTH_USER_MODEL)
│   ├── middleware.py             attache request.tenant
│   ├── decorators.py             @tenant_required
│   └── views_public.py           page publique /r/<slug>/
├── fleet/                      # Véhicules (CRUD, vue grille, badges couleur)
├── reservations/                # Clients, Réservations, anti-chevauchement, PDF contrat
│   └── pdf.py                    génération du contrat avec ReportLab
├── billing/                    # Paiements (OM / MoMo / Cash simulés)
├── dashboard/                  # KPI, graphique Chart.js, alertes
└── templates/                  # Tous les templates (Tailwind + HTMX)
```

## Logique métier critique : anti-double-réservation

Vérifiée à **deux niveaux** :

1. **Niveau code** (`reservations/models.py`, méthode `clean()`) : avant toute
   sauvegarde d'une réservation au statut `confirmée` ou `en_cours`, on
   vérifie qu'aucune autre réservation active sur le même véhicule ne
   chevauche les dates. Sinon : `ValidationError`.
2. **Niveau transaction** (`reservations/views.py`) : la création/confirmation
   se fait dans un `transaction.atomic()` avec `select_for_update()` sur le
   véhicule, pour éviter qu'une race condition (deux utilisateurs qui valident
   au même instant) ne crée malgré tout un chevauchement.

## Isolation multi-tenant

- Toutes les tables métier (`Vehicule`, `Client`, `Reservation`, `Paiement`)
  ont une clé étrangère `tenant`.
- Le middleware `tenants.middleware.TenantMiddleware` attache
  `request.tenant` à partir de l'utilisateur connecté.
- Le décorateur `@tenant_required` (sur toutes les vues internes) impose la
  présence de `request.tenant` et bloque l'accès sinon.
- Chaque vue filtre explicitement ses querysets par `tenant=request.tenant`
  (jamais de requête non filtrée sur un modèle métier).
- La page publique `/r/<slug>/` est le seul endroit sans authentification :
  elle résout le tenant via le `slug` de l'URL, jamais via `request.tenant`.

## Nouveautés V2

Toutes testées en conditions réelles (serveur lancé, requêtes HTTP, génération
de fichiers vérifiée).

### 1. PostgreSQL en production
Rien à changer dans le code. En local, Fleet.cm continue d'utiliser SQLite
automatiquement. Pour passer en production avec PostgreSQL, copiez
`.env.example` en `.env` et renseignez `DATABASE_URL` (fournie par votre
hébergeur, ex: Railway, Render). Sans cette variable, SQLite reste utilisé.

### 2. Paiement en ligne réel (Orange Money / MTN MoMo via CinetPay)
CinetPay est un agrégateur qui gère les deux opérateurs derrière une seule
API — plus simple que d'intégrer chacun séparément.

1. Créez un compte sur https://cinetpay.com
2. Récupérez votre `API_KEY` et `SITE_ID` (mode "test" pour commencer)
3. Renseignez-les dans `.env` (voir `.env.example`)
4. Le bouton "Payer en ligne (OM/MoMo)" apparaît alors automatiquement sur
   chaque paiement en attente — le client est redirigé vers une page CinetPay
   pour payer, et le statut se met à jour automatiquement via webhook
   (`/paiements/notification-cinetpay/`).

Sans ces clés configurées, l'app reste utilisable normalement : les
paiements se marquent "payé" manuellement (comportement V1), rien ne casse.

### 3. Notifications WhatsApp automatiques (via Twilio)
1. Créez un compte sur https://www.twilio.com
2. Activez le "WhatsApp Sandbox" (gratuit pour tester)
3. Renseignez `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` dans `.env`

Ce qui est envoyé automatiquement :
- Confirmation de réservation au client, dès qu'elle passe "confirmée"
- Alertes quotidiennes au patron (assurance qui expire, vidange nécessaire,
  retards de retour) via la commande :
  ```bash
  python manage.py envoyer_alertes_whatsapp
  ```
  À placer dans une tâche planifiée (cron) quotidienne chez votre hébergeur.

Sans clés Twilio configurées, les messages sont simplement journalisés dans
la console (mode démo) au lieu d'échouer.

### 4. Export de rapports PDF / Excel
Depuis le tableau de bord (patron uniquement), boutons "Exporter en PDF" et
"Exporter en Excel" : liste des réservations et paiements du mois en cours,
avec le total du chiffre d'affaires. L'Excel contient 3 feuilles
(Réservations, Paiements, Résumé) prêtes pour un comptable.

### 5. Rôle "gestionnaire" avec permissions restreintes
Le patron peut créer des comptes "gestionnaire" depuis le menu **Équipe**
(visible seulement pour lui). Un gestionnaire peut :
- gérer les véhicules (ajouter/modifier, **pas supprimer**)
- gérer les clients et réservations, enregistrer les retours et paiements
- voir les alertes

Un gestionnaire **ne voit pas** : le chiffre d'affaires, les impayés, le
détail de rentabilité par véhicule, et n'a pas accès à l'export de rapports
ni à la page Équipe. Le patron peut désactiver un compte gestionnaire à tout
moment (sans le supprimer, pour garder l'historique).

## Prochaines étapes suggérées (hors V2)

- Vraie vérification de signature sur le webhook CinetPay (actuellement on
  revérifie le statut via l'API, ce qui est sûr, mais une vérification de
  signature HMAC ajouterait une couche supplémentaire)
- Export des rapports sur une période personnalisée (pas seulement le mois en cours)
- Passage à un vrai numéro WhatsApp Business (au lieu du sandbox Twilio) en production
