"""
PH-Lending Pro — Backup Module
Local backup (DB + Excel + JSON) and Google Drive sync.
"""

import os
import json
import shutil
import socket
import sqlite3
from datetime import datetime

from database import (
    get_connection, rows_to_list, get_db_path,
    APP_SUPPORT_DIR, BACKUP_DIR, MEDIA_DIR
)
from excel_export import export_all_to_excel


def check_internet(host="8.8.8.8", port=53, timeout=3):
    """Check if internet is available."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except (socket.error, OSError):
        return False


def _export_json(output_path):
    """Export all database data to a JSON file."""
    conn = get_connection()
    cursor = conn.cursor()

    data = {}

    # Export each table
    tables = ['clients', 'loans', 'amortization_schedule', 'payments',
              'payment_allocations', 'documents', 'referral_commissions',
              'penalties', 'settings', 'schema_migrations', 'audit_events']

    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        data[table] = rows_to_list(cursor.fetchall())

    conn.close()

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return output_path


def _backup_sqlite_database(output_path):
    """Create a consistent SQLite copy, including data still held in WAL."""
    source = get_connection()
    target = sqlite3.connect(output_path)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
    return output_path


def backup_local():
    """
    Create a full local backup in 3 formats:
    - .db (SQLite copy)
    - .xlsx (Excel export)
    - .json (Raw data)

    Returns dict with paths and status.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_subdir = os.path.join(BACKUP_DIR, f"backup_{timestamp}")
    os.makedirs(backup_subdir, exist_ok=True)

    results = {"timestamp": timestamp, "files": [], "success": True, "errors": []}

    # 1. Copy SQLite database
    try:
        db_backup = os.path.join(backup_subdir, f"phlending_{timestamp}.db")
        _backup_sqlite_database(db_backup)
        results["files"].append({"type": "db", "path": db_backup})
    except Exception as e:
        results["errors"].append(f"DB backup failed: {str(e)}")
        results["success"] = False

    # 2. Excel export
    try:
        xlsx_path = os.path.join(backup_subdir, f"phlending_{timestamp}.xlsx")
        export_all_to_excel(xlsx_path)
        results["files"].append({"type": "xlsx", "path": xlsx_path})
    except Exception as e:
        results["errors"].append(f"Excel backup failed: {str(e)}")
        results["success"] = False

    # 3. JSON export
    try:
        json_path = os.path.join(backup_subdir, f"phlending_{timestamp}.json")
        _export_json(json_path)
        results["files"].append({"type": "json", "path": json_path})
    except Exception as e:
        results["errors"].append(f"JSON backup failed: {str(e)}")
        results["success"] = False

    return results


def get_backup_status():
    """
    Check backup and connectivity status.
    Returns dict with online status and last backup info.
    """
    online = check_internet()

    # Find last backup
    last_backup = None
    if os.path.exists(BACKUP_DIR):
        backups = sorted([
            d for d in os.listdir(BACKUP_DIR)
            if os.path.isdir(os.path.join(BACKUP_DIR, d)) and d.startswith("backup_")
        ], reverse=True)
        if backups:
            last_backup = backups[0].replace("backup_", "")

    return {
        "online": online,
        "last_backup": last_backup,
        "db_path": get_db_path(),
        "backup_dir": BACKUP_DIR,
        "media_dir": MEDIA_DIR
    }


def list_backups():
    """List all available backups."""
    if not os.path.exists(BACKUP_DIR):
        return []

    backups = []
    for d in sorted(os.listdir(BACKUP_DIR), reverse=True):
        full_path = os.path.join(BACKUP_DIR, d)
        if os.path.isdir(full_path) and d.startswith("backup_"):
            files = os.listdir(full_path)
            size = sum(os.path.getsize(os.path.join(full_path, f)) for f in files)
            backups.append({
                "name": d,
                "path": full_path,
                "files": files,
                "size_mb": round(size / (1024 * 1024), 2),
                "timestamp": d.replace("backup_", "")
            })

    return backups


def _resolve_backup_dir(backup_name):
    """Return a backup directory only if it lives inside BACKUP_DIR."""
    name = os.path.basename(str(backup_name or "").strip())
    if not name.startswith("backup_"):
        raise ValueError("Invalid backup name.")

    base = os.path.realpath(BACKUP_DIR)
    candidate = os.path.realpath(os.path.join(BACKUP_DIR, name))
    if os.path.commonpath([base, candidate]) != base or not os.path.isdir(candidate):
        raise ValueError("Backup folder not found.")
    return candidate


def _find_backup_db(backup_dir):
    """Find the SQLite DB file inside a backup folder."""
    db_files = [
        f for f in os.listdir(backup_dir)
        if f.lower().endswith(".db") and os.path.isfile(os.path.join(backup_dir, f))
    ]
    if not db_files:
        raise ValueError("No SQLite database found in this backup.")
    db_files.sort()
    return os.path.join(backup_dir, db_files[0])


def _validate_backup_db(db_path):
    """Run a minimal integrity and schema check before restoring."""
    conn = sqlite3.connect(db_path)
    try:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise ValueError(f"Backup integrity check failed: {integrity}")

        required_tables = {"clients", "loans", "payments", "settings"}
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        table_names = {row[0] for row in rows}
        missing = sorted(required_tables - table_names)
        if missing:
            raise ValueError(f"Backup is missing required tables: {', '.join(missing)}")
    finally:
        conn.close()


def restore_local_backup(backup_name):
    """
    Restore the active profile database from a local backup.
    A fresh safety backup is created before the active database is replaced.
    """
    backup_dir = _resolve_backup_dir(backup_name)
    source_db = _find_backup_db(backup_dir)
    _validate_backup_db(source_db)

    safety_backup = backup_local()
    if not safety_backup.get("success"):
        errors = ", ".join(safety_backup.get("errors", [])) or "unknown error"
        raise RuntimeError(f"Safety backup failed before restore: {errors}")

    target_db = get_db_path()
    for suffix in ("-wal", "-shm"):
        sidecar = target_db + suffix
        if os.path.exists(sidecar):
            os.remove(sidecar)

    shutil.copy2(source_db, target_db)

    for suffix in ("-wal", "-shm"):
        sidecar = target_db + suffix
        if os.path.exists(sidecar):
            os.remove(sidecar)

    return {
        "success": True,
        "restored_from": backup_name,
        "source_db": source_db,
        "safety_backup": safety_backup
    }


# ── Google Drive Integration ─────────────────────────────────────

DRIVE_CREDENTIALS_PATH = os.path.join(APP_SUPPORT_DIR, "google_credentials.json")
DRIVE_TOKEN_PATH = os.path.join(APP_SUPPORT_DIR, "google_token.json")
DRIVE_FOLDER_NAME = "PH-Lending Backups"


def is_drive_configured():
    """Check if Google Drive credentials are set up."""
    return os.path.exists(DRIVE_CREDENTIALS_PATH)


def sync_to_drive():
    """
    Upload latest backup to Google Drive.
    Requires google_credentials.json in app support dir.
    Returns status dict.
    """
    if not is_drive_configured():
        return {
            "success": False,
            "error": "Google Drive not configured. Place credentials.json in app support folder."
        }

    if not check_internet():
        return {
            "success": False,
            "error": "No internet connection. Backup saved locally."
        }

    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        import pickle

        SCOPES = ['https://www.googleapis.com/auth/drive.file']

        creds = None
        if os.path.exists(DRIVE_TOKEN_PATH):
            with open(DRIVE_TOKEN_PATH, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    DRIVE_CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(DRIVE_TOKEN_PATH, 'wb') as token:
                pickle.dump(creds, token)

        service = build('drive', 'v3', credentials=creds)

        # Find or create backup folder
        query = f"name='{DRIVE_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, spaces='drive').execute()
        folders = results.get('files', [])

        if folders:
            folder_id = folders[0]['id']
        else:
            folder_metadata = {
                'name': DRIVE_FOLDER_NAME,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = service.files().create(body=folder_metadata, fields='id').execute()
            folder_id = folder.get('id')

        # Create fresh local backup first
        backup_result = backup_local()
        if not backup_result['success']:
            return {"success": False, "error": "Local backup failed before upload"}

        # Upload each backup file
        uploaded = []
        for file_info in backup_result['files']:
            file_metadata = {
                'name': os.path.basename(file_info['path']),
                'parents': [folder_id]
            }
            media = MediaFileUpload(file_info['path'])
            uploaded_file = service.files().create(
                body=file_metadata, media_body=media, fields='id,name'
            ).execute()
            uploaded.append(uploaded_file['name'])

        return {
            "success": True,
            "folder_id": folder_id,
            "uploaded_files": uploaded,
            "drive_url": f"https://drive.google.com/drive/folders/{folder_id}"
        }

    except Exception as e:
        # Fallback: ensure local backup exists
        backup_local()
        return {
            "success": False,
            "error": f"Drive sync failed: {str(e)}. Local backup created as fallback."
        }


def open_drive_folder():
    """Get the Google Drive folder URL for browser opening."""
    if not is_drive_configured():
        return None

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        import pickle

        if not os.path.exists(DRIVE_TOKEN_PATH):
            return None

        with open(DRIVE_TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)

        service = build('drive', 'v3', credentials=creds)
        query = f"name='{DRIVE_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, spaces='drive').execute()
        folders = results.get('files', [])

        if folders:
            return f"https://drive.google.com/drive/folders/{folders[0]['id']}"

    except Exception:
        pass

    return None
