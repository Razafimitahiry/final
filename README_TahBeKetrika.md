# 🌐 TahBeKetrika — SMM Automation Bot

Automatise la gestion des comptes **Instagram** depuis **Telegram** via le bot `@SmmKingdomTasksBot`.  
Ce script copie automatiquement les publications et stories à partir des messages reçus dans le groupe SMM.

---

## 🚀 Fonctionnalités principales

- 🤖 **Automatisation intelligente** : publie automatiquement le post et la story demandés par le message Telegram.
- 🖼️ **Comparaison entre comptes** : évite les doublons de publications.
- 🕒 **Délai humain simulé** (30 à 90 secondes) entre post et story.
- 🚦 **Système anti-blocage Instagram** (limite 5 min entre deux posts, 3 min entre deux stories).
- 💾 **Sauvegarde locale** des sessions Telegram & Instagram.
- 🔐 **Vérification de licence** et authentification sécurisée.
- 📊 **Logs verbeux** pour le suivi en temps réel.

---

## ⚙️ Installation complète

### 1️⃣ Prérequis système (Linux / macOS)
Avant tout, installez les dépendances système nécessaires :
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv libffi-dev libssl-dev build-essential -y
```

Sur macOS :
```bash
brew install python3
```

### 2️⃣ Cloner le projet
```bash
git clone https://github.com/<votre-utilisateur>/<votre-repo>.git
cd <votre-repo>
```

### 3️⃣ Créer un environnement virtuel Python
```bash
python3 -m venv venv
source venv/bin/activate  # (Linux/Mac)
venv\Scripts\activate   # (Windows)
```

### 4️⃣ Installer les dépendances Python
```bash
pip install -r requirements.txt
```

---

## 🧩 Fichier `requirements.txt`

Ce fichier contient toutes les librairies nécessaires :
```text
# Core
instagrapi==1.18.6
telethon==1.33.1
requests==2.32.3
beautifulsoup4==4.12.3
pillow>=10.3.0

# Utils & Web
urllib3>=2.0.7
certifi>=2024.2.2
idna>=3.6
charset-normalizer>=3.3.2

# Optionnel (pour compatibilité élargie)
pillow>=10.3.0
```

---

## 🔑 Configuration initiale

1. **Lancer le bot** :
   ```bash
   python tahBeKetrika_ready_for_git.py
   ```

2. Lors du premier démarrage :
   - Entrez votre **nom d’utilisateur et clé API** (licence).
   - Connectez votre **numéro Telegram** (le script crée un fichier `sessions/`).
   - Ajoutez vos comptes **Instagram** via :
     ```
     [5] Ajouter un compte Instagram par sessionid
     [6] Ajouter un compte Instagram par identifiants
     ```

3. Vos comptes sont stockés dans :
   ```
   SmmKingdomTask/Compte.txt
   ```

---

## 📱 Fonctionnement automatique

Dès qu’un message de ce type est reçu dans le groupe Telegram SMM :
```
❗️ Account jasmine_cookslife (source account : https://www.instagram.com/jazz_cancook/)

🛠New post is required! (copy from source account and add caption)
👀New story is required! (publish one of the photos as story from source account)
```

Le bot effectue automatiquement les étapes suivantes :
1. Connecte les comptes `source` et `target` depuis les sessions existantes.  
2. Compare les publications du compte source et cible.  
3. Copie **1 seul post manquant** (photo + légende).  
4. Publie une **story** avec une image aléatoire du compte source.  
5. Envoie `/fix_<target_user>` dans Telegram pour signaler la fin de la tâche.

---

## 🔒 Sécurité & Anti-blocage

- Maximum **1 post par message**.
- **Délai aléatoire (30–90s)** avant la story.
- Stockage des limites dans `SmmKingdomTask/ig_rate_limit.json`.
- Authentification vérifiée toutes les **5 minutes**.
- Sauvegarde automatique des sessions pour éviter la reconnexion fréquente.

---

## 🧾 Structure du projet

```
TahBeKetrika/
│
├── tahBeKetrika_ready_for_git.py     # Script principal
├── requirements.txt                   # Dépendances
├── README.md                          # Documentation
└── SmmKingdomTask/
    ├── Compte.txt                     # Comptes Instagram
    ├── ig_rate_limit.json             # Limites d’action
    ├── sessions/                      # Sessions Telegram/Instagram
    └── api_key.json                   # Licence et session ID
```

---

## 🧠 Commandes utiles

- 🔄 Relancer le bot :
  ```bash
  python tahBeKetrika_ready_for_git.py
  ```
- 🧹 Réinitialiser les sessions :
  ```bash
  rm -r SmmKingdomTask/sessions
  ```
- 📊 Vérifier les logs :
  ```
  tail -f logs.txt
  ```

---

## 📄 Licence

Développé par **Ketrika le développeur**  
© 2025 — Tous droits réservés.

---

## 📬 Contact

- 📧 Email : contact@ketrika.dev  
- 💬 Telegram : [@SmmKingdomTasksBot](https://t.me/SmmKingdomTasksBot)
