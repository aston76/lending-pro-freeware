# Suivi d'Implémentation — Loan Manager

Ce document récapitule l'état d'avancement des fonctionnalités demandées.

| # | Fonctionnalité | État | Détails |
|---|----------------|:---:|---------|
| 1 | **Ajout des emails** | ✅ | Colonne ajoutée en DB, affichage et édition intégrés. |
| 2 | **Pourcentages & Durées** | ✅ | Déjà implémenté (Fixed vs Declining). |
| 3 | **Dates de paiement** | ✅ | Intégrées dans la vue Collections et All Payments. |
| 4 | **Modifier / Rallonger les mois** | ✅ | Fonction `extend_loan` ajoutée + boutons IHC. |
| 5 | **Nouveau crédit avec report** | ✅ | Système de Refinance/Rollover fonctionnel. |
| 6 | **Recherche client (3 lettres)** | ✅ | Input de recherche live avec filtrage nom/ID. |
| 7 | **Collections (Sélecteur/Validation)** | ✅ | Vue Calendar refaite avec filtrage par jour et validation groupée. |
| 8 | **Gains totaux par mois** | ✅ | API et Graphiques (barres) ajoutés. |
| 9 | **Détails All Payments** | ✅ | Tableau enrichi (Restant, Mois, Progress, Montant original). |
| 10 | **Bonus de parrainage (₱) dans Settings** | ✅ | Montant configurable + déclencheur (création prêt, 1er paiement, fin du prêt). |
| 11 | **Autocomplete d'adresse (OSM Nominatim)** | ✅ | Recherche live gratuite (Philippines / Cebu) sans clé API requise. |
| 12 | **Champ particularité d'adresse** | ✅ | Champ `address_detail` sous l'adresse principale. |
| 13 | **Refinancement "Cash-Out" Inversé** | ✅ | Mode renouvellement avec déduction du solde actuel et calcul net du cash client. |
| 14 | **Verrou de Renouvellement (3 mois)** | ✅ | Blocage automatique si < 3 paiements effectués sur le prêt en cours. |
| 15 | **Bouton Paiement Rapide (Quick Pay)** | ✅ | Ajout d'un bouton +Pay directement dans la fiche client pour chaque prêt actif. |
| 16 | **Stabilisation paiements / collections** | ✅ | Validation backend, rollback SQLite, méthodes `bank_transfer`/`check`, et masquage des échéances déjà couvertes par les paiements. |

## Synthèse Technique
- **Base de données** : Schéma `clients` mis à jour (email, address_detail).
- **Backend (API)** : Logique de renouvellement inversée dans `api.py` (`renewal_mode`).
- **Frontend** : Refonte de `client_detail.js` (formulaires, bannières, boutons rapides) et `help.js`.
- **Packaging** : Script `create_windows_zip.sh` mis à jour pour inclure ce suivi.
- **Stabilité runtime** : Les erreurs de formulaire prêt/paiement retournent maintenant un message propre sans verrouiller SQLite. Les collections utilisent le cumul payé pour ne plus afficher une échéance déjà réglée.

### 🪟 Notes Techniques Spécifiques à Windows
Pour assurer une compatibilité parfaite sur Windows (souvent différente de macOS) :
- **Encodage (UTF-8)** : Correction des erreurs `charmap` (symboles Peso `₱` et accents). Dans `main.py`, la console est maintenant forcée en UTF-8 (`sys.stdout` reconfiguré via `io.TextIOWrapper`).
- **Dépendances** : Correction de l'erreur `ModuleNotFoundError: dateutil`. Le package `python-dateutil` est explicitement inclus dans `requirements.txt`.
- **Automatisation** : Le fichier `INSTALL.bat` gère désormais :
  1. Installation de Python 3.11 si absent.
  2. Création d'un environnement virtuel (`venv_win`).
  3. Installation des libs et compilation de l'EXE via `PyInstaller`.
  4. Création d'un raccourci Bureau `.lnk` avec l'icône correcte.
- **Portabilité** : Utilisation de `sys._MEIPASS` pour charger les dossiers `web/` lorsque l'application est compilée en `.exe`.

---
*Dernière mise à jour : 4 Mai 2026*
