# 🏷️ Castorama Price Watcher — Guide de déploiement

## Ce que tu vas mettre en place

Un bot qui vérifie le prix d'un article Castorama **toutes les heures** et t'envoie un message WhatsApp dès que le prix baisse. Tout tourne gratuitement sur GitHub, sans serveur.

---

## Étape 1 — Créer un compte GitHub

1. Va sur **https://github.com/signup**
2. Choisis un nom d'utilisateur, email, mot de passe
3. Valide ton email

---

## Étape 2 — Créer le dépôt

1. Une fois connecté, clique sur **"New repository"** (bouton vert en haut à droite)
2. Nom du dépôt : `castorama-watcher`
3. Laisse le reste par défaut, clique **"Create repository"**

---

## Étape 3 — Uploader les fichiers

Dans ton nouveau dépôt, clique sur **"uploading an existing file"** et uploade :

- `check_price.py`
- `requirements.txt`

Ensuite crée le dossier `.github/workflows/` :
1. Clique **"Add file" → "Create new file"**
2. Dans le nom, tape : `.github/workflows/price_watcher.yml`
3. Copie-colle le contenu du fichier `price_watcher.yml`
4. Clique **"Commit changes"**

---

## Étape 4 — Configurer Twilio (WhatsApp)

### 4a. Créer un compte Twilio
1. Va sur **https://www.twilio.com/try-twilio**
2. Inscris-toi gratuitement (pas de CB requise)

### 4b. Activer le Sandbox WhatsApp
1. Dans la console Twilio, cherche **"Messaging" → "Try it out" → "Send a WhatsApp message"**
2. Sur ton téléphone, envoie le message indiqué (ex: `join sandy-tiger`) au numéro Twilio : **+1 415 523 8886**
3. Tu reçois une confirmation → le sandbox est actif ✅

### 4c. Récupérer tes identifiants Twilio
Dans le dashboard Twilio (https://console.twilio.com) :
- **Account SID** : commence par `AC...`
- **Auth Token** : clique sur l'œil pour le révéler

---

## Étape 5 — Ajouter les secrets dans GitHub

Dans ton dépôt GitHub :
1. Va dans **Settings → Secrets and variables → Actions**
2. Clique **"New repository secret"** et ajoute ces 4 secrets :

| Nom | Valeur |
|-----|--------|
| `PRODUCT_URL` | L'URL complète de l'article Castorama à surveiller |
| `TWILIO_ACCOUNT_SID` | Ton Account SID Twilio (ex: `ACxxxxxxxx`) |
| `TWILIO_AUTH_TOKEN` | Ton Auth Token Twilio |
| `TO_WHATSAPP_NUMBER` | Ton numéro au format `whatsapp:+33612345678` |

---

## Étape 6 — Tester manuellement

1. Dans ton dépôt, va dans l'onglet **"Actions"**
2. Clique sur **"Castorama Price Watcher"** dans la liste
3. Clique **"Run workflow" → "Run workflow"**
4. Regarde les logs → tu dois voir le prix affiché ✅

---

## C'est tout ! 🎉

Le bot tournera désormais **toutes les heures automatiquement**.
Tu recevras un WhatsApp uniquement quand le prix baisse.

---

## ⚠️ Notes importantes

- **Sandbox Twilio** : le destinataire doit d'abord envoyer le message de jointure (étape 4b). Pour plusieurs personnes, chacun doit le faire.
- **Limite gratuite Twilio** : largement suffisante pour un usage perso.
- **Si le prix n'est pas détecté** : Castorama peut avoir changé son HTML. Ouvre une issue sur ton dépôt ou modifie les sélecteurs dans `check_price.py`.
