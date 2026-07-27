# Nouveautés de Lending Pro Freeware

Version actuelle : **1.5.0 — build 7**
Date de livraison : **27 juillet 2026**

Ce document regroupe toutes les nouveautés fonctionnelles, visuelles et techniques ajoutées aux versions 1.4.0 et 1.5.0.

## Nouveau branding

- Nouveau logo officiel Lending Pro combinant un registre financier, une courbe de progression et un bouclier.
- Suppression du symbole monétaire de l’ancien logo afin de conserver une identité internationale compatible avec toutes les devises.
- Nouvelle palette bleu nuit, bleu professionnel et vert turquoise.
- Déclinaisons cohérentes pour macOS (`icon.icns`), Windows (`icon.ico`) et l’interface (`PNG`).
- Nouveau logo affiché sur l’écran de connexion, dans la barre latérale et sur la page À propos.
- Générateur d’icônes reproductible à partir d’une source de branding versionnée.

## Écran d’ouverture et connexion facultative

- Nouvel écran d’ouverture professionnel avant l’accès aux données métier.
- Connexion configurable séparément pour chaque profil.
- Lorsque la connexion au démarrage est désactivée, l’application arrive directement sur le tableau de bord.
- Lorsque la connexion est activée, le profil doit être déverrouillé avant le chargement des données.
- Bouton permettant d’afficher ou de masquer le mot de passe.
- Bouton **Lock Session** permettant de verrouiller l’application sans la quitter.
- Accès au bouton Quitter directement depuis l’écran verrouillé.
- Limitation à cinq essais incorrects avant un délai de sécurité de 30 secondes.
- Mot de passe stocké sous forme de hachage PBKDF2-SHA256 avec sel aléatoire et 260 000 itérations.
- Comparaison sécurisée des mots de passe et migration automatique des anciens hachages SHA-256.
- Blocage des appels métier du pont API tant que la session n’est pas authentifiée.
- Aucun mot de passe enregistré en clair dans les fichiers ou la base de données.
- Fonction désactivée par défaut afin de préserver le comportement des installations existantes.

### Activation

1. Ouvrir **Settings**.
2. Aller dans la section **Profiles**.
3. Activer **Profile Password** et définir un mot de passe d’au moins huit caractères.
4. Activer **Login at Startup**.

Le mot de passe protège également la suppression, la réinitialisation et le changement de profil.

> Le verrouillage protège l’accès depuis l’application. Il ne constitue pas un chiffrement du fichier SQLite lui-même.

## Garants et co-makers

- Nouveau registre structuré des garants pour chaque prêt.
- Enregistrement du nom, du contact, de la relation avec l’emprunteur et des informations d’identité.
- Ajout, modification et suppression d’un garant depuis la fiche du prêt.
- Signature manuscrite locale du garant.
- Remplacement et suppression contrôlés des signatures.
- Inclusion des garants et de leurs signatures dans les contrats PDF.
- Export des garants dans une feuille Excel dédiée.

## Garanties et biens mis en gage

- Nouveau registre structuré des garanties associées aux prêts.
- Types pris en charge : véhicule, immobilier, équipement, bijou, électronique et autre.
- Description du bien et valeur estimée.
- Numéro de série et plaque d’immatriculation.
- Notes et informations de suivi.
- Cycle de vie complet : **pledged**, **released**, **seized** et **sold**.
- Libération automatique des garanties encore engagées lorsque le prêt est totalement remboursé.
- Inclusion des garanties dans les contrats PDF et les exports Excel.

## KYC client enrichi

- Numéro de pièce d’identité.
- Date de naissance.
- Genre.
- Employeur.
- Profession ou activité.
- Conservation de la photographie du client et de la capture de sa pièce d’identité.
- Validation des nouvelles données lors de la création et de la modification d’un client.
- Affichage des informations KYC dans la fiche client.
- Intégration du KYC étendu dans les contrats et les exports Excel.

## Nouvelles fréquences de remboursement

- Remboursement quotidien.
- Remboursement hebdomadaire.
- Remboursement toutes les deux semaines.
- Remboursement mensuel.
- Calcul automatique du nombre réel d’échéances selon la durée et la fréquence.
- Dates d’échéance calculées selon la fréquence sélectionnée.
- Montant par échéance enregistré séparément.
- Compatibilité conservée avec les anciens prêts mensuels.
- Prolongations de prêt adaptées à la fréquence choisie.

## Frais, décaissement et taux effectif

- Frais de dossier ou de traitement.
- Frais d’assurance.
- Gestion des intérêts déduits à l’avance.
- Calcul du montant réellement remis au client.
- Calcul du remboursement contractuel total.
- Prévention de la double facturation des intérêts précomptés.
- Prévisualisation du décaissement net avant la création du prêt.
- Calcul du TAEG ou taux annuel effectif à partir des flux datés du prêt.
- Affichage du TAEG, des frais et du décaissement net dans la fiche du prêt.
- Intégration de ces données dans les contrats PDF et les exports Excel.

## Pénalités automatiques

- Activation ou désactivation depuis les paramètres.
- Période de grâce configurable en jours.
- Pénalité sous forme de montant fixe.
- Pénalité calculée en pourcentage du solde impayé de l’échéance.
- Plafond facultatif exprimé en pourcentage du capital initial.
- Création automatique après dépassement de la date d’échéance et du délai de grâce.
- Une seule pénalité automatique par échéance grâce à un mécanisme idempotent.
- Conservation des pénalités manuelles existantes.
- Fonction désactivée par défaut pour éviter toute facturation involontaire.

## Collecteurs

- Création et gestion d’une liste de collecteurs.
- Coordonnées et statut actif ou inactif.
- Affectation d’un collecteur lors de la création d’un prêt.
- Changement de collecteur depuis la fiche du prêt.
- Suivi du portefeuille confié à chaque collecteur.
- Comparaison des montants dus, encaissés et en retard.
- Tableau de performance des collecteurs dans le dashboard.
- Feuille Excel dédiée aux collecteurs.

## Pilotage du risque et reporting

- Portfolio at Risk : **PAR 1**, **PAR 30**, **PAR 60** et **PAR 90**.
- Aging du portefeuille par tranches : courant, 1–30, 31–60, 61–90 et plus de 90 jours.
- Capital exposé dans chaque tranche de retard.
- TAEG effectif moyen pondéré par le capital actif.
- Rendement du portefeuille.
- Suivi des frais enregistrés.
- Taux de récupération après défaut.
- Montants récupérés sur les prêts en défaut.
- Date du passage en défaut et solde au moment du défaut.
- Performance détaillée par collecteur.
- Nouvelles cartes et sections de reporting sur le tableau de bord.

## Prêts, paiements et cohérence comptable

- Stockage séparé du capital, des intérêts, des frais, du décaissement et du remboursement total.
- Utilisation du remboursement total pour les paiements, soldes, refinancements et prolongations.
- Allocation des paiements aux échéances avec prise en compte des paiements annulés.
- Recalcul automatique du statut du prêt après chaque paiement ou annulation.
- Passage automatique au statut payé lorsque le montant dû est totalement couvert.
- Conservation des prêts anciens grâce aux migrations et aux valeurs de repli.
- Journal d’audit des opérations métier sensibles.

## Contrats PDF et reçus

- KYC étendu dans les contrats.
- Fréquence et nombre d’échéances.
- Frais de traitement et d’assurance.
- Montant net décaissé.
- TAEG effectif.
- Garants et signatures.
- Garanties et statut des biens.
- Totaux des reçus et échéanciers alignés sur le remboursement contractuel réel.

## Exports Excel

- Colonnes KYC supplémentaires dans la feuille Clients.
- Données financières étendues dans la feuille Prêts.
- Nouvelles feuilles **Guarantors**, **Collateral** et **Collectors**.
- Export des fréquences, frais, décaissements, TAEG et affectations.
- Export complet ou sélectif conservé.

## Page À propos et contact

- Nouvelle page À propos intégrée à l’application.
- Présentation de la confidentialité, des calculs et des documents professionnels.
- Proposition d’adaptation du logiciel aux besoins particuliers d’une entreprise.
- Adresse de contact : **alain.eric@ik.me**.
- Bouton ouvrant directement la messagerie de l’utilisateur avec un message prérempli.

## Interface et cohérence linguistique

- Interface visible uniformisée en anglais.
- Suppression des mélanges français/anglais dans les boutons, messages et notifications.
- Le sélecteur de langue est maintenant clairement nommé **Donation Reminder Language**.
- Les 17 langues existantes restent disponibles pour les rappels de don.
- Réorganisation des cartes financières pour éviter les débordements de texte.
- Adaptation de l’écran de connexion aux fenêtres compactes jusqu’à 900 × 600.
- Nouveau logo cohérent dans la barre latérale et sur la page À propos.
- Correction du chargement de la page **Help & Guide**, dont le contenu dépendant de la devise est maintenant construit après l’initialisation de l’application.

## Base de données et migrations

- Nouvelles tables pour les garants, garanties et collecteurs.
- Nouvelles colonnes KYC sur les clients.
- Nouvelles colonnes financières, de fréquence, de défaut et de collecteur sur les prêts.
- Informations supplémentaires sur les pénalités automatiques.
- Index et contraintes destinés à éviter les doublons.
- Reprise automatique des valeurs des anciens prêts.
- Migrations rétrocompatibles exécutées au démarrage.
- Vérification de l’intégrité SQLite et des clés étrangères.

## Packaging et livraison

- Version applicative portée à **1.5.0**.
- Numéro de build macOS porté à **7**.
- Application installée reconstruite avec la nouvelle icône.
- Bundle Apple Silicon autonome reconstruit.
- Signature ad hoc macOS vérifiée.
- DMG ARM64 reconstruit et contrôlé par SHA-256.
- Création d’une icône Windows ICO avec les tailles 16 à 256 pixels.
- Vérification de l’absence de base client, profil ou journal dans les paquets distribués.

## Validation effectuée

- Contrôle syntaxique Python et JavaScript.
- **25 tests automatisés réussis**.
- La commande `npm test` sélectionne automatiquement l’environnement virtuel local compatible macOS, Linux ou Windows.
- Test d’une migration depuis une ancienne base mensuelle.
- Test de génération des données de démonstration.
- Test de création d’un prêt avec garant, garantie, frais, décaissement net et fréquence hebdomadaire.
- Test de l’idempotence des pénalités automatiques.
- Test du mauvais et du bon mot de passe.
- Test du verrouillage du pont API avant authentification.
- Test du verrouillage manuel de la session.
- Test de l’ouverture directe lorsque le login est désactivé.
- Contrôle visuel de l’écran de connexion en taille normale et en 900 × 600.
- Test de génération des contrats PDF et des exports Excel.
- Démarrage réel de la copie installée et du bundle autonome.
- Vérification des signatures, versions et sommes de contrôle.

## Emplacements des livrables

- Application installée : `/Users/alain/Applications/Lending Pro Freeware.app`
- DMG : `release/Lending-Pro-Freeware-macOS-arm64.dmg`
- Somme SHA-256 : `release/Lending-Pro-Freeware-macOS-arm64.dmg.sha256`
- Source du logo : `branding/lending-pro-icon-source.png`
- Logo de l’interface : `web/assets/lending-pro-mark.png`

Pour l’historique version par version, consulter également [`CHANGELOG.md`](CHANGELOG.md).
