# SpendWise — Documentation API : Authentification & Vérification Email

Base URL (développement) : `http://localhost:8000/api/v1`

Toutes les requêtes et réponses sont au format JSON (`Content-Type: application/json`), sauf indication contraire.

---

## Sommaire

1. [Inscription](#1-inscription)
2. [Connexion](#2-connexion)
3. [Vérification de l'email (OTP)](#3-vérification-de-lemail-otp)
4. [Renvoi du code OTP](#4-renvoi-du-code-otp)
5. [Vérifier le statut de vérification](#5-vérifier-le-statut-de-vérification)
6. [Récupérer le profil connecté](#6-récupérer-le-profil-connecté)
7. [Rafraîchir l'access token](#7-rafraîchir-laccess-token)
8. [Déconnexion](#8-déconnexion)
9. [Déconnexion de tous les appareils](#9-déconnexion-de-tous-les-appareils)
10. [Mot de passe oublié](#10-mot-de-passe-oublié)
11. [Réinitialiser le mot de passe](#11-réinitialiser-le-mot-de-passe)
12. [Changer le mot de passe (connecté)](#12-changer-le-mot-de-passe-connecté)
13. [Modifier le profil](#13-modifier-le-profil)
14. [Wallets (e-wallets)](#14-wallets-e-wallets)
15. [Catégories](#15-catégories)
16. [Dépenses](#16-dépenses)
17. [Budgets](#17-budgets)
18. [Statistiques](#18-statistiques)
19. [Notifications](#19-notifications)
20. [Intelligence Artificielle](#20-intelligence-artificielle)
21. [Authentification sur les routes protégées](#21-authentification-sur-les-routes-protégées)
22. [Codes d'erreur globaux](#22-codes-derreur-globaux)
23. [Devises disponibles](#23-devises-disponibles)
24. [Icônes et couleurs de catégories disponibles](#24-icônes-et-couleurs-de-catégories-disponibles)
25. [Guide de test rapide (curl)](#25-guide-de-test-rapide-curl)

---

## 1. Inscription

**`POST /auth/register`**

Crée un compte utilisateur. Le compte est créé avec `is_verified = false`, et un code OTP à 6 caractères est automatiquement envoyé par email.

### Corps de la requête

```json
{
  "nom": "Junior Yopa",
  "email": "junior@example.com",
  "mot_de_passe": "MotDePasse123",
  "devise_preferee": "XAF",
  "langue_preferee": "fr"
}
```

### Contraintes de validation

| Champ | Règle |
|---|---|
| `nom` | 2 à 150 caractères |
| `email` | format email valide |
| `mot_de_passe` | 8 à 128 caractères, au moins 1 majuscule, au moins 1 chiffre |
| `devise_preferee` | code ISO 3 lettres existant en base (voir [section 12](#12-devises-disponibles)) |
| `langue_preferee` | `"fr"` ou `"en"` |

### Réponse succès — `201 Created`

```json
{
  "id": "ccd83220-040d-407c-9161-d1c023090dec",
  "nom": "Junior Yopa",
  "email": "junior@example.com",
  "devise_preferee": "XAF",
  "langue_preferee": "fr",
  "fuseau_horaire": "Africa/Douala",
  "is_active": true,
  "is_verified": false,
  "photo_profil_url": null,
  "telephone": null,
  "date_creation": "2026-07-24T22:10:00Z",
  "last_login": null
}
```

### Erreurs possibles

| Code | Cas |
|---|---|
| `409 Conflict` | Email déjà utilisé |
| `422 Unprocessable Entity` | Champ invalide (mot de passe trop faible, email malformé, devise inconnue) |

---

## 2. Connexion

**`POST /auth/login`**

⚠️ **Bloquée tant que l'email n'est pas vérifié** (choix de conception assumé).

### Corps de la requête

```json
{
  "email": "junior@example.com",
  "mot_de_passe": "MotDePasse123"
}
```

### Réponse succès — `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "8f3a1c9e2b7d4f6a0e5c8b2d9f1a3e7c...",
  "token_type": "bearer"
}
```

- `access_token` : durée de vie **30 minutes** — à envoyer dans le header `Authorization: Bearer <access_token>` sur les routes protégées
- `refresh_token` : durée de vie **30 jours** — à stocker de façon sécurisée (ex: secure storage mobile, cookie httpOnly web), sert uniquement à obtenir un nouvel access token

### Erreurs possibles

| Code | Cas | Message |
|---|---|---|
| `401 Unauthorized` | Email ou mot de passe incorrect | `"Email ou mot de passe incorrect"` |
| `403 Forbidden` | Email non vérifié | `"Merci de vérifier ton adresse email avant de te connecter"` |
| `403 Forbidden` | Compte désactivé | `"Ce compte a été désactivé"` |
| `423 Locked` | Trop de tentatives échouées (5 max) | `"Trop de tentatives échouées. Compte verrouillé 15 minutes."` |

**Recommandation frontend** : si `403` avec le message de vérification, rediriger automatiquement vers l'écran de saisie du code OTP (pré-remplir l'email).

---

## 3. Vérification de l'email (OTP)

**`POST /auth/verify-email`**

### Corps de la requête

```json
{
  "email": "junior@example.com",
  "otp_code": "7KXM2P"
}
```

- `otp_code` : exactement 6 caractères, alphanumériques majuscules (`A-Z`, `2-9`, sans `0`, `1`, `I`, `O` pour éviter les ambiguïtés visuelles)

### Réponse succès — `200 OK`

```json
{
  "message": "Email vérifié avec succès",
  "is_verified": true
}
```

### Erreurs possibles

| Code | Cas | Message |
|---|---|---|
| `400 Bad Request` | Code incorrect | `"Code de vérification incorrect"` |
| `400 Bad Request` | Code expiré (> 10 min) | `"Ce code a expiré, demande un nouveau code"` |
| `400 Bad Request` | Code déjà utilisé | `"Ce code a déjà été utilisé"` |
| `409 Conflict` | Email déjà vérifié | `"Cette adresse email est déjà vérifiée"` |
| `423 Locked` | 5 tentatives échouées sur ce code | `"Trop de tentatives échouées. Réessaie dans 15 minutes."` |

**Recommandation frontend** : après succès, rediriger directement vers l'écran de connexion (ou connecter automatiquement si tu ajoutes cette logique plus tard).

---

## 4. Renvoi du code OTP

**`POST /auth/resend-code`**

### Corps de la requête

```json
{
  "email": "junior@example.com"
}
```

### Réponse succès — `204 No Content`

Aucun corps de réponse. Un nouvel email avec un nouveau code est envoyé.

### Erreurs possibles

| Code | Cas | Message |
|---|---|---|
| `409 Conflict` | Email déjà vérifié | `"Cette adresse email est déjà vérifiée"` |
| `429 Too Many Requests` | Plus de 5 demandes dans l'heure | `"Trop de demandes de renvoi. Réessaie dans une heure."` |

**Recommandation frontend** : afficher un bouton "Renvoyer le code" avec un cooldown visuel (ex: 60 secondes avant de pouvoir recliquer), pour limiter les appels inutiles côté UX même si la vraie limite est gérée côté serveur.

---

## 5. Vérifier le statut de vérification

**`GET /auth/check-verification`**

🔒 Nécessite un `access_token` valide (voir [section 10](#10-authentification-sur-les-routes-protégées)).

### Réponse succès — `200 OK`

```json
{
  "email": "junior@example.com",
  "is_verified": false
}
```

**Recommandation frontend** : appeler cette route après connexion pour décider d'afficher ou non un bandeau d'incitation à vérifier l'email.

---

## 6. Récupérer le profil connecté

**`GET /auth/me`**

🔒 Nécessite un `access_token` valide.

### Réponse succès — `200 OK`

Même structure que la réponse d'inscription (section 1).

### Erreurs possibles

| Code | Cas |
|---|---|
| `401 Unauthorized` | Token manquant, invalide ou expiré |
| `403 Forbidden` | Compte désactivé |

---

## 7. Rafraîchir l'access token

**`POST /auth/refresh`**

À appeler quand l'`access_token` a expiré (après 30 min), en utilisant le `refresh_token`.

### Corps de la requête

```json
{
  "refresh_token": "8f3a1c9e2b7d4f6a0e5c8b2d9f1a3e7c..."
}
```

### Réponse succès — `200 OK`

```json
{
  "access_token": "nouveau_token...",
  "refresh_token": "nouveau_refresh_token...",
  "token_type": "bearer"
}
```

⚠️ **Important** : le `refresh_token` change à chaque appel (rotation de sécurité). L'ancien devient invalide — le frontend doit toujours stocker le **nouveau** `refresh_token` reçu, pas réutiliser l'ancien.

### Erreurs possibles

| Code | Cas |
|---|---|
| `401 Unauthorized` | Refresh token invalide, expiré, révoqué, ou déjà utilisé |

**Recommandation frontend** : intercepter les `401` sur n'importe quelle route protégée → tenter automatiquement un `/refresh` → si ça échoue aussi, déconnecter l'utilisateur et rediriger vers l'écran de connexion.

---

## 8. Déconnexion

**`POST /auth/logout`**

Révoque une session précise (l'appareil courant).

### Corps de la requête

```json
{
  "refresh_token": "8f3a1c9e2b7d4f6a0e5c8b2d9f1a3e7c..."
}
```

### Réponse succès — `204 No Content`

---

## 9. Déconnexion de tous les appareils

**`POST /auth/logout-all`**

🔒 Nécessite un `access_token` valide. Révoque toutes les sessions actives de l'utilisateur (mobile + web + autres appareils).

### Réponse succès — `204 No Content`

---

## 10. Mot de passe oublié

**`POST /auth/forgot-password`**

Déclenche l'envoi d'un code OTP par email si le compte existe. Ne révèle jamais si l'email est inconnu (réponse identique dans tous les cas).

### Corps de la requête

```json
{
  "email": "junior@example.com"
}
```

### Réponse succès — `204 No Content`

Aucun corps de réponse, que l'email existe ou non.

**Recommandation frontend** : n'affiche jamais de message différenciant "email envoyé" de "email inconnu" — affiche toujours un message neutre du type "Si ce compte existe, un code a été envoyé."

---

## 11. Réinitialiser le mot de passe

**`POST /auth/reset-password`**

### Corps de la requête

```json
{
  "email": "junior@example.com",
  "otp_code": "7KXM2P",
  "nouveau_mot_de_passe": "NouveauPass123"
}
```

### Contraintes

`nouveau_mot_de_passe` suit les mêmes règles qu'à l'inscription (8-128 caractères, au moins 1 majuscule, au moins 1 chiffre).

### Réponse succès — `204 No Content`

⚠️ Toutes les sessions actives de l'utilisateur sont révoquées après un reset réussi — l'utilisateur devra se reconnecter sur tous ses appareils.

### Erreurs possibles

Mêmes codes que la vérification d'email (section 3) : code incorrect, expiré, déjà utilisé, verrouillage anti brute-force après 5 tentatives.

---

## 12. Changer le mot de passe (connecté)

**`POST /auth/change-password`**

🔒 Nécessite un `access_token` valide.

### Corps de la requête

```json
{
  "mot_de_passe_actuel": "AncienPass123",
  "nouveau_mot_de_passe": "NouveauPass456"
}
```

### Réponse succès — `204 No Content`

⚠️ Toutes les sessions actives sont révoquées après ce changement, y compris potentiellement la session courante côté refresh token (l'access token en cours reste valide jusqu'à son expiration naturelle de 30 minutes).

### Erreurs possibles

| Code | Cas | Message |
|---|---|---|
| `400 Bad Request` | Mot de passe actuel incorrect | `"Le mot de passe actuel est incorrect"` |
| `422 Unprocessable Entity` | Nouveau mot de passe ne respecte pas les règles | détail de validation Pydantic |

---

## 13. Modifier le profil

**`PATCH /users/me`**

🔒 Nécessite un `access_token` valide.

Tous les champs sont optionnels — seuls ceux fournis sont modifiés.

### Corps de la requête (exemple partiel)

```json
{
  "nom": "Junior Yopa",
  "devise_preferee": "EUR",
  "langue_preferee": "fr",
  "telephone": "+237600000000",
  "fuseau_horaire": "Africa/Douala"
}
```

### Réponse succès — `200 OK`

Même structure que `UserResponse` (voir section 1), avec les champs mis à jour.

**Non modifiable via cette route** : `email`, `mot_de_passe`, `is_verified`, `is_active`, `is_superuser` — ces champs sont volontairement absents du schéma d'entrée.

---

## 14. Wallets (e-wallets)

🔒 Toutes les routes de cette section nécessitent un `access_token` valide **et** un compte avec email vérifié.

### 14.1 Créer un wallet

**`POST /wallets`**

```json
{
  "nom_wallet": "Espèces",
  "type_wallet": "especes",
  "solde_initial": 50000,
  "devise": "XAF"
}
```

`type_wallet` doit être exactement l'une de ces trois valeurs : `"especes"`, `"mobile_money"`, `"banque"`.

Réponse — `201 Created` :
```json
{
  "id": "uuid",
  "nom_wallet": "Espèces",
  "type_wallet": "especes",
  "solde": "50000.00",
  "devise": "XAF",
  "is_active": true,
  "created_at": "...",
  "updated_at": "..."
}
```

### 14.2 Lister les wallets

**`GET /wallets?active_only=true`**

### 14.3 Récupérer un wallet précis

**`GET /wallets/{wallet_id}`**

### 14.4 Modifier un wallet

**`PATCH /wallets/{wallet_id}`**
```json
{
  "nom_wallet": "Espèces (poche)",
  "is_active": true
}
```

### 14.5 Déposer sur un wallet

**`POST /wallets/{wallet_id}/deposit`**
```json
{
  "montant": 10000,
  "reference": "Salaire juillet"
}
```

### 14.6 Retirer d'un wallet

**`POST /wallets/{wallet_id}/withdraw`**
```json
{
  "montant": 15000,
  "reference": "Courses"
}
```

Erreur si solde insuffisant — `400 Bad Request` : `"Solde insuffisant pour effectuer cette opération"`

### 14.7 Historique des transactions

**`GET /wallets/{wallet_id}/transactions`**

Réponse : liste chronologique inversée (plus récent en premier) de chaque dépôt/retrait avec `solde_apres` (montant du solde juste après cette opération).

### Erreurs communes à toutes les routes wallet

| Code | Cas |
|---|---|
| `404 Not Found` | Wallet introuvable ou n'appartenant pas à l'utilisateur |
| `400 Bad Request` | Wallet désactivé, ou solde insuffisant |
| `403 Forbidden` | Email non vérifié |

---

## 15. Catégories

🔒 Toutes les routes nécessitent un `access_token` valide **et** un compte avec email vérifié.

### 15.1 Créer une catégorie personnalisée

**`POST /categories`**
```json
{
  "nom": "Frais universitaires",
  "icone": "education",
  "couleur": "#4f46e5"
}
```

Voir [section 19](#19-icônes-et-couleurs-de-catégories-disponibles) pour les valeurs valides d'`icone` et `couleur`.

Erreur si le nom existe déjà (par défaut ou personnalisée) — `409 Conflict` : `"Une catégorie avec ce nom existe déjà"`

### 15.2 Lister les catégories

**`GET /categories`**

Retourne les catégories par défaut (communes à tous) **et** les catégories personnalisées de l'utilisateur connecté, triées catégories par défaut en premier puis ordre alphabétique.

### 15.3 Récupérer une catégorie précise

**`GET /categories/{category_id}`**

### 15.4 Modifier une catégorie

**`PATCH /categories/{category_id}`**
```json
{
  "nom": "Frais de scolarité"
}
```

⚠️ Échoue avec `403 Forbidden` si la catégorie est une catégorie par défaut : `"Impossible de modifier ou supprimer une catégorie par défaut"`

### 15.5 Supprimer une catégorie

**`DELETE /categories/{category_id}`** → `204 No Content`

Même restriction que la modification pour les catégories par défaut.

---

## 16. Dépenses

🔒 Toutes les routes nécessitent un `access_token` valide **et** un compte avec email vérifié.

### 16.1 Créer une dépense

**`POST /expenses`**

```json
{
  "wallet_id": "uuid",
  "category_id": "uuid",
  "montant": 5000,
  "devise": "XAF",
  "description": "Courses de la semaine",
  "date_depense": "2026-07-28",
  "est_recurrente": false
}
```

- `devise` peut être différente de la devise du wallet — une conversion automatique est appliquée au débit, via le dernier taux de change synchronisé.
- Le montant enregistré dans la dépense reste toujours celui saisi par l'utilisateur, dans sa devise d'origine.

Réponse — `201 Created` :
```json
{
  "id": "uuid",
  "wallet_id": "uuid",
  "category_id": "uuid",
  "montant": "5000.00",
  "devise": "XAF",
  "description": "Courses de la semaine",
  "date_depense": "2026-07-28",
  "source": "manuelle",
  "est_recurrente": false,
  "created_at": "...",
  "updated_at": "..."
}
```

### 16.2 Lister les dépenses (avec filtres optionnels)

**`GET /expenses?category_id={id}&wallet_id={id}&date_debut=2026-07-01&date_fin=2026-07-31`**

Tous les paramètres sont optionnels et combinables.

### 16.3 Récupérer une dépense précise

**`GET /expenses/{expense_id}`**

### 16.4 Modifier une dépense

**`PATCH /expenses/{expense_id}`**

```json
{
  "category_id": "uuid",
  "description": "Nouvelle description",
  "date_depense": "2026-07-29"
}
```

⚠️ `montant`, `devise` et `wallet_id` ne sont **jamais modifiables** après création (protection contre la désynchronisation financière). Pour corriger un montant erroné, supprime la dépense et recrée-la.

### 16.5 Supprimer une dépense

**`DELETE /expenses/{expense_id}`** → `204 No Content`

⚠️ Le wallet associé est automatiquement **recrédité** du montant qui avait été débité (converti si nécessaire) — la suppression agit comme un remboursement complet.

### Erreurs communes

| Code | Cas |
|---|---|
| `404 Not Found` | Dépense, wallet ou catégorie introuvable / n'appartenant pas à l'utilisateur |
| `400 Bad Request` | Solde insuffisant sur le wallet, ou aucun taux de change disponible pour la conversion demandée |

**Recommandation frontend** : si la création échoue pour cause de taux de change manquant, afficher un message du type "Conversion temporairement indisponible pour cette devise, réessaie plus tard."

---

## 17. Budgets

🔒 Toutes les routes nécessitent un `access_token` valide **et** un compte avec email vérifié.

### 17.1 Créer un budget

**`POST /budgets`**

Budget par catégorie :
```json
{
  "category_id": "uuid",
  "montant_limite": 50000,
  "devise": "XAF",
  "periode": "mensuel",
  "date_debut": "2026-07-01"
}
```

Budget global (toutes catégories confondues) — `category_id` à `null` :
```json
{
  "category_id": null,
  "montant_limite": 200000,
  "devise": "XAF",
  "periode": "mensuel",
  "date_debut": "2026-07-01"
}
```

`periode` accepte : `"hebdomadaire"` ou `"mensuel"`.

### 17.2 Lister les budgets

**`GET /budgets`**

### 17.3 Récupérer un budget précis

**`GET /budgets/{budget_id}`**

### 17.4 Modifier un budget

**`PATCH /budgets/{budget_id}`**
```json
{
  "montant_limite": 60000
}
```

⚠️ `devise`, `periode` et `date_debut` ne sont pas modifiables — supprime et recrée le budget pour changer ces paramètres.

### 17.5 Supprimer un budget

**`DELETE /budgets/{budget_id}`** → `204 No Content`

### 17.6 Consulter la progression d'un budget

**`GET /budgets/{budget_id}/progress`**

Réponse — `200 OK` :
```json
{
  "budget_id": "uuid",
  "montant_limite": "50000.00",
  "montant_depense": "42000.00",
  "pourcentage": "84.00",
  "devise": "XAF",
  "periode_debut": "2026-07-01",
  "periode_fin": "2026-07-31",
  "seuil_80_atteint": true,
  "seuil_100_atteint": false
}
```

- `periode_debut` / `periode_fin` reflètent la fenêtre de la période **en cours**, recalculée dynamiquement à chaque appel.
- `montant_depense` agrège toutes les dépenses concernées, converties dans la devise du budget si nécessaire.

**Recommandation frontend** : afficher une barre de progression colorée (verte < 80%, orange entre 80-100%, rouge ≥ 100%) en te basant directement sur `seuil_80_atteint` et `seuil_100_atteint`.

---

## 18. Statistiques

🔒 Toutes les routes nécessitent un `access_token` valide **et** un compte avec email vérifié.

### 18.1 Répartition par catégorie

**`GET /statistics/by-category?date_debut=2026-07-01&date_fin=2026-07-31&devise=XAF`**

`devise` est optionnel — si omis, utilise `devise_preferee` du profil utilisateur.

Réponse — `200 OK` :
```json
{
  "devise": "XAF",
  "periode_debut": "2026-07-01",
  "periode_fin": "2026-07-31",
  "total_general": "45000.00",
  "repartition": [
    {
      "category_id": "uuid",
      "category_nom": "Alimentation",
      "category_icone": "restaurant",
      "category_couleur": "#f59e0b",
      "montant_total": "35000.00",
      "pourcentage": "77.78"
    }
  ]
}
```

### 18.2 Évolution mensuelle

**`GET /statistics/monthly-evolution?annee=2026&devise=XAF`**

Réponse — `200 OK` :
```json
{
  "devise": "XAF",
  "points": [
    {"mois": "2026-01", "montant_total": "0.00"},
    {"mois": "2026-07", "montant_total": "45000.00"}
  ]
}
```

Retourne toujours 12 points (janvier à décembre), y compris les mois sans dépense.

### 18.3 Résumé comparatif

**`GET /statistics/summary?date_debut=2026-07-01&date_fin=2026-07-31&devise=XAF`**

Réponse — `200 OK` :
```json
{
  "devise": "XAF",
  "periode_debut": "2026-07-01",
  "periode_fin": "2026-07-31",
  "total_periode": "45000.00",
  "total_periode_precedente": "30000.00",
  "evolution_pourcentage": "50.00",
  "categorie_principale_nom": "Alimentation",
  "categorie_principale_montant": "35000.00"
}
```

`total_periode_precedente` compare à une période de durée identique juste avant celle demandée (pas forcément "le mois dernier" au sens calendaire strict).

### Erreurs communes

| Code | Cas | Message |
|---|---|---|
| `400 Bad Request` | Aucune devise fournie et aucune devise préférée définie | `"Aucune devise de référence définie..."` |

---

## 19. Notifications

### 19.1 Lister les notifications

**`GET /notifications?unread_only=false`**

🔒 Nécessite un `access_token` valide (email vérifié non requis).

Réponse — `200 OK` :
```json
[
  {
    "id": "uuid",
    "type": "budget_seuil_80",
    "titre": "Budget à 80%",
    "message": "Tu as atteint 85.00% de ton budget (8500.00 XAF sur 10000.00 XAF).",
    "reference_id": "uuid_du_budget",
    "lu": false,
    "date": "2026-07-28T14:30:00Z"
  }
]
```

`type` possibles : `budget_seuil_80`, `budget_seuil_100`, `rappel_facture`, `resume_mensuel`, `systeme`. `reference_id` pointe vers l'entité concernée (ex: un budget) — son interprétation dépend du `type`.

### 19.2 Compteur de notifications non lues

**`GET /notifications/unread-count`**

Réponse — `200 OK` :
```json
{"count": 3}
```

**Recommandation frontend** : idéal pour afficher un badge numérique sur une icône de cloche.

### 19.3 Marquer une notification comme lue

**`PATCH /notifications/{notification_id}/read`** → `200 OK`, renvoie la notification mise à jour.

### 19.4 Marquer toutes les notifications comme lues

**`PATCH /notifications/read-all`** → `204 No Content`

---

## 20. Intelligence Artificielle

🔒 Toutes les routes nécessitent un `access_token` valide **et** un compte avec email vérifié.

⚠️ Toutes les routes de cette section partagent un **quota quotidien de 50 appels par utilisateur**, réinitialisé chaque jour.

### 20.1 Suggérer une catégorie pour une dépense

**`POST /ai/suggest-category`**

```json
{
  "description": "Facture Eneo électricité"
}
```

Réponse succès — `200 OK` :
```json
{
  "category_id": "uuid",
  "category_nom": "Factures",
  "confiance": 0.98
}
```

Si l'IA est indisponible, incertaine, ou hallucine une catégorie inexistante — `200 OK` avec corps `null` :
```json
null
```

**Recommandation frontend** : si la réponse est `null`, afficher simplement le sélecteur de catégorie manuel, sans message d'erreur alarmant — c'est un comportement normal et attendu.

### 20.2 Poser une question au chatbot financier

**`POST /ai/chat`**

```json
{
  "question": "Combien j'ai dépensé en alimentation ce mois-ci ?"
}
```

Réponse — `200 OK` :
```json
{
  "reponse": "Ce mois-ci, tu as dépensé 42000 XAF en Alimentation."
}
```

### Exemples de questions reconnues

| Type de question | Exemple |
|---|---|
| Total par catégorie | "Combien j'ai dépensé en transport ce mois-ci ?" |
| Total général | "Combien j'ai dépensé au total ce mois-ci ?" |
| Catégorie principale | "Quelle est ma plus grosse dépense ce mois-ci ?" |
| Progression de budget | "Où en suis-je sur mon budget alimentation ?" |

Périodes reconnues dans la question : "ce mois-ci" (par défaut), "le mois dernier", "cette semaine".

### Comportement hors périmètre

- **Question financière non couverte** (ex: "quelle est ma dépense la moins chère ?") → réponse invitant à consulter les statistiques détaillées de l'application.
- **Question hors sujet** (ex: "quelle est la capitale du Cameroun ?") → réponse de recadrage rappelant que l'assistant ne traite que des finances personnelles, sans jamais répondre à la question hors-sujet elle-même.

### Erreurs communes

| Code | Cas |
|---|---|
| `429 Too Many Requests` | Quota quotidien de 50 appels IA atteint |

**Recommandation frontend** : afficher un indicateur de chargement pendant l'appel (peut prendre jusqu'à 10-12 secondes en cas de lenteur du fournisseur IA), et prévoir un état "réessaie plus tard" propre en cas de `429`.

---

## 21. Authentification sur les routes protégées

Pour toute route marquée 🔒, ajoute ce header à la requête :

```
Authorization: Bearer <access_token>
```

Exemple avec `fetch` (JavaScript / Next.js) :

```javascript
const response = await fetch("http://localhost:8000/api/v1/auth/me", {
  headers: {
    "Authorization": `Bearer ${accessToken}`
  }
});
```

Exemple avec Dio (Flutter) :

```dart
final response = await dio.get(
  '/auth/me',
  options: Options(headers: {'Authorization': 'Bearer $accessToken'}),
);
```

---

## 22. Codes d'erreur globaux

Toutes les erreurs suivent le format standard FastAPI :

```json
{
  "detail": "Message d'erreur en français"
}
```

Sauf les erreurs de validation (`422`), qui suivent le format Pydantic :

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "mot_de_passe"],
      "msg": "Value error, Le mot de passe doit contenir au moins une majuscule",
      "input": "password123"
    }
  ]
}
```

| Code HTTP | Signification générale |
|---|---|
| `400` | Requête invalide (données incorrectes métier) |
| `401` | Non authentifié / token invalide |
| `403` | Authentifié mais accès refusé (compte désactivé, email non vérifié) |
| `409` | Conflit (email déjà utilisé, déjà vérifié) |
| `422` | Erreur de validation des champs |
| `423` | Compte ou code temporairement verrouillé |
| `429` | Trop de requêtes (limite de renvoi de code) |
| `500` | Erreur serveur inattendue |

---

## 23. Devises disponibles

Actuellement en base (table `devises`) :

| Code | Nom | Symbole |
|---|---|---|
| `XAF` | Franc CFA (BEAC) | FCFA |
| `EUR` | Euro | € |
| `USD` | Dollar américain | $ |
| `GBP` | Livre sterling | £ |
| `NGN` | Naira nigérian | ₦ |

*(Un endpoint `GET /devises` sera ajouté pour que le frontend récupère cette liste dynamiquement plutôt que de la coder en dur.)*

---

## 24. Icônes et couleurs de catégories disponibles

### Icônes valides (`icone`)

`restaurant`, `transport`, `logement`, `sante`, `education`, `loisirs`, `shopping`, `factures`, `abonnement`, `voyage`, `cadeau`, `epargne`, `famille`, `animaux`, `sport`, `beaute`, `assurance`, `impots`, `don`, `autre`

**Recommandation frontend** : maintenir une correspondance locale entre ces codes texte et une bibliothèque d'icônes (ex: `lucide-react`, `flutter_icons`) — par exemple `"restaurant"` → icône de couverts.

### Couleurs valides (`couleur`)

| Code hexadécimal | Nom |
|---|---|
| `#2563eb` | Bleu |
| `#dc2626` | Rouge |
| `#059669` | Vert |
| `#f59e0b` | Orange |
| `#7c3aed` | Violet |
| `#db2777` | Rose |
| `#eab308` | Jaune |
| `#6b7280` | Gris |
| `#0891b2` | Cyan |
| `#4f46e5` | Indigo |

### Catégories par défaut déjà présentes en base

Alimentation, Transport, Logement, Santé, Éducation, Loisirs, Shopping, Factures, Abonnements, Voyage, Cadeaux, Épargne, Famille, Sport, Assurance, Impôts, Dons, Autre — non modifiables ni supprimables par les utilisateurs.

---

## 25. Guide de test rapide (curl)

```bash
# 1. Inscription
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"nom":"Test User","email":"test@example.com","mot_de_passe":"Password123","devise_preferee":"XAF","langue_preferee":"fr"}'

# 2. Tentative de connexion (doit échouer, email non vérifié)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","mot_de_passe":"Password123"}'

# 3. Vérification (remplace CODE par le code reçu par email)
curl -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","otp_code":"CODE"}'

# 4. Connexion (doit réussir maintenant)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","mot_de_passe":"Password123"}'

# 5. Profil (remplace TOKEN par l'access_token reçu à l'étape 4)
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer TOKEN"
```

---

## Résumé du flux complet pour le frontend

```
Inscription (register)
        │
        ▼
Écran "Vérifie ton email" ◄──── code envoyé automatiquement
        │
        ├── Saisie code → verify-email → succès → Écran de connexion
        │
        └── "Renvoyer le code" → resend-code (max 5/heure)
        │
        ▼
Connexion (login)
        │
        ├── 403 email non vérifié → retour écran de vérification
        ├── 423 compte verrouillé → afficher message, attendre 15 min
        └── 200 succès → stocker access_token + refresh_token → Dashboard
        │
        ▼
Sur chaque requête protégée :
        ├── 200 → continuer normalement
        └── 401 → tenter /refresh automatiquement
                    ├── succès → réessayer la requête originale
                    └── échec → déconnexion + retour écran de connexion
```
