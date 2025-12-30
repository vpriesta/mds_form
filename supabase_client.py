# # supabase_client.py
# from typing import Any, Dict, List, Optional, Tuple
# import json
# import logging
# import streamlit as st
# import datetime
# import decimal

# # supabase-py client
# # from supabase import create_client, Client

# # Setup logger
# logger = logging.getLogger("supabase_client")
# if not logger.handlers:
#     handler = logging.StreamHandler()
#     handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
#     logger.addHandler(handler)
# logger.setLevel(logging.INFO)


# # @st.cache_resource
# # def get_supabase_client() -> Client:
# #     """
# #     Create and cache a Supabase client instance.

# #     Expects the following keys in Streamlit secrets (or as environment variables):
# #       - SUPABASE_URL
# #       - SUPABASE_ANON_KEY

# #     NOTE: Do NOT put service_role key into client used by Streamlit users.
# #     Use service role only in trusted server-side automation.
# #     """
# #     try:
# #         url = st.secrets.get("SUPABASE_URL") or st.secrets.get("supabase_url")
# #         key = st.secrets.get("SUPABASE_ANON_KEY") or st.secrets.get("supabase_anon_key")

# #         if not url or not key:
# #             # fallback to environment (if user set them there)
# #             import os
# #             url = url or os.environ.get("SUPABASE_URL")
# #             key = key or os.environ.get("SUPABASE_ANON_KEY")

# #         if not url or not key:
# #             raise RuntimeError(
# #                 "Supabase credentials not found. Add SUPABASE_URL and SUPABASE_ANON_KEY to Streamlit secrets."
# #             )

# #         client = create_client(url, key)
# #         # Quick test ping (safe)
# #         _ = client.auth
# #         logger.info("Supabase client created successfully.")
# #         return client
# #     except Exception as e:
# #         logger.exception("Failed to create Supabase client.")
# #         raise


# # -------------------------
# #  Helper functions
# # -------------------------
# def make_json_safe(obj):
#     """Recursively convert objects into JSON-serializable formats."""
#     if isinstance(obj, dict):
#         return {k: make_json_safe(v) for k, v in obj.items()}
#     elif isinstance(obj, list):
#         return [make_json_safe(v) for v in obj]
#     elif isinstance(obj, (datetime.date, datetime.datetime)):
#         return obj.isoformat()
#     elif isinstance(obj, decimal.Decimal):
#         return float(obj)
#     return obj

# def upsert_activity(activity_id: str, user_id: str, payload: Dict[str, Any], status: str = "draft"):
#     # sup = get_supabase_client()
#     try:
#         clean_payload = make_json_safe(payload)

#         row = {
#             "activity_id": activity_id,
#             "user_id": user_id,
#             "data": clean_payload,
#             "status": status
#         }

#         row = make_json_safe(row)   # <── penting banget, cegah date bocor!

#         logger.debug("UPSERT DATA RAW: %s", row)

#         # res = sup.table("activities").upsert(row, on_conflict="activity_id").execute()
        
#         data = res.data[0] if isinstance(res.data, list) and res.data else res.data
#         return True, data

#     except Exception as e:
#         logger.exception("Exception in upsert_activity: %s", str(e))
#         return False, None



# def get_activity(activity_id: str) -> Optional[Dict]:
#     """
#     Fetch a single activity by id. Returns dict or None.
#     """
#     # sup = get_supabase_client()
#     try:
#         # res = sup.table("activities").select("*").eq("activity_id", activity_id).execute()
#         if not res.data:
#             return None

#         return res.data[0]

#     except Exception:
#         logger.exception("Exception in get_activity")
#         return None


# def list_all_activities() -> List[Dict]:
#     # sup = get_supabase_client()
#     try:
#         # res = sup.table("activities").select("*").order("updated_at", desc=True).execute()
#         return res.data or []

#     except Exception:
#         logger.exception("Exception in list_all_activities")
#         return []


# def list_activities_for_user(user_id: str, status: Optional[str] = None, limit: int = 200) -> List[Dict]:
#     # sup = get_supabase_client()
#     try:
#         # qry = (
#         #     sup.table("activities")
#         #     .select("*")
#         #     .eq("user_id", user_id)
#         #     .order("updated_at", desc=True)
#         #     .limit(limit)
#         # )

#         if status:
#             qry = qry.eq("status", status)

#         res = qry.execute()
#         return res.data or []

#     except Exception:
#         logger.exception("Exception in list_activities_for_user")
#         return []


# def list_submitted_activities(limit: int = 500) -> List[Dict]:
#     # sup = get_supabase_client()
#     try:
#         # res = (
#         #     sup.table("activities")
#         #     .select("*")
#         #     .eq("status", "submitted")
#         #     .order("updated_at", desc=True)
#         #     .limit(limit)
#         #     .execute()
#         # )
#         return res.data or []

#     except Exception:
#         logger.exception("Exception in list_submitted_activities")
#         return []


# def mark_status(activity_id: str, status: str, verifier: Optional[str] = None, comment: Optional[str] = None) -> bool:
#     # sup = get_supabase_client()
#     try:
#         update_payload = {"status": status}

#         if verifier:
#             update_payload["verified_by"] = verifier
#         if comment:
#             update_payload["verifier_comment"] = comment

#         # sup.table("activities").update(update_payload).eq("activity_id", activity_id).execute()
#         return True

#     except Exception:
#         logger.exception("Exception in mark_status")
#         return False


# def delete_activity(activity_id: str) -> bool:
#     # sup = get_supabase_client()
#     try:
#         # sup.table("activities").delete().eq("activity_id", activity_id).execute()
#         return True

#     except Exception:
#         logger.exception("Exception in delete_activity")
#         return False


# # -------------------------
# #  Convenience helpers
# # -------------------------
# def submit_activity(activity_id: str, user_id: str) -> bool:
#     current = get_activity(activity_id)
#     if not current:
#         logger.error("submit_activity: not found %s", activity_id)
#         return False

#     return mark_status(activity_id, "submitted")


# def mark_verified(activity_id: str, verifier: str, comment: Optional[str] = None) -> bool:
#     return mark_status(activity_id, "verified", verifier=verifier, comment=comment)


# # -------------------------
# #  Example usage (commented)
# # -------------------------
# # from supabase_client import upsert_activity, get_activity, list_activities_for_user
# #
# # success, row = upsert_activity("act-123", "user1", {"judul": "Test"}, status="draft")
# # row = get_activity("act-123")
# # activities = list_activities_for_user("user1")

# supabase_client.py  (GSHEET VERSION)
from typing import Any, Dict, List, Optional
import json
import logging
import streamlit as st
import datetime
import decimal

import gspread
from google.oauth2.service_account import Credentials

# -------------------------------------------------
# Logger
# -------------------------------------------------
logger = logging.getLogger("gsheet_client")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# -------------------------------------------------
# Google Sheet setup
# -------------------------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_NAME = "MS Form Temp Table"      # Google Sheet file name
WORKSHEET_NAME = "Sheet1"        # Tab name


@st.cache_resource
def get_worksheet():
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)

    sheet = client.open(SHEET_NAME)
    ws = sheet.worksheet(WORKSHEET_NAME)

    # Ensure header exists
    if ws.row_count == 0 or ws.get("A1") == [[]]:
        ws.append_row(
            ["activity_id", "user_id", "status", "data", "updated_at"]
        )

    return ws


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def make_json_safe(obj):
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    elif isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)
    return obj


def _now():
    return datetime.datetime.utcnow().isoformat()


def _find_row(ws, activity_id: str) -> Optional[int]:
    records = ws.get_all_records()
    for idx, row in enumerate(records, start=2):
        if row.get("activity_id") == activity_id:
            return idx
    return None


# -------------------------------------------------
# CORE FUNCTIONS (same names as before)
# -------------------------------------------------
def upsert_activity(activity_id: str, user_id: str, payload: Dict[str, Any], status: str = "draft"):
    try:
        ws = get_worksheet()

        clean_payload = make_json_safe(payload)
        json_data = json.dumps(clean_payload, ensure_ascii=False)

        row_idx = _find_row(ws, activity_id)

        row_data = [
            activity_id,
            user_id,
            status,
            json_data,
            _now(),
        ]

        if row_idx:
            ws.update(f"A{row_idx}:E{row_idx}", [row_data])
        else:
            ws.append_row(row_data)

        return True, {
            "activity_id": activity_id,
            "user_id": user_id,
            "status": status,
            "data": clean_payload,
        }

    except Exception as e:
        logger.exception("upsert_activity failed")
        return False, None


def get_activity(activity_id: str) -> Optional[Dict]:
    try:
        ws = get_worksheet()
        records = ws.get_all_records()

        for row in records:
            if row["activity_id"] == activity_id:
                row["data"] = json.loads(row["data"]) if row.get("data") else {}
                return row

        return None

    except Exception:
        logger.exception("get_activity failed")
        return None


def list_all_activities() -> List[Dict]:
    try:
        ws = get_worksheet()
        records = ws.get_all_records()

        for r in records:
            r["data"] = json.loads(r["data"]) if r.get("data") else {}

        return records

    except Exception:
        logger.exception("list_all_activities failed")
        return []


def list_activities_for_user(user_id: str, status: Optional[str] = None, limit: int = 200):
    try:
        ws = get_worksheet()
        records = ws.get_all_records()

        out = []
        for r in records:
            if r["user_id"] != user_id:
                continue
            if status and r["status"] != status:
                continue

            r["data"] = json.loads(r["data"]) if r.get("data") else {}
            out.append(r)

        return out[:limit]

    except Exception:
        logger.exception("list_activities_for_user failed")
        return []


def list_submitted_activities(limit: int = 500):
    try:
        ws = get_worksheet()
        records = ws.get_all_records()

        out = []
        for r in records:
            if r["status"] == "submitted":
                r["data"] = json.loads(r["data"]) if r.get("data") else {}
                out.append(r)

        return out[:limit]

    except Exception:
        logger.exception("list_submitted_activities failed")
        return []


def mark_status(activity_id: str, status: str, verifier: Optional[str] = None, comment: Optional[str] = None) -> bool:
    try:
        ws = get_worksheet()
        row_idx = _find_row(ws, activity_id)
        if not row_idx:
            return False

        ws.update(f"C{row_idx}", status)
        ws.update(f"E{row_idx}", _now())
        return True

    except Exception:
        logger.exception("mark_status failed")
        return False


def delete_activity(activity_id: str) -> bool:
    try:
        ws = get_worksheet()
        row_idx = _find_row(ws, activity_id)
        if not row_idx:
            return False

        ws.delete_rows(row_idx)
        return True

    except Exception:
        logger.exception("delete_activity failed")
        return False


# -------------------------------------------------
# Convenience helpers (unchanged)
# -------------------------------------------------
def submit_activity(activity_id: str, user_id: str) -> bool:
    return mark_status(activity_id, "submitted")


def mark_verified(activity_id: str, verifier: str, comment: Optional[str] = None) -> bool:
    return mark_status(activity_id, "verified")

