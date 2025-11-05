#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tahBeKetrika.py - corrected full script with account() function integrated.
Generated for user; includes auto post/story feature and rate limits.
"""

import os
import sys
import re
import time
import json
import random
import threading
import requests
import platform
import sqlite3
import hashlib
import uuid
from uuid import uuid4
from datetime import datetime, timedelta
# instagrapi and telethon are imported at runtime when the script is executed on the user's system
# to avoid executing heavy imports in this environment, they remain in the script text below.

# Colors
vi='\\033[1;35m'; R='\\033[1;91m'; V='\\033[1;92m'; J='\\033[1;33m'; B='\\033[1;97m'; o=\"\\x1b[38;5;214m\"; S='\\033[0m'; Bl='\\033[1;34m'; c='\\033[7;96m'; r='\\033[7;91m'; co='\\033[1;46m'

# --- Config and paths ---
SERVER_URL = \"https://tahbeketrika.pythonanywhere.com/\"
API_KEY_FILE = \"api_key.json\"
SESSION_FILE = \"session_id.txt\"
BASE_DIR = os.path.join(os.path.dirname(__file__), \"SmmKingdomTask\")
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)
IG_SESSION_DIR = os.path.join(BASE_DIR, \"ig_sessions\")
os.makedirs(IG_SESSION_DIR, exist_ok=True)
ON_HOLD_FILE = os.path.join(BASE_DIR, \"on_hold_accounts.txt\")
RATE_LIMIT_FILE = os.path.join(BASE_DIR, \"ig_rate_limit.json\")
ACTION_STATE_FILE = os.path.join(BASE_DIR, 'action_state.json')
DAILY_STATE_FILE = os.path.join(BASE_DIR, 'daily_state.json')
ON_HOLD_ACTION_FILE = os.path.join(BASE_DIR, 'on_hold_action.json')

# Telegram API (example placeholders - keep real values)
api_id = 2040
api_hash = \"b18441a1ff607e10a989891a5462e627\"
session = \"sessions\"

# Globals
clien = []
accounts_with_no_tasks = []
DAYS_LEFT = None

logo = f\"\"\"{o}═════════════════════════════════════════
{vi}┌────────────────────────────────┐
│   _     _     _     _     _    │
│  / \\   / \\   / \\   / \\   / \\   │
│ ( T ) ( A ) ( H ) ( B ) ( E )  │
│  \\_/   \\_/   \\_/   \\_/   \\_/   │
│                                │
│   _     _     _     _     _    │
│  / \\   / \\   / \\   / \\   / \\   │
│ ( K ) ( E ) ( T ) ( R ) ( K )  │
│  \\_/   \\_/   \\_/   \\_/   \\_/   │
│                                │
│                                │
└────────────────────────────────┘{V}2025
{o}═════════════════════════════════════════
{B}[{V}•{B}]{o}Développeur    {B}==  {vi}ketrika le développeur
{B}[{V}•{B}]{o}Version       {B}==  {vi}Payant 
{B}[{V}•{B}]{o}Tah         {B}==  {vi}Tah@Ketrika
{B}[{V}•{B}]{o}Bot Tah     {B}==  {vi}SmmKingdomTask {V}V{J}Turbo
{o}═════════════════════════════════════════\"\"\"

# ---------------- Utility functions -----------------

def get_device_id():
    try:
        raw_id = f\"{platform.node()}-{uuid.getnode()}\"
        device_id = hashlib.sha256(raw_id.encode()).hexdigest()[:20]
        return device_id
    except Exception:
        return \"unknown_device\"

def clear_credentials():
    if os.path.exists(API_KEY_FILE):
        os.remove(API_KEY_FILE)
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

def load_credentials():
    if os.path.exists(API_KEY_FILE):
        try:
            with open(API_KEY_FILE, \"r\") as f:
                return json.load(f)
        except Exception:
            clear_credentials()
    return None

def save_credentials(username, api_key, session_id, device_id):
    credentials = {\"username\": username, \"api_key\": api_key, \"session_id\": session_id, \"device_id\": device_id, \"verified_at\": datetime.now().isoformat()}
    with open(API_KEY_FILE, \"w\") as f:
        json.dump(credentials, f)

def update_days_left(expires_at: str):
    global DAYS_LEFT
    try:
        if not expires_at:
            DAYS_LEFT = None
            return
        exp_date = datetime.fromisoformat(expires_at)
        now = datetime.utcnow()
        diff = exp_date - now
        DAYS_LEFT = diff.days
    except Exception:
        DAYS_LEFT = None

def get_days_left_str():
    global DAYS_LEFT
    if DAYS_LEFT is None:
        return \"\\033[1;92mAbonnement actif\\033[0m\"
    elif DAYS_LEFT < 0:
        return \"\\033[1;91m[EXPIRE]\\033[0m\"
    elif DAYS_LEFT == 0:
        return \"\\033[1;93mExpire aujourd'hui\\033[0m\"
    else:
        return f\"\\033[1;93m{DAYS_LEFT} jour(s) restant(s)\\033[0m\"

def human_delay(min_sec=1, max_sec=3):
    time.sleep(random.uniform(min_sec, max_sec))

# ---------------- Rate limit helpers -----------------

def _load_rate_limits():
    if os.path.exists(RATE_LIMIT_FILE):
        try:
            with open(RATE_LIMIT_FILE, \"r\") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_rate_limits(data):
    with open(RATE_LIMIT_FILE, \"w\") as f:
        json.dump(data, f)

def _can_post(username, action):
    data = _load_rate_limits()
    now = time.time()
    if username not in data:
        data[username] = {}
    last_time = data[username].get(action, 0)
    if action == \"post\" and now - last_time < 300:  # 5 min
        print(f\"{J}[AUTO] ⏳ Attente requise avant nouveau post pour {username}{S}\")
        return False
    if action == \"story\" and now - last_time < 180:  # 3 min
        print(f\"{J}[AUTO] ⏳ Attente requise avant nouvelle story pour {username}{S}\")
        return False
    data[username][action] = now
    _save_rate_limits(data)
    return True

# ---------------- IG session & helpers -----------------

def get_password_for_username(username):
    compte_path = os.path.join(BASE_DIR, \"Compte.txt\")
    if not os.path.exists(compte_path):
        return None
    with open(compte_path, 'r') as f:
        for line in f:
            if '|' in line:
                user, pwd = line.strip().split('|', 1)
                if user == username:
                    return pwd
    return None

def ig_connect(username, password=None):
    # import here to avoid failing when not installed in the environment where file is created
    from instagrapi import Client
    session_file = os.path.join(IG_SESSION_DIR, f\"{username}.json\")
    cl = Client()
    if os.path.exists(session_file):
        try:
            cl.load_settings(session_file)
            if not cl.user_id:
                if password:
                    cl.login(username, password)
                    cl.dump_settings(session_file)
                else:
                    raise Exception(\"Mot de passe requis pour la première connexion.\")
        except Exception as e:
            print(f\"{R}Erreur de chargement de session, reconnexion: {e}{S}\")
            if password:
                cl = Client()
                cl.login(username, password)
                cl.dump_settings(session_file)
            else:
                raise Exception(\"Mot de passe requis pour la reconnexion.\")
    else:
        if not password:
            raise Exception(\"Mot de passe requis pour la première connexion.\")
        cl.login(username, password)
        cl.dump_settings(session_file)
    return cl

# ---------------- Auto post/story function -----------------

def auto_story_post_request(message_text):
    try:
        match = re.search(r'Account\\s+(\\w+)\\s+\\(source account :\\s*(https://www\\.instagram\\.com/[^)]+)\\)', message_text)
        if not match:
            return

        target_user = match.group(1).strip()
        source_url = match.group(2).strip().rstrip('/')
        source_user = source_url.split('/')[-1]

        print(f\"{o}[AUTO] 🔍 Traitement automatique: target={target_user}, source={source_user}{S}\")

        target_pwd = get_password_for_username(target_user)
        source_pwd = get_password_for_username(source_user)

        try:
            cl_target = ig_connect(target_user, password=target_pwd) if target_pwd else ig_connect(target_user)
        except Exception as e:
            print(f\"{J}[AUTO] Impossible de se connecter à target {target_user}: {e}{S}\")
            cl_target = None

        try:
            cl_source = ig_connect(source_user, password=source_pwd) if source_pwd else ig_connect(source_user)
        except Exception as e:
            print(f\"{J}[AUTO] Impossible de se connecter à source {source_user}: {e}{S}\")
            cl_source = None

        if cl_target is None or cl_source is None:
            print(f\"{R}[AUTO] Connexion manquante pour source ou target. Abandon.{S}\")
            return

        try:
            src_user_id = cl_source.user_id_from_username(source_user)
            src_medias = cl_source.user_medias(src_user_id, 5)
        except Exception as e:
            print(f\"{R}[AUTO] Erreur récupération medias source: {e}{S}\")
            src_medias = []

        try:
            tgt_user_id = cl_target.user_id_from_username(target_user)
            tgt_medias = cl_target.user_medias(tgt_user_id, 20)
        except Exception as e:
            print(f\"{J}[AUTO] Erreur récupération medias target: {e}{S}\")
            tgt_medias = []

        target_signatures = set()
        for m in tgt_medias:
            try:
                sig = getattr(m, 'pk', None) or getattr(m, 'thumbnail_url', None) or str(getattr(m, 'id', ''))
                if sig:
                    target_signatures.add(str(sig))
            except:
                continue

        posted = False
        for media in src_medias:
            try:
                sig = str(getattr(media, 'pk', None) or getattr(media, 'thumbnail_url', None) or '')
                if sig in target_signatures:
                    continue

                caption = getattr(media, 'caption_text', '') or ''

                photo_url = getattr(media, 'thumbnail_url', None)
                if not photo_url:
                    try:
                        info = cl_source.media_info(media.pk)
                        photo_url = getattr(info, 'thumbnail_url', None)
                    except Exception:
                        photo_url = None

                if not photo_url:
                    print(f\"{J}[AUTO] Aucun URL dispo pour media {media}. Pass.{S}\")
                    continue

                if not _can_post(target_user, \"post\"):
                    print(f\"{J}[AUTO] Publication post sautée (limite temporelle){S}\")
                    break

                photo_path = os.path.join('/tmp', f\"{uuid.uuid4()}.jpg\")
                try:
                    with open(photo_path, 'wb') as f:
                        f.write(requests.get(photo_url, timeout=20).content)
                except Exception as e:
                    print(f\"{J}[AUTO] Erreur téléchargement image: {e}{S}\")
                    try: os.remove(photo_path)
                    except: pass
                    continue

                try:
                    print(f\"{V}[AUTO] 🖼️ Upload en cours...{S}\")
                    cl_target.photo_upload(photo_path, caption)
                    print(f\"{V}[AUTO] ✅ Posté 1 publication sur {target_user}{S}\")
                    posted = True
                except Exception as e:
                    print(f\"{R}[AUTO] Erreur upload post: {e}{S}\")
                finally:
                    try: os.remove(photo_path)
                    except: pass

                pause = random.randint(30, 90)
                print(f\"{B}[AUTO] ⏱️ Pause {pause}s avant story...{S}\")
                time.sleep(pause)
                break

            except Exception as e:
                print(f\"{J}[AUTO] Exception lors du traitement d'un media: {e}{S}\")
                continue

        if src_medias and _can_post(target_user, \"story\"):
            try:
                story_media = random.choice(src_medias)
                story_url = getattr(story_media, 'thumbnail_url', None)
                if not story_url:
                    try:
                        info = cl_source.media_info(story_media.pk)
                        story_url = getattr(info, 'thumbnail_url', None)
                    except:
                        story_url = None

                if story_url:
                    story_path = os.path.join('/tmp', f\"story_{uuid.uuid4()}.jpg\")
                    with open(story_path, 'wb') as f:
                        f.write(requests.get(story_url, timeout=20).content)
                    try:
                        print(f\"{V}[AUTO] 📲 Upload story...{S}\")
                        cl_target.photo_upload_to_story(story_path)
                        print(f\"{V}[AUTO] ✅ Story publiée sur {target_user}{S}\")
                    except Exception as e:
                        print(f\"{J}[AUTO] Erreur publication story: {e}{S}\")
                    finally:
                        try: os.remove(story_path)
                        except: pass
            except Exception as e:
                print(f\"{J}[AUTO] Erreur lors de la story: {e}{S}\")

        try:
            client = clien[0]
            channel_entity = client.get_entity(\"@SmmKingdomTasksBot\")
            client.send_message(entity=channel_entity, message=f\"/fix_{target_user}\")
            print(f\"{V}[AUTO] /fix_{target_user} envoyé.{S}\")
        except Exception as e:
            print(f\"{J}[AUTO] Impossible d'envoyer /fix_{target_user} : {e}{S}\")

    except Exception as e:
        print(f\"{R}[AUTO] Erreur critique dans auto_story_post_request: {e}{S}\")


# ---------------- Telegram message helpers -----------------

# The function 'message' returns the latest relevant message text from the bot history
def message():
    global clien
    client = clien[0]
    try:
        channel_entity = client.get_entity(\"@SmmKingdomTasksBot\")
        posts = client(GetHistoryRequest(peer=channel_entity, limit=10, add_offset=0, max_id=0, min_id=0, hash=0))
        for p in range(len(posts.messages)):
            msg = posts.messages[p].message or ''
            if any(skip in msg for skip in [\"Thank you\",\"WAS NOT rewarded\",\"is not approved\",\"Account was passed\",\"on review now\"]):
                continue
            return msg
    except Exception as e:
        print(f\"{J}Erreur lecture messages Telegram: {e}{S}\")
    return \"\"

# ---------------- New account() function (reads messages and triggers auto) -----------------

def account():
    global clien, accounts_with_no_tasks
    client = clien[0]
    load_on_hold_accounts()
    print(f\"{V}Mode account() lancé — écoute des messages SmmKingdomTasksBot...{S}\")

    try:
        channel_entity = client.get_entity(\"@SmmKingdomTasksBot\")
    except Exception as e:
        print(f\"{R}Impossible de trouver le bot @SmmKingdomTasksBot: {e}{S}\")
        return

    while True:
        try:
            # send trigger to bot
            client.send_message(entity=channel_entity, message=\"Instagram\")
            time.sleep(1)

            # fetch recent messages and check for post/story requests
            posts = client(GetHistoryRequest(peer=channel_entity, limit=10, add_offset=0, max_id=0, min_id=0, hash=0))
            for m in posts.messages:
                text = getattr(m, 'message', '') or ''
                if any(x in text for x in [\"New post is required\", \"New story is required\", \"⚠️Please do it\"]):
                    print(f\"{o}[AUTO] Message détecté: {text[:120]}...{S}\")
                    try:
                        auto_story_post_request(text)
                    except Exception as e:
                        print(f\"{J}[AUTO] Erreur lors de l'exécution automatique: {e}{S}\")
                    time.sleep(2)
            time.sleep(5)
        except KeyboardInterrupt:
            print(f\"{R}Interrompu par l'utilisateur{S}\")
            break
        except Exception as e:
            print(f\"{J}Erreur dans la boucle account(): {e}{S}\")
            time.sleep(5)
            continue

# ---------------- Other helper stubs (minimal) -----------------

def load_on_hold_accounts():
    global accounts_with_no_tasks
    if os.path.exists(ON_HOLD_FILE):
        with open(ON_HOLD_FILE, 'r') as f:
            accounts_with_no_tasks = [line.strip() for line in f if line.strip()]
    else:
        accounts_with_no_tasks = []

def save_on_hold_accounts():
    with open(ON_HOLD_FILE, 'w') as f:
        for u in accounts_with_no_tasks:
            f.write(u + \"\\n\")

def menu():
    clear_screen = lambda: os.system('clear') if os.name != 'nt' else os.system('cls')
    clear_screen()
    print(logo)
    print(f\"{o}[{V}1{o}] Démarrer les tâche automatiques\")
    print(f\"{o}[{V}0{o}] Quitter\")
    sel = input(f\"{o}[{V}?{o}] Votre choix : {B}\")
    if sel == \"1\":
        number()
    elif sel == \"0\":
        sys.exit(0)
    else:
        menu()

def number():
    clear_screen = lambda: os.system('clear') if os.name != 'nt' else os.system('cls')
    clear_screen()
    try:
        phone = open(\"number.txt\",\"r\").read().strip()
    except Exception:
        phone = input(f\"{o}[{V}?{o}] Numéro de téléphone T/G : {vi}\")
        with open(\"number.txt\",\"w\") as f:
            f.write(phone)
    telegram(phone, return_data=False)

def telegram(phone, return_data):
    global clien
    # Delayed import for telethon to avoid import errors in environments without telethon installed
    from telethon import TelegramClient
    clien = []
    app_version = \"5.1.7 x64\"
    device = \"TermuxDevice\"
    if not os.path.exists(session):
        os.makedirs(session)
    client = TelegramClient(f\"{session}/{phone}\", api_id=api_id, api_hash=api_hash, device_model=device, app_version=app_version)
    clien.append(client)
    try:
        client.connect()
    except Exception as e:
        print(f\"{R}Erreur connexion Telethon: {e}{S}\")
        return
    if not client.is_user_authorized():
        try:
            client.send_code_request(phone=phone)
            code = input(\"[?] Entrez le code reçu : \")
            client.sign_in(phone=phone, code=code)
        except PhoneNumberBannedError:
            print(f\"{r}[!] Le numéro {phone} a été banni{S}\")
            return
        except PhoneNumberInvalidError:
            print(f\"{r}[!] Numéro invalide{S}\")
            return
        except SessionPasswordNeededError:
            pw2fa = input(\"[?] Entrez le mot de passe (2FA) : \")
            client.sign_in(phone=phone, password=pw2fa)
    me = client.get_me()
    print(f\"[√] Compte : {getattr(me, 'first_name','')} {getattr(me,'last_name','')}\")
    account()

# ---------------- Main -----------------

if __name__ == \"__main__\":
    try:
        clear_screen = lambda: os.system('clear') if os.name != 'nt' else os.system('cls')
        clear_screen()
        print(logo)
        menu()
    except KeyboardInterrupt:
        print(\"Interrompu\")
        try:
            if clien and clien[0].is_connected():
                clien[0].disconnect()
        except Exception:
            pass
        sys.exit(0)
