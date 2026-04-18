"""
sheets.py — All Google Sheets read/write operations
With caching to avoid hitting Google Sheets API rate limits.
"""
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import bcrypt
import time

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SPREADSHEET_ID = "1svY3lp6RUTp4K-bigbx2JDAeh8RNLACsuXCYqxP4QgQ"

SHEET_USERS     = "users"
SHEET_AUDIT_LOG = "audit_log"


# ─── CONNECTION ────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def get_client():
    """Authenticate once and cache the client forever."""
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


@st.cache_resource(show_spinner=False)
def get_spreadsheet():
    """Cache the spreadsheet object."""
    return get_client().open_by_key(SPREADSHEET_ID)


def ensure_sheet(spreadsheet, name: str, headers: list):
    """Get sheet by name, create with headers if missing."""
    try:
        return spreadsheet.worksheet(name)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=name, rows=2000, cols=len(headers))
        ws.append_row(headers)
        return ws


def safe_call(fn, retries=3, wait=5):
    """Retry wrapper for API calls that may hit rate limits."""
    for attempt in range(retries):
        try:
            return fn()
        except gspread.exceptions.APIError as e:
            if "429" in str(e) and attempt < retries - 1:
                time.sleep(wait * (attempt + 1))
            else:
                raise


# ─── USER MANAGEMENT ───────────────────────────────────────────────────────────

def get_users_sheet(spreadsheet):
    return ensure_sheet(spreadsheet, SHEET_USERS,
                        ["username", "password_hash", "role", "created_at", "last_active"])


@st.cache_data(ttl=30, show_spinner=False)
def load_users_cached(_spreadsheet_id: str) -> dict:
    """
    Cache users for 30 seconds to avoid repeated reads.
    Uses spreadsheet_id as key (hashable) instead of the object itself.
    """
    sp = get_spreadsheet()
    ws = get_users_sheet(sp)
    records = safe_call(ws.get_all_records)
    return {r["username"]: r for r in records}


def load_users(spreadsheet=None) -> dict:
    """Public interface — always reads from cache."""
    return load_users_cached(SPREADSHEET_ID)


def invalidate_users_cache():
    """Call after any write to users sheet to force refresh."""
    load_users_cached.clear()


def create_user(spreadsheet, username: str, password: str, role: str = "auditor"):
    users = load_users()
    if username in users:
        return False, "اسم المستخدم موجود مسبقاً"
    ws     = get_users_sheet(spreadsheet)
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    safe_call(lambda: ws.append_row(
        [username, hashed, role, datetime.now().isoformat(), ""]
    ))
    invalidate_users_cache()
    return True, "تم إنشاء المستخدم بنجاح"


def delete_user(spreadsheet, username: str):
    ws      = get_users_sheet(spreadsheet)
    records = safe_call(ws.get_all_values)
    for i, row in enumerate(records):
        if row and row[0] == username:
            safe_call(lambda: ws.delete_rows(i + 1))
            try:
                spreadsheet.del_worksheet(
                    spreadsheet.worksheet(f"user_{username}")
                )
            except Exception:
                pass
            invalidate_users_cache()
            return True
    return False


def verify_password(spreadsheet, username: str, password: str):
    users = load_users()
    if username not in users:
        return False, None
    u = users[username]
    if bcrypt.checkpw(password.encode(), u["password_hash"].encode()):
        # Update last_active in background (non-blocking)
        try:
            ws   = get_users_sheet(spreadsheet)
            cell = safe_call(lambda: ws.find(username))
            safe_call(lambda: ws.update_cell(cell.row, 5, datetime.now().isoformat()))
            invalidate_users_cache()
        except Exception:
            pass
        return True, u
    return False, None


def update_password(spreadsheet, username: str, new_password: str):
    ws     = get_users_sheet(spreadsheet)
    cell   = safe_call(lambda: ws.find(username))
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    safe_call(lambda: ws.update_cell(cell.row, 2, hashed))
    invalidate_users_cache()


# ─── USER DATA SHEET ───────────────────────────────────────────────────────────

DATA_HEADERS = [
    "row_id", "leg_name", "entity_final", "type",
    "entity_audited", "type_audited", "audit_status", "audit_notes",
    "last_updated",
]


def get_user_sheet(spreadsheet, username: str):
    return ensure_sheet(spreadsheet, f"user_{username}", DATA_HEADERS)


def save_user_data(spreadsheet, username: str, groups: list):
    """Write all audit rows for this user to their sheet (initial upload)."""
    ws   = get_user_sheet(spreadsheet, username)
    rows = [DATA_HEADERS]
    row_id = 0
    for g in groups:
        for r in g["rows"]:
            rows.append([
                row_id,
                r["leg_name"],
                r["entity_final"],
                r["type"],
                r["entity_audited"],
                r["type_audited"],
                r["audit_status"],
                r["audit_notes"],
                datetime.now().isoformat(),
            ])
            row_id += 1
    safe_call(ws.clear)
    safe_call(lambda: ws.update(rows))


def save_single_row(spreadsheet, username: str, row_id: int, row_data: dict):
    """Update only one row — fast and minimal API calls."""
    ws      = get_user_sheet(spreadsheet, username)
    records = safe_call(ws.get_all_values)
    for i, rec in enumerate(records):
        if rec and str(rec[0]) == str(row_id):
            safe_call(lambda: ws.update(
                f"A{i+1}:I{i+1}",
                [[
                    row_id,
                    row_data["leg_name"],
                    row_data["entity_final"],
                    row_data["type"],
                    row_data["entity_audited"],
                    row_data["type_audited"],
                    row_data["audit_status"],
                    row_data["audit_notes"],
                    datetime.now().isoformat(),
                ]]
            ))
            return


@st.cache_data(ttl=60, show_spinner=False)
def load_user_data_cached(_spreadsheet_id: str, username: str):
    """Cache user data for 60 seconds."""
    sp = get_spreadsheet()
    try:
        ws      = get_user_sheet(sp, username)
        records = safe_call(ws.get_all_records)
        return records if records else None
    except Exception:
        return None


def load_user_data(spreadsheet, username: str):
    return load_user_data_cached(SPREADSHEET_ID, username)


def invalidate_user_data_cache():
    load_user_data_cached.clear()


def rebuild_groups_from_sheet(records: list) -> list:
    """Convert flat sheet records back into grouped structure."""
    seen, groups = {}, []
    for i, r in enumerate(records):
        name = r["leg_name"]
        if name not in seen:
            seen[name] = len(groups)
            groups.append({"leg_name": name, "rows": []})
        groups[seen[name]]["rows"].append({
            "orig_idx":       i,
            "leg_name":       r["leg_name"],
            "entity_final":   r["entity_final"],
            "type":           r["type"],
            "entity_audited": r["entity_audited"],
            "type_audited":   r["type_audited"],
            "audit_status":   r["audit_status"],
            "audit_notes":    r["audit_notes"],
        })
    return groups


# ─── AUDIT LOG ─────────────────────────────────────────────────────────────────

def log_change(spreadsheet, username: str, leg_name: str,
               field: str, old_val: str, new_val: str):
    if old_val == new_val:
        return
    try:
        ws = ensure_sheet(
            spreadsheet, SHEET_AUDIT_LOG,
            ["timestamp", "username", "leg_name", "field", "old_value", "new_value"]
        )
        safe_call(lambda: ws.append_row([
            datetime.now().isoformat(),
            username, leg_name, field, old_val, new_val,
        ]))
    except Exception:
        pass  # Never let logging break the main flow


# ─── ADMIN DASHBOARD ───────────────────────────────────────────────────────────

@st.cache_data(ttl=30, show_spinner=False)
def get_all_users_progress_cached(_spreadsheet_id: str) -> list:
    sp    = get_spreadsheet()
    users = load_users()
    result = []
    for username, info in users.items():
        if info["role"] == "admin":
            continue
        try:
            ws       = sp.worksheet(f"user_{username}")
            records  = safe_call(ws.get_all_records)
            total    = len(records)
            reviewed = sum(1 for r in records if r.get("audit_status") != "لم يُراجع")
            modified = sum(1 for r in records if r.get("audit_status") == "معدّل")
            pct      = int(reviewed / total * 100) if total else 0
        except Exception:
            total = reviewed = modified = pct = 0
        result.append({
            "username":    username,
            "total":       total,
            "reviewed":    reviewed,
            "modified":    modified,
            "pct":         pct,
            "last_active": info.get("last_active", ""),
        })
    return result


def get_all_users_progress(spreadsheet) -> list:
    return get_all_users_progress_cached(SPREADSHEET_ID)
