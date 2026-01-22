# 👤 Guide de Gestion des Utilisateurs et des Rôles

Ce guide explique comment administrer les utilisateurs dans le système **Execution PM** et comment attribuer les responsabilités (Rôles) via l'interface standard d'Odoo.

---

## 🛠️ 1. Accès à la Gestion des Utilisateurs

Pour gérer qui a accès au système et avec quels droits :
1. activez le **Mode Développeur** dans les paramètres d'Odoo (recommandé pour voir tous les groupes).
2. Allez dans le menu **Paramètres > Utilisateurs et Sociétés > Utilisateurs**.
3. Sélectionnez un utilisateur existant ou cliquez sur **Nouveau**.

---

## 🎭 2. Les Rôles (Groupes de Sécurité)

Dans la fiche de l'utilisateur, sous l'onglet **Droits d'Accès**, recherchez la section **Execution PM**. Vous y trouverez les rôles suivants :

| Nom du Groupe (Odoo) | Rôle Métier | Droits Principaux |
| :--- | :--- | :--- |
| **Contractor (Declare)** | **Entrepreneur / Entreprise** | Créer des plannings (brouillon), Saisir des avancements, Ajouter des documents. |
| **Control Office (Review)** | **Bureau de Contrôle / Surveillant** | Consulter tout, ajouter des commentaires de révision, aider à la vérification. |
| **PMO (Validate)** | **Ingénieur Conseil / Chef PMO** | Approuver les plannings, Valider les avancements, Modifier les dates. |
| **Authority (Read-Only)** | **Ministère / Direction Générale** | Vue globale sur tous les tableaux de bord et projets, mais **aucune modification** possible. |
| **Administrator** | **Service Informatique / Admin** | Configurer les types de projets, les secteurs, les seuils d'alertes et la maintenance. |
| **User** | *Accès de Base* | Rôle de base pour voir l'application. Hérité automatiquement par tous les autres. |

---

## 🔐 3. Le "Filtre Automatique" (Record Rules)

Le système ne se contente pas de limiter les boutons (cliquer ou pas), il limite aussi ce que l'utilisateur **voit** à l'écran :

*   **Règle "Projets de l'Entrepreneur" :** Un utilisateur avec le rôle **Contractor** ne verra dans sa liste que les projets où son entreprise est sélectionnée dans le champ "Main Contractor" sur la fiche projet.
*   **Règle "Lecture Seule" :** L'utilisateur **Authority** peut ouvrir n'importe quel projet, mais Odoo masquera tous les boutons d'édition (Sauvegarder, Créer, Valider).
*   **Règle "Validation Croisée" :** Un validateur (PMO) ne peut pas valider une déclaration qu'il aurait créée lui-même (si le cas se présente), garantissant la séparation des pouvoirs.

---

## 📝 4. Processus de Création d'un Nouvel Utilisateur

Voici la procédure recommandée pour intégrer un membre de l'équipe :

1.  **Création du Contact :** Créez d'abord la fiche dans **Contacts** (ex: "Entreprise ABC" ou "M. Diallo").
2.  **Création de l'Utilisateur :** Créez l'utilisateur avec son adresse email.
3.  **Assignation du Rôle :**
    - Pour un ingénieur de suivi : Choisissez **Control Office**.
    - Pour le signataire final : Choisissez **PMO**.
    - Pour le client : Choisissez **Authority**.
4.  **Liaison au Projet :** 
    - Allez sur le **Projet** concerné.
    - Dans l'onglet **Équipe**, ajoutez l'utilisateur ou assurez-vous que son entreprise est bien dans le champ **Main Contractor**.

---

## 💡 5. Questions Fréquentes

**Q: Pourquoi mon entrepreneur ne voit aucun projet ?**  
*R: Vérifiez qu'il possède bien le rôle "Contractor (Declare)" ET que son entreprise est bien renseignée comme "Main Contractor" sur le projet cible.*

**Q: Est-ce qu'un utilisateur peut avoir deux rôles ?**  
*R: Oui, mais Odoo appliquera le rôle le plus élevé. Par exemple, un Manager (PMO) possède par défaut tous les droits du Bureau de Contrôle.*

**Q: Comment bloquer un accès immédiatement ?**  
*R: Désactivez simplement l'utilisateur dans les paramètres, ou retirez tous les groupes sous la section "Execution PM".*
