# 📌 Workflow Git - SpendWise

Ce projet suit un workflow basé sur :

- `main` : Versions stables et publiées.
- `dev` : Branche d'intégration.
- `feature/*` : Une branche par fonctionnalité.

---

# Arborescence des branches

```
main
│
└── dev
    ├── feature/project-setup
    ├── feature/auth
    ├── feature/users
    ├── feature/categories
    ├── feature/income
    ├── feature/expense
    ├── feature/budget
    ├── feature/email
    ├── feature/notification
    ├── feature/statistics
    ├── feature/ai
    └── feature/report
```

---

# Avant de commencer une nouvelle fonctionnalité

Se placer dans le projet

```bash
cd ~/SpendWise
```

Activer l'environnement virtuel

```bash
source /chemin/vers/le/venv/bin/activate
```

Se placer sur la branche de développement

```bash
git switch dev
```

Récupérer les dernières modifications

```bash
git pull
```

Créer une nouvelle branche

Exemple :

```bash
git switch -c feature/auth
```

---

# Pendant le développement

Coder normalement.

Vérifier régulièrement les fichiers modifiés

```bash
git status
```

---

# Fin du développement de la fonctionnalité

Ajouter les modifications

```bash
git add .
```

Créer un commit

```bash
git commit -m "feat(auth): ajout de l'authentification JWT"
```

Envoyer la branche

```bash
git push -u origin feature/auth
```

---

# Fusion dans dev

Revenir sur dev

```bash
git switch dev
```

Mettre dev à jour

```bash
git pull
```

Fusionner la fonctionnalité

```bash
git merge feature/auth
```

Envoyer dev

```bash
git push
```

---

# Nettoyage

Supprimer la branche locale

```bash
git branch -d feature/auth
```

Supprimer la branche distante

```bash
git push origin --delete feature/auth
```

---

# Publication d'une nouvelle version

Basculer sur main

```bash
git switch main
```

Mettre main à jour

```bash
git pull
```

Fusionner dev

```bash
git merge dev
```

Publier

```bash
git push
```

Retourner sur dev

```bash
git switch dev
```

---

# Vérifications utiles

Branche courante

```bash
git branch
```

Etat du projet

```bash
git status
```

Historique

```bash
git log --oneline --graph --all
```

Branches locales

```bash
git branch
```

Branches distantes

```bash
git branch -r
```

Toutes les branches

```bash
git branch -a
```

---

# Convention des commits

Nouvelle fonctionnalité

```text
feat(auth): ajout de la connexion JWT
```

Correction de bug

```text
fix(expense): correction du calcul des dépenses
```

Refactorisation

```text
refactor(database): réorganisation des services
```

Documentation

```text
docs(readme): mise à jour de la documentation
```

Tests

```text
test(auth): ajout des tests utilisateurs
```

Maintenance

```text
chore(project): mise à jour des dépendances
```

Optimisation

```text
perf(statistics): amélioration des performances
```

Suppression

```text
remove(notification): suppression de l'ancien service
```

---

# Règles du projet

✅ Toujours créer une branche `feature/*` depuis `dev`.

✅ Ne jamais développer directement sur `dev`.

✅ Ne jamais développer directement sur `main`.

✅ Une fonctionnalité = une branche.

✅ Une branche terminée est fusionnée dans `dev` puis supprimée.

✅ `main` ne contient que des versions stables.

---

# Exemple complet

```bash
git switch dev

git pull

git switch -c feature/auth

# Développement...

git status

git add .

git commit -m "feat(auth): création du système JWT"

git push -u origin feature/auth

git switch dev

git pull

git merge feature/auth

git push

git branch -d feature/auth

git push origin --delete feature/auth
```