# tahBeKetrika.py
# Merged version: original user script + auto post/story feature
# IMPORTANT: run this on your machine with Telethon and instagrapi installed and configured.
# Save as tahBeKetrika.py and run: python tahBeKetrika.py

import requests
import os
import random
import threading
import json
import platform
import sys
import time
from uuid import uuid4
from telethon.errors import FloodWaitError
from telethon.errors import SessionPasswordNeededError, PhoneNumberInvalidError, PhoneNumberBannedError
from telethon import TelegramClient, sync, events
from telethon.tl.functions.messages import GetHistoryRequest, GetBotCallbackAnswerRequest
from bs4 import BeautifulSoup as bs
import re
from random import choice
from concurrent.futures import ThreadPoolExecutor as tpe
import webbrowser
import datetime
import sqlite3
import shutil
import hashlib
from datetime import datetime, timedelta
from instagrapi import Client
import uuid

# Colors
vi='\\033[1;35m'
R='\\033[1;91m'
V='\\033[1;92m'
black="\\033[1;30m"
J='\\033[1;33m'
C='\\033[1;96m'
B='\\033[1;97m'
Bl='\\033[1;34m'
o="\\x1b[38;5;214m"    # Orange
O='\\033[38;5;208m'
S='\\033[0m'
c='\\033[7;96m'
r='\\033[7;91m'
v='\\033[7;92m'
ro='\\033[1;41m'
co='\\033[1;46m'

# --- Configuration ---
SERVER_URL = "https://tahbeketrika.pythonanywhere.com/"
API_KEY_FILE = "api_key.json"
SESSION_FILE = "session_id.txt"

def get_device_id():
    try:
        raw_id = f"{platform.node()}-{uuid.getnode()}"
        device_id = hashlib.sha256(raw_id.encode()).hexdigest()[:20]
        return device_id
    except Exception:
        return "unknown_device"

logo=f"""
{o}═════════════════════════════════════════
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
{o}═════════════════════════════════════════"""

DAYS_LEFT = None

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
    except Exception as e:
        print(f"⚠️ Erreur lors du calcul de la date d'expiration : {e}")
        DAYS_LEFT = None

def get_days_left_str():
    global DAYS_LEFT
    if DAYS_LEFT is None:
        return "\\033[1;92mAbonnement actif\\033[0m"
    elif DAYS_LEFT < 0:
        return "\\033[1;91m[EXPIRE]\\033[0m"
    elif DAYS_LEFT == 0:
        return "\\033[1;93mExpire aujourd'hui\\033[0m"
    else:
        return f"\\033[1;93m{DAYS_LEFT} jour(s) restant(s)\\033[0m"

def get_or_create_session_id():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f:
                return f.read().strip()
        except:
            pass
    session_id = str(uuid.uuid4())
    with open(SESSION_FILE, "w") as f:
        f.write(session_id)
    return session_id

def clear_credentials():
    if os.path.exists(API_KEY_FILE):
        os.remove(API_KEY_FILE)
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

def verify_with_server(api_key, session_id, device_id):
    try:
        payload = {"api_key": api_key, "session_id": session_id, "device_id": device_id}
        response = requests.post(f"{SERVER_URL}/api/verify", json=payload, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"{R}❌ Erreur serveur: {response.status_code}{S}")
            return None
    except requests.exceptions.Timeout:
        print(f"{R}❌ Timeout - Serveur non accessible{S}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"{R}❌ Impossible de se connecter au serveur{S}")
        return None
    except Exception as e:
        print(f"{R}❌ Erreur de connexion: {e}{S}")
        return None

def get_user_credentials():
    print(f"\n{o}═════════════════════════════════════════")
    print(f"{V}🔐 AUTHENTIFICATION REQUISE")
    print(f"{o}═════════════════════════════════════════{S}")
    username = input(f"{o}👤 Nom d'utilisateur : {vi}").strip()
    api_key = input(f"{o}🔑 Clé API : {vi}").strip()
    if not username or not api_key:
        print(f"{R}❌ Les deux champs sont obligatoires{S}")
        return None, None
    return username, api_key

def save_credentials(username, api_key, session_id, device_id):
    credentials = {"username": username, "api_key": api_key, "session_id": session_id, "device_id": device_id, "verified_at": datetime.now().isoformat()}
    with open(API_KEY_FILE, "w") as f:
        json.dump(credentials, f)

def load_credentials():
    if os.path.exists(API_KEY_FILE):
        try:
            with open(API_KEY_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, KeyError):
            print(f"{R}❌ Fichier de licence corrompu{S}")
            clear_credentials()
    return None

def authenticate_user():
    global DAYS_LEFT
    credentials = load_credentials()
    if credentials:
        api_key = credentials.get("api_key")
        session_id = credentials.get("session_id", get_or_create_session_id())
        device_id = credentials.get("device_id", get_device_id())
        result = verify_with_server(api_key, session_id, device_id)
        if result and result.get("access"):
            username = result.get("username", credentials.get("username"))
            save_credentials(username, api_key, session_id, device_id)
            if "jours_restants" in result:
                DAYS_LEFT = result["jours_restants"]
            elif "expires_at" in result:
                update_days_left(result["expires_at"])
            print(f"\n{V}✅ Authentification réussie !{S}")
            print(f"{B}👤 Utilisateur : {vi}{username}{S}")
            print(f"{B}📅 Statut : {get_days_left_str()}{S}")
            return True
    clear_credentials()
    for attempt in range(3):
        print(f"\n{o}🎯 Tentative {attempt + 1}/3")
        print(f"{o}═════════════════════════════════════════{S}")
        username, api_key = get_user_credentials()
        if not username or not api_key:
            continue
        session_id = get_or_create_session_id()
        device_id = get_device_id()
        result = verify_with_server(api_key, session_id, device_id)
        if result and result.get("access"):
            save_credentials(username, api_key, session_id, device_id)
            if "jours_restants" in result:
                DAYS_LEFT = result["jours_restants"]
            elif "expires_at" in result:
                update_days_left(result["expires_at"])
            print(f"\n{V}✅ Authentification réussie !{S}")
            print(f"{B}👤 Utilisateur : {vi}{username}{S}")
            print(f"{B}📅 Statut : {get_days_left_str()}{S}")
            return True
        else:
            reason = result.get("reason", "accès refusé") if result else "erreur connexion"
            error_messages = {
                "licence_invalide": f"{R}❌ Clé API invalide{S}",
                "licence_expiree": f"{R}❌ Licence expirée{S}",
                "licence_desactivee": f"{R}❌ Licence désactivée{S}",
                "licence_utilisee_ailleurs": f"{R}❌ Licence utilisée sur un autre appareil{S}",
                "device_id_manquant": f"{R}❌ Identifiant appareil manquant{S}"
            }
            print(error_messages.get(reason, f"{R}❌ Erreur: {reason}{S}"))
            if attempt < 2:
                retry = input(f"\n{J}🔄 Réessayer ? (o/N) : {S}").strip().lower()
                if retry not in ['o', 'oui', 'y', 'yes']:
                    break
    print(f"\n{R}🚫 Échec de l'authentification. Fermeture.{S}")
    return False

def auto_check_license(interval_minutes=5):
    def monitor():
        global DAYS_LEFT
        while True:
            try:
                credentials = load_credentials()
                if not credentials:
                    print(f"\n{R}❌ Licence introuvable - Arrêt{S}")
                    os._exit(1)
                result = verify_with_server(credentials["api_key"], credentials["session_id"], credentials["device_id"])
                if not result or not result.get("access"):
                    print(f"\n{R}❌ Licence révoquée - Arrêt{S}")
                    clear_credentials()
                    os._exit(1)
                if "jours_restants" in result:
                    DAYS_LEFT = result["jours_restants"]
                elif "expires_at" in result:
                    update_days_left(result["expires_at"])
                if DAYS_LEFT is not None and DAYS_LEFT <= 0:
                    print(f"\n{R}❌ Licence expirée - Arrêt{S}")
                    clear_credentials()
                    os._exit(1)
            except Exception as e:
                print(f"{J}⚠️ Erreur vérification licence: {e}{S}")
            time.sleep(interval_minutes * 60)
    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()

# === GLOBALS ===
clien=[]
var1=[]
var2=[]
var=[]
compte=[]
comptes=[]
accounts_with_no_tasks = []
rq=requests.session()
session = "sessions"
BASE_DIR = os.path.join(os.path.dirname(__file__), "SmmKingdomTask")
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)
ON_HOLD_FILE = os.path.join(BASE_DIR, "on_hold_accounts.txt")

ACTION_LIMITS = {'follow': 1000, 'like': 4000, 'comment': 1000, 'story': 2000}
DAILY_LIMITS = {'follow': 20000, 'like': 50000, 'comment': 20000, 'story': 30000}
ACTION_TYPES = ['follow', 'like', 'comment', 'story']
ACTION_STATE_FILE = os.path.join(BASE_DIR, 'action_state.json')
DAILY_STATE_FILE = os.path.join(BASE_DIR, 'daily_state.json')
ON_HOLD_ACTION_FILE = os.path.join(BASE_DIR, 'on_hold_action.json')
EXPIRES_AT = None

def human_delay(min_sec=1, max_sec=3):
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)

def load_action_state():
    if os.path.exists(ACTION_STATE_FILE):
        with open(ACTION_STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_action_state(state):
    with open(ACTION_STATE_FILE, 'w') as f:
        json.dump(state, f)

def load_daily_state():
    if os.path.exists(DAILY_STATE_FILE):
        with open(DAILY_STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_daily_state(state):
    with open(DAILY_STATE_FILE, 'w') as f:
        json.dump(state, f)

def load_on_hold_action():
    if os.path.exists(ON_HOLD_ACTION_FILE):
        with open(ON_HOLD_ACTION_FILE, 'r') as f:
            return json.load(f)
    return {a: [] for a in ACTION_TYPES}

def save_on_hold_action(state):
    with open(ON_HOLD_ACTION_FILE, 'w') as f:
        json.dump(state, f)

def load_on_hold_accounts():
    global accounts_with_no_tasks
    if os.path.exists(ON_HOLD_FILE):
        with open(ON_HOLD_FILE, 'r') as f:
            accounts_with_no_tasks = [line.strip() for line in f.readlines() if line.strip()]
    else:
        accounts_with_no_tasks = []

def save_on_hold_accounts():
    with open(ON_HOLD_FILE, 'w') as f: 
        for user in accounts_with_no_tasks:
            f.write(user + '\\n')

peer = "SmmKingdomTasksBot"
api_id = 2040
api_hash = "b18441a1ff607e10a989891a5462e627"

def user():
  a=random.randint(30,999)
  b=random.randint(0,9)
  c=random.randint(0,9)
  d=random.randint(0,30)
  e=random.randint(10,99)
  f=random.randint(20,29)
  g=random.randint(300,500)
  i=random.randint(6,12)
  k=random.randint(1000000,10000000)
  j="".join(random.SystemRandom().choice("AZERTYUIOPQSDFGHJKLMWXCVBN") for i in range(5))
  proc=random.choice(['qcom',f'mt{random.randint(6750,6790)}'])
  marque=random.choice(['TCL','TECNO','SAMSUNG','ITEL','VIVO','REDMI','MEIZU','HUAWEI','HONOR','ONE PLUS','REALME','SONY','POCO','DOCOMO','OPPO','NOKIA'])
  h=random.choice(['720x,1280','1080x1920','1920x2500'])
  en = random.choice(['en_US','en_GB','en_FR'])
  version=random.choice(['5.0','5.0.1','6.0.1','7.1','8.1.0','9','10','11','12','13','14'])
  ua=f"Instagram {a}.{b}.{c}.{d}.{e} Android ({f}/{version}; {g}dpi; {h}; {marque}; Note {i}; {j}; {proc}; {en}; {k})"
  return ua

def clear():
  os.system('cls' if os.name == 'nt' else 'clear')
  print(logo)

def menu():
    global var
    clear()
    print(f"\\033[1;96m[Licence]\\033[0m {get_days_left_str()}")
    print(f"{o}[{V}1{o}] Démarrer les tâche automatiques")
    print(f"{o}[{V}2{o}] Gérer les comptes")
    print(f"{o}[{V}3{o}] Voir les statistiques")
    print(f"{o}[{V}4{o}] Déconnexion Telegram")
    print(f"{o}[{V}5{o}] Ajouter un compte Instagram par sessionid")
    print(f"{o}[{V}6{o}] Ajouter un compte Instagram par identifiants")
    print(f"{o}[{V}7{o}] Supprimer un compte Instagram")
    print(f"{o}[{V}8{o}] Mettre à jour le bot")
    print(f"{o}[{V}9{o}] Restaurer un compte en attente (on hold)")
    print(f"{o}[{V}0{o}] Quitter")
    print(f"{o}═════════════════════════════════════════")
    sel = input(f"{o}[{V}?{o}] Votre choix : {B}")
    if sel == "1":
        var.clear()
        var.append("1")
        number()
    elif sel == "2":
        var.clear()
        var.append("2")
        menu()
    elif sel == "3":
        show_statistics()
    elif sel == "4":
        try:
            if os.name == 'nt':
                os.system("rmdir /S /Q sessions")
            else:
                os.system("rm -r sessions")
        except Exception:
            pass
        try:
            os.remove("number.txt")
        except Exception:
            pass
        clear()
        print(f"{r}Déconnexion réussie{S}")
        time.sleep(4)
        menu()
    elif sel == "5":
        add_account_by_cookie()
    elif sel == "6":
        add_account_by_login()
    elif sel == "7":
        delete_instagram_account()
    elif sel == "8":
        update_bot()
    elif sel == "9":
        restore_on_hold_account()
    elif sel == "0":
        exit()
    else:
        menu()

def number():
  clear()
  try:
    phone=open("number.txt","r").read()
  except:
    phone=input(f"{o}[{V}?{o}] Numéro de téléphone T/G : {vi}")
    open("number.txt","w").write(phone)
  telegram(phone, return_data=False)

def telegram(phone, return_data):
    global clien
    clien = []
    app_version = "5.1.7 x64"
    device = "Redmi Note 8 Pro"

    if not os.path.exists(session):
        os.makedirs(session)
    client = TelegramClient(f"{session}/{phone}", api_id=api_id, api_hash=api_hash, device_model=device, app_version=app_version, system_version="Android 11", lang_code="us", system_lang_code="en-US",)
    clien.append(client)
    try:
        client.connect()
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            print(f"{R}La base de données de session est verrouillée.{S}")
            print(f"{J}Cela peut se produire si le script a été mal arrêté. Essayez de supprimer le dossier 'sessions' et réessayez.{S}")
            time.sleep(5)
            exit()
        else:
            print(f"{R}Erreur de connexion Telethon: {e}{S}")
            exit()
    except Exception as e:
        print(f"{R}Une erreur inattendue est survenue: {e}{S}")
        exit()
    if not client.is_user_authorized():
        try:
            client.send_code_request(phone=phone)
            clear()
            if os.path.exists("number.txt"):
                with open("number.txt", "r") as f:
                    number = f.read().strip()
            else:
                number = "Inconnu"
            print(f"[*] Votre numéro : {number}")
            code = input("[?] Entrez le code reçu : ")
            client.sign_in(phone=phone, code=code)
            clear()
        except PhoneNumberBannedError:
            clear()
            print(f"{r}[!] Le numéro de téléphone {phone} a été banni par Telegram.{S}")
            print(f"{J}[-] Veuillez utiliser un autre numéro.{S}")
            try:
                os.remove("number.txt")
            except OSError:
                pass
            time.sleep(4)
            menu()
            return
        except PhoneNumberInvalidError:
            clear()
            print(f"{r}[!] Le numéro de téléphone {phone} est invalide.{S}")
            print(f"{J}[-] Veuillez vérifier le numéro et réessayer.{S}")
            try:
                os.remove("number.txt")
            except OSError:
                pass
            time.sleep(4)
            menu()
            return
        except SessionPasswordNeededError:
            pw2fa = input("[?] Entrez le mot de passe (2FA) : ")
            client.sign_in(phone=phone, password=pw2fa)
    me = client.get_me()
    telegram_username = me.username
    email = None
    phone = me.phone if hasattr(me, 'phone') else None
    if not return_data:
        print(f"[√] Compte : {me.first_name} {me.last_name}")
        print("═════════════════════════════════════════")
        if var[0] == "1":
            account()
        elif var[0] == "2":
            manage()

# ---------- Helper functions to read Telegram channel history ----------
_processed_auto_msgs_file = os.path.join(BASE_DIR, "processed_auto_messages.txt")
_processed_auto_msgs = set()
def _load_processed_msgs():
    global _processed_auto_msgs
    if os.path.exists(_processed_auto_msgs_file):
        try:
            with open(_processed_auto_msgs_file, 'r') as f:
                _processed_auto_msgs = set(line.strip() for line in f if line.strip())
        except:
            _processed_auto_msgs = set()
def _save_processed_msg(msg_id):
    try:
        with open(_processed_auto_msgs_file, 'a') as f:
            f.write(str(msg_id) + '\\n')
    except:
        pass

def managers():
  global clien
  client=clien[0]
  channel_entity = client.get_entity("@SmmKingdomTasksBot")
  posts = client(GetHistoryRequest(peer=channel_entity, limit=10, offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0))
  count=[0,1,2,3,4,5,6,7,8,9]
  for p in count:
    message=posts.messages[p].message
    if "Thank you" in message:
      continue
    elif "Instagram :" in message:
      return message
    elif "WAS NOT rewarded" in message:
      continue
    elif "is not approved" in message:
      continue
    elif "Account was passed" in message:
      continue
    elif "on review now" in message:
      continue
    else:
      continue

def manage():
  count=managers()
  path=os.path.join(BASE_DIR, "acc.txt")
  open(path,'w').write(str(count))
  for x in open(path,'r').readlines():
    acc=x.strip()
    if "💎" in acc:
      user=re.search("💎 (.*?) /",str(acc)).group(1)
      print(f"{vi}{o}Nom d'utilisateur : {vi}{user}")
      pwd=input(f"{o}Mot de passe : {vi}")
      s_acc=open(os.path.join(BASE_DIR, "Compte.txt"),'a')
      s_acc.write(f"{user}|{pwd}\\n")
      s_acc.close()
      continue
    elif "✅" in acc:
      cuser=acc.split("✅ ")[1].split(" (")[0]
      print(f"{vi}{o}Nom d'utilisateur : {vi}{cuser}")
      pwd=input(f"{o}Mot de passe : {vi}")
      s_acc=open(os.path.join(BASE_DIR, "Compte.txt"),'a')
      s_acc.write(f"{cuser}|{pwd}\\n")
      s_acc.close()
      continue
    else:
      continue
  try:
      os.remove(path)
  except:
      pass

def message():
  global clien
  client=clien[0]
  channel_entity = client.get_entity("@SmmKingdomTasksBot")
  posts = client(GetHistoryRequest(peer=channel_entity, limit=10, offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0))
  count=[0,1,2,3,4,5,6,7,8,9]
  for p in count:
    try:
        message=posts.messages[p].message
    except:
        continue
    if "Thank you" in message:
      continue
    elif "Here is a" in message:
      continue
    elif "WAS NOT rewarded" in message:
      continue
    elif "is not approved" in message:
      continue
    elif "Account was passed" in message:
      continue
    else:
      return message

def coms1():
  global clien
  client=clien[0]
  channel_entity = client.get_entity("@SmmKingdomTasksBot")
  posts = client(GetHistoryRequest(peer=channel_entity, limit=10, offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0))
  count=[0,1,2,3,4,5,6,7,8,9]
  for p in count:
    try:
        message=posts.messages[p].message
    except:
        continue
    if "Thank you" in message:
      continue
    elif "the comment" in message:
      return message
    else:
      continue

def coms(user):
  global clien
  client=clien[0]
  channel_entity = client.get_entity("@SmmKingdomTasksBot")
  posts = client(GetHistoryRequest(peer=channel_entity, limit=10, offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0))
  count=[0,1,2,3,4,5,6,7,8,9]
  for p in count:
    try:
        message=posts.messages[p].message
    except:
        continue
    if "Thank you" in message:
      continue
    elif "▪️ Action :" in message:
      continue
    elif "Here is a" in message:
      continue
    elif user in message:
      continue
    elif "Completed" in message:
      continue
    elif "======" in message:
      continue
    else:
      return message

def insta():
  global clien
  client=clien[0]
  channel_entity = client.get_entity("@SmmKingdomTasksBot")
  posts = client(GetHistoryRequest(peer=channel_entity, limit=10, offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0))
  count=[0,1,2,3,4,5,6,7,8,9]
  for p in count:
    try:
        message=posts.messages[p].message
    except:
        continue
    if "Thank you" in message:
      continue
    elif "Here is a" in message:
      continue
    elif "Please give us" in message:
      return message
    elif "Please choose" in message:
      return message
    elif "⚠️Please do it" in message:
      return message
    elif "======" in message:
      return message
    elif "Instagram" in message:
      return message
    elif "New story is required!" in message:
      return message
    elif "New post is required!" in message:
      return message
    else:
      continue
  return "Instagram"

# === New: auto_story_post_request implementation ===
def auto_story_post_request(message_text, posts_to_check=10):
    """
    Process a Telegram message that requests copying posts and story from a source account
    to a target account. The function:
      - parses target and source usernames
      - fetches last `posts_to_check` medias from source
      - fetches recent medias from target
      - compares by caption AND media fingerprint (thumbnail_url or pk)
      - publishes the first media that doesn't exist on target (avoids duplicates)
      - publishes a story from that media
      - sends /fix_target back to Telegram
    """
    global clien
    try:
        # parse the message to extract target and source usernames
        m = re.search(r'Account\\s+([\\w._-]+)\\s*\\(source account\\s*:\\s*(https?://[^)]+)\\)', message_text)
        if not m:
            print(f"{J}[AUTO] Message non parsable pour auto post/story: {message_text}{S}")
            return
        target_user = m.group(1).strip()
        source_url = m.group(2).strip().rstrip('/')
        source_user = source_url.split('/')[-1]
        print(f"{o}[AUTO] Traitement auto post/story: target={target_user}, source={source_user}{S}")

        # get passwords if available
        target_pwd = get_password_for_username(target_user)
        source_pwd = get_password_for_username(source_user)

        # connect to Instagram accounts (use session if available)
        try:
            cl_source = ig_connect(source_user, password=source_pwd) if source_pwd else ig_connect(source_user)
        except Exception as e:
            print(f"{R}[AUTO] Impossible de se connecter à la source {source_user}: {e}{S}")
            return
        try:
            cl_target = ig_connect(target_user, password=target_pwd) if target_pwd else ig_connect(target_user)
        except Exception as e:
            print(f"{R}[AUTO] Impossible de se connecter à la cible {target_user}: {e}{S}")
            return

        # fetch source medias and target medias
        try:
            src_id = cl_source.user_id_from_username(source_user)
            src_medias = cl_source.user_medias(src_id, posts_to_check)
        except Exception as e:
            print(f"{R}[AUTO] Erreur récupération medias source: {e}{S}")
            src_medias = []
        try:
            tgt_id = cl_target.user_id_from_username(target_user)
            tgt_medias = cl_target.user_medias(tgt_id, 200)
        except Exception as e:
            print(f"{R}[AUTO] Erreur récupération medias cible: {e}{S}")
            tgt_medias = []

        # Build fingerprint set for target to detect duplicates
        tgt_fingerprints = set()
        for m in tgt_medias:
            try:
                cap = (getattr(m, 'caption_text', '') or '').strip()
                thumb = getattr(m, 'thumbnail_url', '') or getattr(m, 'image_versions2', None) or ''
                pk = getattr(m, 'pk', '') or getattr(m, 'id', '')
                key = (cap, str(thumb), str(pk))
                tgt_fingerprints.add(key)
            except:
                continue

        posted_any = False
        for media in src_medias:
            try:
                caption = (getattr(media, 'caption_text', '') or '').strip()
                thumb = getattr(media, 'thumbnail_url', None) or ''
                pk = getattr(media, 'pk', None) or getattr(media, 'id', None) or ''
                key = (caption, str(thumb), str(pk))
                # compare against target fingerprints by caption or media id/url
                duplicate = False
                for tkey in tgt_fingerprints:
                    # consider duplicate if captions equal OR media id/thumbnail equal
                    if (caption and caption == tkey[0]) or (str(pk) and str(pk) == tkey[2]) or (thumb and thumb == tkey[1]):
                        duplicate = True
                        break
                if duplicate:
                    print(f"{J}[AUTO] Media déjà présent sur target (pass). Caption[:30]: {caption[:30]}{S}")
                    continue

                # download media to temp file
                if thumb:
                    try:
                        img_data = requests.get(thumb, timeout=20).content
                        tmp_path = os.path.join('/tmp' if os.name!='nt' else os.environ.get('TEMP','.'), f"tah_auto_{uuid.uuid4()}.jpg")
                        with open(tmp_path, 'wb') as f:
                            f.write(img_data)
                    except Exception as e:
                        print(f"{J}[AUTO] Erreur téléchargement image: {e}{S}")
                        continue
                else:
                    # try to get url via media info
                    try:
                        info = cl_source.media_info(media.pk)
                        img_url = getattr(info, 'thumbnail_url', None)
                        if img_url:
                            img_data = requests.get(img_url, timeout=20).content
                            tmp_path = os.path.join('/tmp' if os.name!='nt' else os.environ.get('TEMP','.'), f"tah_auto_{uuid.uuid4()}.jpg")
                            with open(tmp_path, 'wb') as f:
                                f.write(img_data)
                        else:
                            print(f"{J}[AUTO] Aucun URL pour media, pass.{S}")
                            continue
                    except Exception as e:
                        print(f"{J}[AUTO] Impossible d'obtenir media_info: {e}{S}")
                        continue

                # Post to target (photo upload + same caption)
                try:
                    print(f"{V}[AUTO] Publication sur {target_user}...{S}")
                    cl_target.photo_upload(tmp_path, caption)
                    print(f"{V}[AUTO] ✅ Publication réussie pour {target_user}{S}")
                    posted_any = True
                    # update target fingerprint set to avoid reposting same media during loop
                    tgt_fingerprints.add(key)
                except Exception as e:
                    print(f"{R}[AUTO] Erreur lors de la publication: {e}{S}")
                finally:
                    try:
                        os.remove(tmp_path)
                    except:
                        pass

                # small pause
                time.sleep(random.randint(10, 30))

                # Post story from the same image (if allowed)
                try:
                    # Re-download or reuse tmp_path logic - quickly re-fetch thumbnail
                    if thumb:
                        story_tmp = os.path.join('/tmp' if os.name!='nt' else os.environ.get('TEMP','.'), f"tah_story_{uuid.uuid4()}.jpg")
                        with open(story_tmp, 'wb') as f:
                            f.write(requests.get(thumb, timeout=20).content)
                        cl_target.photo_upload_to_story(story_tmp)
                        try: os.remove(story_tmp)
                        except: pass
                        print(f"{V}[AUTO] ✅ Story publiée pour {target_user}{S}")
                    else:
                        print(f"{J}[AUTO] Pas d'URL story disponible, ignoré.{S}")
                except Exception as e:
                    print(f"{J}[AUTO] Erreur publication story: {e}{S}")

                # Send /fix_target message to Telegram bot
                try:
                    client = clien[0]
                    channel_entity = client.get_entity("@SmmKingdomTasksBot")
                    fix_cmd = f"/fix_{target_user}"
                    client.send_message(entity=channel_entity, message=fix_cmd)
                    print(f"{V}[AUTO] {fix_cmd} envoyé.{S}")
                except Exception as e:
                    print(f"{J}[AUTO] Impossible d'envoyer {fix_cmd} : {e}{S}")

                # done for this target (if you want to post multiple different posts, remove break)
                # continue to next source media to try to publish more until limit
                # we will not break; we allow multiple posts if multiple unique ones exist
                time.sleep(random.randint(5, 15))
            except Exception as e:
                print(f"{R}[AUTO] Exception lors du traitement d'un media: {e}{S}")
                continue

        if not posted_any:
            print(f"{J}[AUTO] Aucun nouveau post trouvé à publier pour {target_user}.{S}")
    except Exception as e:
        print(f"{R}[AUTO] Erreur critique dans auto_story_post_request: {e}{S}")
        import traceback
        traceback.print_exc()

# Background listener that polls Telegram history for auto-post messages
def auto_post_listener(poll_interval=8, posts_to_check=10):
    """
    Poll the Telegram channel every poll_interval seconds and process messages
    that contain 'Account ... (source account : ...)' by calling auto_story_post_request.
    """
    global clien
    _load_processed_msgs()
    while True:
        try:
            if not clien:
                time.sleep(1)
                continue
            client = clien[0]
            try:
                channel_entity = client.get_entity("@SmmKingdomTasksBot")
            except Exception as e:
                time.sleep(poll_interval)
                continue
            history = client(GetHistoryRequest(peer=channel_entity, limit=20, offset_date=None, offset_id=0, max_id=0, min_id=0, add_offset=0, hash=0))
            for msg in reversed(history.messages):
                try:
                    mid = getattr(msg, 'id', None)
                    if not mid or str(mid) in _processed_auto_msgs:
                        continue
                    text = getattr(msg, 'message', '') or ''
                    if 'Account' in text and 'source account' in text and ('New post is required' in text or 'New story is required' in text):
                        print(f"{o}[AUTO] Message auto trouvé id={mid}{S}")
                        _processed_auto_msgs.add(str(mid))
                        _save_processed_msg(mid)
                        # process in separate thread so listener keeps polling
                        threading.Thread(target=auto_story_post_request, args=(text, posts_to_check), daemon=True).start()
                except Exception as e:
                    print(f"{J}[AUTO] Erreur lecture message: {e}{S}")
                    continue
        except Exception as e:
            print(f"{J}[AUTO] Listener exception: {e}{S}")
        time.sleep(poll_interval)

# --- The existing account() function with listener thread started alongside main loop ---
def account():
    global clien
    client = clien[0]
    load_on_hold_accounts()
    # start background listener thread for auto post/story
    listener_thread = threading.Thread(target=auto_post_listener, args=(8, 10), daemon=True)
    listener_thread.start()

    while True:
        try:
            path = os.path.join(BASE_DIR, "insta-acct.txt")
            if os.path.exists(path):
                all_accounts = [line.strip() for line in open(path, 'r').readlines() if line.strip()]
                active_accounts_exist = any(user not in accounts_with_no_tasks for user in all_accounts)

                if not active_accounts_exist:
                    print(f"{J}Tous les comptes sont en attente ou le fichier est vide.{S}")
                    print(f"{J}Utilisez l'option 6 du menu pour réactiver des comptes.{S}")
                    time.sleep(4)
                    menu()
                    return

                for user in all_accounts:
                    if user in accounts_with_no_tasks:
                        continue

                    try:
                        action_state = load_action_state()
                        daily_state = load_daily_state()
                        today = datetime.now().strftime('%Y-%m-%d')

                        if user in daily_state and daily_state[user].get('date') == today:
                            blocked = all(daily_state[user][a] >= DAILY_LIMITS[a] for a in ACTION_TYPES)
                            if blocked:
                                print(f"{J}[!] {user} a atteint ses limites journalières, passage au suivant.{S}")
                                if user not in accounts_with_no_tasks:
                                    accounts_with_no_tasks.append(user)
                                continue

                        channel_entity = client.get_entity("@SmmKingdomTasksBot")
                        client.send_message(entity=channel_entity, message=f"Instagram")

                        loop = 0
                        while True:
                            loop += 1
                            try:
                                if insta() in "Instagram":
                                    if loop <= 10:
                                        sys.stdout.write(f"\\rInstagram {loop}s\\r")
                                        sys.stdout.flush()
                                        time.sleep(0.1)
                                    else:
                                        client.send_message(entity=channel_entity, message="Instagram")
                                        break
                                else:
                                    break
                            except Exception as e:
                                print(f"{R}Erreur lors de l'attente de réponse du bot: {e}{S}")
                                break

                        client.send_message(entity=channel_entity, message=f"{user}")
                        styled_user = f"\\033[1;96m\\033[4m{user}\\033[0m"
                        print(f"{o}[{B}•{o}] Nom d'utilisateur : {styled_user}{S}")

                        try:
                            mss = message()
                            if not mss:
                                time.sleep(2)
                                continue
                            if "Sorry" in mss:
                                continue
                            elif "▪️ Action :" in mss:
                                task(user)
                                print(f"\\033[1;96m[SUCCÈS] Tâche effectuée pour {styled_user}\\033[0m")
                                continue
                            elif "🟡 Account" in mss:
                                print(f"{co}{mss}{S}")
                                if user not in accounts_with_no_tasks:
                                    accounts_with_no_tasks.append(user)
                                    save_on_hold_accounts()
                                time.sleep(2)
                                continue
                            else:
                                time.sleep(4)
                                task(user)
                                print(f"\\033[1;96m[SUCCÈS] Tâche effectuée pour {styled_user}\\033[0m")
                                continue
                        except Exception as e:
                            print(f"{R}Erreur lors du traitement du message pour {user}: {e}{S}")
                            continue

                    except Exception as e:
                        print(f"{R}Erreur générale pour {user}: {e}{S}")
                        print(f"{J}Continuation avec le prochain utilisateur...{S}")
                        continue

            else:
                os.system("clear")
                u = (f"{r}Aucun fichier trouvé : SmmKingdomTask/insta-acct.txt\n{S}")
                for ix in u:
                    print(ix, end='', flush=True)
                    time.sleep(0.1)
                menu()
                return

        except Exception as e:
            print(f"{R}Erreur critique dans la boucle principale: {e}{S}")
            print(f"{J}Redémarrage de la boucle dans 10 secondes...{S}")
            time.sleep(10)
            continue

# The rest of the functions (task, action executors, ig_connect, etc.) are retained from original script.
# For brevity and to ensure integrity, we'll include them largely unchanged below.

def task(user):
    global clien, var1, accounts_with_no_tasks
    client = clien[0]

    try:
        if not _initialize_task_state(user):
            return None

        time.sleep(2)
        channel_entity = client.get_entity("@SmmKingdomTasksBot")
        mss = message()

        if "▪️ Action :" in mss:
            return _handle_action_task(user, mss, client, channel_entity)
        elif "Sorry" in mss:
            return _handle_sorry_message(user)
        elif "🟡 Account" in mss:
            return _handle_yellow_account_message(user, mss)
        else:
            return _handle_other_messages(user, mss, client, channel_entity)

    except Exception as e:
        print(f"{R}Erreur dans la tâche pour {user}: {e}{S}")
        print(f"{J}Continuation avec le prochain utilisateur...{S}")
        return None

def _initialize_task_state(user):
    reactivate_accounts()
    action_state = load_action_state()
    daily_state = load_daily_state()
    on_hold_action = load_on_hold_action()
    today = datetime.now().strftime('%Y-%m-%d')

    if user not in action_state:
        action_state[user] = {a: {'count': 0, 'last_reset': time.time()} for a in ACTION_TYPES}

    if user not in daily_state or daily_state[user].get('date') != today:
        daily_state[user] = {'date': today, 'follow': 0, 'like': 0, 'comment': 0, 'story': 0}

    save_action_state(action_state)
    save_daily_state(daily_state)
    save_on_hold_action(on_hold_action)

    accounts_path = os.path.join(BASE_DIR, "insta-acct.txt")
    if os.path.exists(accounts_path):
        with open(accounts_path, 'r') as f:
            all_accounts = [line.strip() for line in f if line.strip()]
        if all_accounts_blocked(daily_state, all_accounts):
            print(f"{R}Tous les comptes ont atteint leur limite journalière. Arrêt du programme jusqu'à demain.{S}")
            exit()

    return True

def _handle_action_task(user, mss, client, channel_entity):
    action_type = _determine_action_type(mss)
    if not action_type:
        return None

    if not _check_action_limits(user, action_type):
        return None

    return _execute_action(user, action_type, mss, client, channel_entity)

def _determine_action_type(mss):
    if "the post" in mss:
        return 'like'
    elif "Follow" in mss:
        return 'follow'
    elif "the comment" in mss:
        return 'comment'
    elif "the story" in mss:
        return 'story'
    return None

def _check_action_limits(user, action_type):
    action_state = load_action_state()
    daily_state = load_daily_state()
    on_hold_action = load_on_hold_action()

    for entry in on_hold_action.get(action_type, []):
        if entry['user'] == user:
            if time.time() - entry['hold_time'] < 3600:
                if user not in accounts_with_no_tasks:
                    accounts_with_no_tasks.append(user)
                return False
            else:
                on_hold_action[action_type] = [e for e in on_hold_action[action_type] if e['user'] != user]
                save_on_hold_action(on_hold_action)
                if user in accounts_with_no_tasks:
                    accounts_with_no_tasks.remove(user)
                    save_on_hold_accounts()

    if daily_state[user][action_type] >= DAILY_LIMITS[action_type]:
        print(f"{R}Limite journalière atteinte pour {user} ({action_type}). Mise en attente jusqu'à demain.{S}")
        if user not in accounts_with_no_tasks:
            accounts_with_no_tasks.append(user)
            save_on_hold_accounts()
        return False

    if action_state[user][action_type]['count'] >= ACTION_LIMITS[action_type]:
        print(f"{J}Limite horaire atteinte pour {user} ({action_type}). Mise en attente 1h.{S}")
        on_hold_action[action_type].append({'user': user, 'hold_time': time.time()})
        save_on_hold_action(on_hold_action)
        if user not in accounts_with_no_tasks:
            accounts_with_no_tasks.append(user)
            save_on_hold_accounts()
        return False

    return True

def _execute_action(user, action_type, mss, client, channel_entity):
    link = re.search('▪️ Link :\\n(.*?)\\n▪️ Action :', str(mss)).group(1)

    if action_type == 'like':
        return _execute_like_action(user, link, client, channel_entity)
    elif action_type == 'follow':
        return _execute_follow_action(user, link, client, channel_entity)
    elif action_type == 'comment':
        return _execute_comment_action(user, link, client, channel_entity)
    elif action_type == 'story':
        return _execute_story_action(user, link, client, channel_entity)

    return None

def _execute_like_action(user, link, client, channel_entity):
    print(f"{vi}Lien du post : {B}{link}")
    human_delay()
    try:
        cl = ig_connect(user)
        media_id = cl.media_pk_from_url(link)
        cl.media_like(media_id)
        print(f"{vi}[{V}√{vi}] {V}Like réussi{S}")
        try:
            cl.feed_timeline()
            time.sleep(2)
        except Exception as e:
            print(f"{J}Scroll down simulé échoué : {e}{S}")
        _update_action_counters(user, 'like')
        client.send_message(entity=channel_entity, message="✅Completed")
        human_delay()
        task(user)
        return None
    except Exception as e:
        print(f"{vi}[{R}x{vi}] {R}Échec du Like: {e}{S}")
        client.send_message(entity=channel_entity, message="✅Completed")
        human_delay()
        task(user)
        return None

def _execute_follow_action(user, link, client, channel_entity):
    print(f"{vi}Lien utilisateur : {B}{link}")
    human_delay()
    try:
        cl = ig_connect(user)
        username = link.rstrip('/').split('/')[-1]
        if not username or username == "":
            client.send_message(entity=channel_entity, message="✅Completed")
            human_delay()
            task(user)
            return None
        user_id = cl.user_id_from_username(username)
        cl.user_follow(user_id)
        print(f"{vi}[{V}√{vi}] {V}Follow réussi{S}")
        try:
            cl.feed_timeline()
            time.sleep(2)
        except Exception as e:
            print(f"{J}{e}{S}")
        _update_action_counters(user, 'follow')
        client.send_message(entity=channel_entity, message="✅Completed")
        human_delay()
        task(user)
        return None
    except Exception as e:
        print(f"{vi}[{R}x{vi}] {R}Échec du Follow: {e}{S}")
        client.send_message(entity=channel_entity, message="✅Completed")
        human_delay()
        task(user)
        return None

def _execute_comment_action(user, link, client, channel_entity):
    print(f"{vi}Lien du commentaire : {B}{link}")
    delay = random.randint(350, 400)
    time.sleep(delay)
    mss_comment = coms(user)
    print(f"{J}{mss_comment}")
    try:
        cl = ig_connect(user)
        media_id = cl.media_pk_from_url(link)
        cl.media_comment(media_id, mss_comment)
        print(f"{vi}[{V}+{vi}] {V}Commentaire réussi{S}")
        try:
            cl.feed_timeline()
            time.sleep(2)
        except Exception as e:
            print(f"{J}Scroll down simulé échoué : {e}{S}")
        _update_action_counters(user, 'comment')
        client.send_message(entity=channel_entity, message="✅Completed")
        human_delay()
        task(user)
        return None
    except Exception as e:
        print(f"{vi}[{R}x{vi}] {R}Échec du commentaire: {e}{S}")
        client.send_message(entity=channel_entity, message="✅Completed")
        human_delay()
        task(user)
        return None

def _execute_story_action(user, link, client, channel_entity):
    print(f"{vi}Lien du story : {B}{link}")
    human_delay()
    try:
        cl = ig_connect(user)
        media_id = cl.media_pk_from_url(link)
        cl.media_like(media_id)
        print(f"{vi}[{V}√{vi}] {V}Story like réussi{S}")
        _update_action_counters(user, 'story')
        client.send_message(entity=channel_entity, message="✅Completed")
        human_delay()
        task(user)
        return None
    except Exception as e:
        print(f"{vi}[{R}x{vi}] {R}Échec du Story like: {e}{S}")
        client.send_message(entity=channel_entity, message="✅Completed")
        human_delay()
        task(user)
        return None

def _update_action_counters(user, action_type):
    action_state = load_action_state()
    daily_state = load_daily_state()
    action_state[user][action_type]['count'] += 1
    daily_state[user][action_type] += 1
    save_action_state(action_state)
    save_daily_state(daily_state)

def _handle_sorry_message(user):
    print(f"{J} {user}{S}")
    return None

def _handle_yellow_account_message(user, mss):
    print(f"{co}{mss}{S}")
    if user not in accounts_with_no_tasks:
        accounts_with_no_tasks.append(user)
        save_on_hold_accounts()
        print(f"{J}[-] {user} ajouté à la liste d'attente.{S}")
    time.sleep(2)
    return None

def _handle_other_messages(user, mss, client, channel_entity):
    if "Completed" in mss:
        return _handle_completed_message(user, client, channel_entity)
    elif user in mss:
        return _handle_user_message(user, client, channel_entity)
    else:
        return _handle_comment_message(user, mss, client, channel_entity)

def _handle_completed_message(user, client, channel_entity):
    i = 0
    while True:
        i += 1
        if message() in "✅Completed":
            if i <= 15:
                sys.stdout.write(f"\\r✅Completed {i}s\\r")
                sys.stdout.flush()
                time.sleep(0.1)
            else:
                client.send_message(entity=channel_entity, message="✅Completed")
                task(user)
                return None
        else:
            break
    task(user)
    return None

def _handle_user_message(user, client, channel_entity):
    a = 0
    while True:
        a += 1
        if message() in user:
            if a <= 15:
                sys.stdout.write(f"\\r{user} {a}s\\r")
                sys.stdout.flush()
                time.sleep(0.1)
            else:
                client.send_message(entity=channel_entity, message=f"{user}")
                return None
        else:
            break
    return None

def _handle_comment_message(user, mss, client, channel_entity):
    try:
        cmt = coms1()
        link = re.search('▪️ Link :\\n(.*?)\\n▪️ Action :', str(cmt)).group(1)
        print(f"{vi}Lien du commentaire : {B}{link}")
        print(f"{J}{mss}")
        cl = ig_connect(user)
        media_id = cl.media_pk_from_url(link)
        cl.media_comment(media_id, mss)
        print(f"{vi}[{V}√{vi}] {V}Commentaire réussi{S}")
        client.send_message(entity=channel_entity, message="✅Completed")
        task(user)
        return None
    except Exception as e:
        print(f"{vi}[{R}x{vi}] {R}Échec du commentaire: {e}{S}")
        client.send_message(entity=channel_entity, message="✅Completed")
        task(user)
        return None

def reactivate_accounts():
    on_hold_action = load_on_hold_action()
    now = time.time()
    changed = False
    for action in ACTION_TYPES:
        new_list = []
        for entry in on_hold_action.get(action, []):
            user, hold_time = entry['user'], entry['hold_time']
            if now - hold_time >= 3600:
                print(f"{V}Réactivation automatique de {user} pour l'action {action}.{S}")
                changed = True
            else:
                new_list.append(entry)
        on_hold_action[action] = new_list
    if changed:
        save_on_hold_action(on_hold_action)

def all_accounts_blocked(daily_state, accounts):
    today = datetime.now().strftime('%Y-%m-%d')
    for user in accounts:
        if user not in daily_state or daily_state[user].get('date') != today:
            return False
        for action in ACTION_TYPES:
            if daily_state[user][action] < DAILY_LIMITS[action]:
                return False
    return True

# === IG session directory ===
IG_SESSION_DIR = os.path.join(BASE_DIR, "ig_sessions")
os.makedirs(IG_SESSION_DIR, exist_ok=True)

def ig_connect(username, password=None):
    session_file = os.path.join(IG_SESSION_DIR, f"{username}.json")
    os.makedirs(os.path.dirname(session_file), exist_ok=True)
    cl = Client()
    if os.path.exists(session_file):
        try:
            cl.load_settings(session_file)
            if not cl.user_id:
                if password:
                    cl.login(username, password)
                    cl.dump_settings(session_file)
                else:
                    raise Exception("Mot de passe requis pour la première connexion.")
        except Exception as e:
            print(f"{R}Erreur de chargement de session, reconnexion: {e}{S}")
            if password:
                cl = Client()
                cl.login(username, password)
                cl.dump_settings(session_file)
            else:
                raise Exception("Mot de passe requis pour la reconnexion.")
    else:
        if not password:
            raise Exception("Mot de passe requis pour la première connexion.")
        cl.login(username, password)
        cl.dump_settings(session_file)
    return cl

def get_password_for_username(username):
    compte_path = os.path.join(BASE_DIR, "Compte.txt")
    if not os.path.exists(compte_path):
        return None
    with open(compte_path, 'r') as f:
        for line in f:
            if '|' in line:
                user, pwd = line.strip().split('|', 1)
                if user == username:
                    return pwd
    return None

def add_account_by_cookie():
    clear()
    print(f"{o}--- Ajouter un compte Instagram par sessionid ---{S}")
    username = input(f"{o}Nom d'utilisateur Instagram : {vi}").strip()
    sessionid = input(f"{o}SessionID Instagram (sessionid cookie) : {vi}").strip()
    cl = Client()
    session_file = os.path.join(IG_SESSION_DIR, f"{username}.json")
    try:
        cl.login_by_sessionid(sessionid)
        cl.dump_settings(session_file)
        import uuid, json
        marques = ['TCL','TECNO','SAMSUNG','ITEL','VIVO','REDMI','MEIZU','HUAWEI','HONOR','ONE PLUS','REALME','SONY','POCO','DOCOMO','OPPO','NOKIA']
        manufacturer = random.choice(marques)
        user_agent = user()
        fingerprint = str(uuid.uuid4())
        with open(session_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data['country'] = 'MG'
        data['manufacturer'] = manufacturer
        data['user_agent'] = user_agent
        data['fingerprint'] = fingerprint
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        accounts_path = os.path.join(BASE_DIR, "insta-acct.txt")
        with open(accounts_path, 'a') as f:
            f.write(f"{username}\\n")
        print(f"{V}[√] Compte ajouté avec sessionid valide.{S}")
        time.sleep(2)
    except Exception as e:
        print(f"{R}[-] SessionID invalide ou expiré : {e}{S}")
        time.sleep(3)
    menu()

def add_account_by_login():
    clear()
    print(f"{o}--- Ajouter un compte Instagram par identifiants ---{S}")
    username = input(f"{o}Nom d'utilisateur Instagram : {vi}").strip()
    pwd = input(f"{o}Mot de passe : {vi}").strip()
    cl = Client()
    session_file = os.path.join(IG_SESSION_DIR, f"{username}.json")
    try:
        cl.login(username, pwd)
        cl.dump_settings(session_file)
        import uuid, json
        marques = ['TCL','TECNO','SAMSUNG','ITEL','VIVO','REDMI','MEIZU','HUAWEI','HONOR','ONE PLUS','REALME','SONY','POCO','DOCOMO','OPPO','NOKIA']
        manufacturer = random.choice(marques)
        user_agent = user()
        fingerprint = str(uuid.uuid4())
        with open(session_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data['country'] = 'MG'
        data['manufacturer'] = manufacturer
        data['user_agent'] = user_agent
        data['fingerprint'] = fingerprint
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        accounts_path = os.path.join(BASE_DIR, "insta-acct.txt")
        with open(accounts_path, 'a') as f:
            f.write(f"{username}\\n")
        print(f"{V}[√] Compte ajouté et session sauvegardée.{S}")
        time.sleep(2)
    except Exception as e:
        print(f"{R}[-] Connexion échouée : {e}{S}")
        time.sleep(3)
    menu()

def delete_instagram_account():
    clear()
    print(f"{o}--- Supprimer un compte Instagram ---{S}")
    accounts_path = os.path.join(BASE_DIR, "insta-acct.txt")
    if not os.path.exists(accounts_path):
        print(f"{R}Aucun compte à supprimer.{S}")
        time.sleep(2)
        menu()
        return
    with open(accounts_path, 'r') as f:
        accounts = [line.strip() for line in f if line.strip()]
    if not accounts:
        print(f"{R}Aucun compte à supprimer.{S}")
        time.sleep(2)
        menu()
        return
    print(f"{B}Comptes Instagram enregistrés :{S}")
    for idx, acc in enumerate(accounts, 1):
        print(f"{J}[{idx}] {acc}{S}")
    try:
        choice = int(input(f"{o}Numéro du compte à supprimer : {vi}"))
        if 1 <= choice <= len(accounts):
            user_to_delete = accounts[choice - 1]
            with open(accounts_path, 'w') as f:
                for acc in accounts:
                    if acc != user_to_delete:
                        f.write(acc + '\\n')
            session_file = os.path.join(IG_SESSION_DIR, f"{user_to_delete}.json")
            if os.path.exists(session_file):
                os.remove(session_file)
            print(f"{V}Compte {user_to_delete} supprimé avec succès.{S}")
        else:
            print(f"{R}Choix invalide.{S}")
    except Exception as e:
        print(f"{R}Erreur : {e}{S}")
    time.sleep(2)
    menu()

def show_statistics():
    clear()
    print(f"{o}═════════════════════════════════════════")
    print(f"{vi}📊 STATISTIQUES DU BOT{S}")
    print(f"{o}═════════════════════════════════════════")
    try:
        accounts_path = os.path.join(BASE_DIR, "insta-acct.txt")
        if os.path.exists(accounts_path):
            with open(accounts_path, 'r') as f:
                all_accounts = [line.strip() for line in f if line.strip()]
            print(f"{B}[{V}•{B}] {o}Comptes Instagram enregistrés : {vi}{len(all_accounts)}{S}")
            active_accounts = [user for user in all_accounts if user not in accounts_with_no_tasks]
            on_hold_count = len(accounts_with_no_tasks)
            print(f"{B}[{V}•{B}] {o}Comptes actifs : {V}{len(active_accounts)}{S}")
            print(f"{B}[{V}•{B}] {o}Comptes en attente : {J}{on_hold_count}{S}")
            action_state = load_action_state()
            daily_state = load_daily_state()
            today = datetime.now().strftime('%Y-%m-%d')
            print(f"\n{o}📈 ACTIONS AUJOURD'HUI ({today}){S}")
            print(f"{o}═════════════════════════════════════════")
            total_actions = {'follow': 0, 'like': 0, 'comment': 0, 'story': 0}
            for user in all_accounts:
                if user in daily_state and daily_state[user].get('date') == today:
                    for action_type in ACTION_TYPES:
                        total_actions[action_type] += daily_state[user].get(action_type, 0)
            for action_type in ACTION_TYPES:
                current = total_actions[action_type]
                limit = DAILY_LIMITS[action_type]
                percentage = (current / limit * 100) if limit > 0 else 0
                bar = "█" * int(percentage / 10) + "░" * (10 - int(percentage / 10))
                print(f"{B}[{V}•{B}] {o}{action_type.upper()} : {vi}{current}{o}/{vi}{limit}{o} ({percentage:.1f}%){S}")
                print(f"    {bar} {percentage:.1f}%")
            print(f"\n{o}⏰ LIMITES HORAIRES{S}")
            print(f"{o}═════════════════════════════════════════")
            for action_type in ACTION_TYPES:
                current_hourly = 0
                for user in action_state:
                    if user in action_state and action_type in action_state[user]:
                        current_hourly += action_state[user][action_type].get('count', 0)
                limit_hourly = ACTION_LIMITS[action_type]
                print(f"{B}[{V}•{B}] {o}{action_type.upper()} : {vi}{current_hourly}{o}/{vi}{limit_hourly}{o} par heure{S}")
        else:
            print(f"{R}Aucun compte Instagram enregistré.{S}")
    except Exception as e:
        print(f"{R}Erreur lors du chargement des statistiques : {e}{S}")
    print(f"\n{o}═════════════════════════════════════════")
    input(f"{o}Appuyez sur Entrée pour retourner au menu...{S}")
    menu()

def update_bot():
    clear()
    print(f"{o}--- Mise à jour du Bot ---{S}")
    try:
        print(f"{Bl}Téléchargement de la dernière version...{S}")
        url = "https://raw.githubusercontent.com/Razafimitahiry/serverSmm/refs/heads/main/tahBeKetrika.py"
        response = requests.get(url)
        response.raise_for_status()
        with open(__file__, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"{V}Mise à jour réussie ! Le script va redémarrer.{S}")
        time.sleep(3)
        os.execv(sys.executable, ['python'] + sys.argv)
    except requests.exceptions.RequestException as e:
        print(f"{R}Erreur lors du téléchargement de la mise à jour: {e}{S}")
        print(f"{J}Veuillez réessayer plus tard ou mettre à jour manuellement depuis GitHub.{S}")
        time.sleep(5)
        menu()
    except Exception as e:
        print(f"{R}Une erreur est survenue lors de la mise à jour: {e}{S}")
        time.sleep(5)
        menu()

def restore_on_hold_account():
    clear()
    print(f"{o}--- Gérer les comptes en attente (on hold) ---{S}")
    load_on_hold_accounts()
    if not accounts_with_no_tasks:
        print(f"{V}Aucun compte en attente à gérer.{S}")
        time.sleep(2)
        menu()
        return
    print(f"{B}Comptes en attente :{S}")
    for idx, acc in enumerate(accounts_with_no_tasks, 1):
        print(f"{J}[{idx}] {acc}{S}")
    print(f"\n{R}Tapez SUPPRIMER pour tout supprimer ou le numéro d'un compte à supprimer un à un.{S}")
    print(f"{V}Tapez RESTAURATION pour restaurer automatiquement tous les comptes restaurables sans mot de passe.{S}")
    try:
        choice = input(f"{o}Votre choix : {vi}").strip()
        if choice.upper() == 'SUPPRIMER':
            accounts_with_no_tasks.clear()
            save_on_hold_accounts()
            print(f"{V}Tous les comptes en attente ont été supprimés avec succès.{S}")
            time.sleep(2)
            menu()
            return
        elif choice.upper() == 'RESTAURATION':
            restored = []
            not_restored = []
            for username in accounts_with_no_tasks[:]:
                session_file = os.path.join(IG_SESSION_DIR, f"{username}.json")
                if os.path.exists(session_file):
                    try:
                        cl = ig_connect(username)
                        cl.account_info()
                        restored.append(username)
                        accounts_with_no_tasks.remove(username)
                    except Exception:
                        not_restored.append(username)
                else:
                    not_restored.append(username)
            save_on_hold_accounts()
            print(f"{V}{len(restored)} compte(s) restauré(s) automatiquement sans mot de passe.{S}")
            if not_restored:
                print(f"{J}Comptes restant à restaurer manuellement : {', '.join(not_restored)}{S}")
            time.sleep(3)
            menu()
            return
        elif choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(accounts_with_no_tasks):
                username = accounts_with_no_tasks[idx - 1]
                accounts_with_no_tasks.remove(username)
                save_on_hold_accounts()
                print(f"{V}Compte {username} supprimé de la liste d'attente.{S}")
                time.sleep(2)
                menu()
                return
            else:
                print(f"{R}Choix invalide.{S}")
                time.sleep(2)
                menu()
                return
        else:
            print(f"{R}Entrée invalide.{S}")
            time.sleep(2)
            menu()
            return
    except Exception as e:
        print(f"{R}Erreur : {e}{S}")
        time.sleep(2)
    menu()

if __name__ == "__main__":
    try:
        clear()
        print(logo)
        if not authenticate_user():
            sys.exit(1)
        auto_check_license(interval_minutes=5)
        load_on_hold_accounts()
        print(f"\n{V}🚀 Démarrage du bot...{S}")
        time.sleep(2)
        menu()
    except KeyboardInterrupt:
        print(f"\n{R}🛑 Interruption par l'utilisateur{S}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{R}💥 Erreur critique: {e}{S}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if clien and clien[0].is_connected():
            print(f"{Bl}Déconnexion du client Telegram...{S}")
            try:
                clien[0].disconnect()
            except Exception as e:
                print(f"{J}Avertissement lors de la déconnexion : {e}{S}")
        print(f"{V}Script terminé.{S}")
