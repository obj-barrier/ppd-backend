import csv
import os
from datetime import datetime

USERS_CSV = os.path.join("DemoDatabase", "users.csv")
PREFERENCES_CSV = os.path.join("DemoDatabase", "user_preferences.csv")
SESSIONS_CSV = os.path.join("DemoDatabase", "shopping_sessions.csv")

# ------------------------------------------------------------------------------
# 1. CSV READ/WRITE UTILITY FUNCTIONS
# ------------------------------------------------------------------------------
def load_csv(filepath, fieldnames=None):
    """
    Reads a CSV file and returns a list of dicts.
    If fieldnames is None, use the first row as headers.
    """
    if not os.path.exists(filepath):
        # Return an empty list if file doesn't exist
        return []
    
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f, fieldnames=fieldnames)
        rows = list(reader)
        # If we didn't provide fieldnames explicitly, DictReader automatically
        # takes them from the first row.
        # So if we provided them, we might want to skip the first row if it's a header row.
        if fieldnames is not None:
            # The first row is actually data, not headers
            # do nothing special
            pass
        else:
            # The first row is the header
            pass
    return rows

def save_csv(filepath, rows, fieldnames):
    """
    Writes a list of dicts to a CSV file using the specified fieldnames.
    Overwrites the entire file.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

# ------------------------------------------------------------------------------
# 2. USERS
# ------------------------------------------------------------------------------
def load_users():
    """
    Load users from CSV. Returns a list of dictionaries with keys:
      ['user_id', 'name', 'email', 'password', 'created_at']
    """
    # We assume the first row in the CSV is the header row with these fieldnames:
    fieldnames = ["user_id", "name", "email", "password", "created_at"]
    rows = load_csv(USERS_CSV)  # Let DictReader infer the headers from the first row
    return rows

def save_users(users_list):
    """
    Save the list of user dictionaries to CSV, overwriting the file.
    """
    fieldnames = ["user_id", "name", "email", "password", "created_at"]
    save_csv(USERS_CSV, users_list, fieldnames)

def create_user(name, email, password):
    """
    Creates a new user, appending to users.csv.
    Returns the new user dict.
    """
    users = load_users()

    # Generate new user_id (just max + 1)
    max_id = 0
    for u in users:
        uid = int(u["user_id"])
        if uid > max_id:
            max_id = uid
    new_id = max_id + 1

    created_at = datetime.now().isoformat()

    new_user = {
        "user_id": str(new_id),
        "name": name,
        "email": email,
        "password": password,  
        "created_at": created_at
    }

    users.append(new_user)
    save_users(users)

    return new_user

def get_user_by_id(user_id):
    """
    Retrieve a user dict by user_id (string or int) from users.csv.
    Returns None if not found.
    """
    user_id_str = str(user_id)
    users = load_users()
    for user in users:
        if user["user_id"] == user_id_str:
            return user
    return None

def get_user_by_email(email):
    """
    Retrieve a user dict by email from users.csv.
    Returns None if not found.
    """
    users = load_users()
    for user in users:
        # Assuming emails are stored consistently (case-sensitive or you can use lower())
        if user["email"] == email:
            return user
    return None

# ------------------------------------------------------------------------------
# 3. USER PREFERENCES
# ------------------------------------------------------------------------------
def load_preferences():
    """
    Load preferences from CSV.
    Returns a list of dicts with keys:
      ['preference_id', 'user_id', 'preference_key', 'preference_value']
    """
    return load_csv(PREFERENCES_CSV)  # Let DictReader infer headers

def save_preferences(prefs_list):
    """
    Save preferences to CSV.
    """
    fieldnames = ["preference_id", "user_id", "preference_key", "preference_value"]
    save_csv(PREFERENCES_CSV, prefs_list, fieldnames)

def get_preferences_by_user_id(user_id):
    """
    Returns a list of preference dicts for the given user_id.
    """
    user_id_str = str(user_id)
    prefs = load_preferences()
    user_prefs = []
    for p in prefs:
        if p["user_id"] == user_id_str:
            user_prefs.append(p)
    return user_prefs

def update_user_preferences(user_id, pref_list):
    """
    Create or update multiple preferences for a user.
    `pref_list` is expected to be a list of dicts:
      [{ 'key': 'budget', 'value': '$100-$200' }, ...]
    Returns the updated list of preferences for that user.
    """
    user_id_str = str(user_id)
    all_prefs = load_preferences()

    # We'll create a map of preference_key -> preference_id for quick lookup
    # among existing preferences for this user.
    existing_prefs = [p for p in all_prefs if p["user_id"] == user_id_str]
    pref_key_to_id = {p["preference_key"]: p["preference_id"] for p in existing_prefs}

    # We need to find the max preference_id across all preferences
    max_id = 0
    for p in all_prefs:
        pid = int(p["preference_id"])
        if pid > max_id:
            max_id = pid

    for new_pref in pref_list:
        key = new_pref["key"]
        value = new_pref["value"]

        if key in pref_key_to_id:
            # Update existing preference
            pref_id = pref_key_to_id[key]
            for p in all_prefs:
                if p["preference_id"] == pref_id:
                    p["preference_value"] = value
                    break
        else:
            # Create new preference
            max_id += 1
            new_p = {
                "preference_id": str(max_id),
                "user_id": user_id_str,
                "preference_key": key,
                "preference_value": value
            }
            all_prefs.append(new_p)
            pref_key_to_id[key] = str(max_id)  # track newly added

    save_preferences(all_prefs)
    return get_preferences_by_user_id(user_id)

# ------------------------------------------------------------------------------
# 4. SHOPPING SESSIONS
# ------------------------------------------------------------------------------
def load_shopping_sessions():
    """
    Load shopping sessions from CSV.
    Returns a list of dicts with keys:
      ['session_id', 'user_id', 'thread_id', 'intent', 'created_at', 'updated_at']
    """
    return load_csv(SESSIONS_CSV)

def save_shopping_sessions(sessions_list):
    """
    Save shopping sessions to CSV.
    """
    fieldnames = ["session_id", "user_id", "thread_id", "intent", "created_at", "updated_at"]
    save_csv(SESSIONS_CSV, sessions_list, fieldnames)

def create_shopping_session(user_id, intent, thread_id=None):
    """
    Creates a new shopping session.
    - user_id (int or str)
    - intent (str)
    - thread_id (str) from OpenAI conversation, if already created
    """
    sessions = load_shopping_sessions()

    # Generate new session_id
    max_id = 0
    for s in sessions:
        sid = int(s["session_id"])
        if sid > max_id:
            max_id = sid
    new_id = max_id + 1

    now_str = datetime.now().isoformat()

    new_session = {
        "session_id": str(new_id),
        "user_id": str(user_id),
        "thread_id": thread_id if thread_id else "",
        "intent": intent,
        "created_at": now_str,
        "updated_at": now_str
    }

    sessions.append(new_session)
    save_shopping_sessions(sessions)
    return new_session

def get_shopping_session(session_id):
    """
    Retrieve a shopping session by ID.
    """
    session_id_str = str(session_id)
    sessions = load_shopping_sessions()
    for s in sessions:
        if s["session_id"] == session_id_str:
            return s
    return None

def update_shopping_session(session_id, intent=None, thread_id=None):
    """
    Update certain fields (intent, thread_id) of a shopping session.
    """
    sessions = load_shopping_sessions()
    now_str = datetime.now().isoformat()

    updated_session = None
    for s in sessions:
        if s["session_id"] == str(session_id):
            if intent is not None:
                s["intent"] = intent
            if thread_id is not None:
                s["thread_id"] = thread_id
            s["updated_at"] = now_str
            updated_session = s
            break

    if updated_session:
        save_shopping_sessions(sessions)
    return updated_session

def get_shopping_sessions_by_user_id(user_id):
    """
    Retrieve all shopping sessions associated with the given user_id.
    Returns a list of session dictionaries.
    """
    user_id_str = str(user_id)
    sessions = load_shopping_sessions()
    user_sessions = [s for s in sessions if s["user_id"] == user_id_str]
    return user_sessions


