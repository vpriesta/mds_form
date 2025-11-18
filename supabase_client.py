# supabase_client.py
from typing import Any, Dict, List, Optional, Tuple
import json
import logging
import streamlit as st
import datetime

# supabase-py client
from supabase import create_client, Client

# Setup logger
logger = logging.getLogger("supabase_client")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


@st.cache_resource
def get_supabase_client() -> Client:
    """
    Create and cache a Supabase client instance.

    Expects the following keys in Streamlit secrets (or as environment variables):
      - SUPABASE_URL
      - SUPABASE_ANON_KEY

    NOTE: Do NOT put service_role key into client used by Streamlit users.
    Use service role only in trusted server-side automation.
    """
    try:
        url = st.secrets.get("SUPABASE_URL") or st.secrets.get("supabase_url")
        key = st.secrets.get("SUPABASE_ANON_KEY") or st.secrets.get("supabase_anon_key")

        if not url or not key:
            # fallback to environment (if user set them there)
            import os
            url = url or os.environ.get("SUPABASE_URL")
            key = key or os.environ.get("SUPABASE_ANON_KEY")

        if not url or not key:
            raise RuntimeError(
                "Supabase credentials not found. Add SUPABASE_URL and SUPABASE_ANON_KEY to Streamlit secrets."
            )

        client = create_client(url, key)
        # Quick test ping (safe)
        _ = client.auth
        logger.info("Supabase client created successfully.")
        return client
    except Exception as e:
        logger.exception("Failed to create Supabase client.")
        raise


# -------------------------
#  Helper functions
# -------------------------
def convert_dates(obj):
    if isinstance(obj, dict):
        return {k: convert_dates(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_dates(v) for v in obj]
    elif isinstance(obj, datetime.date):
        return obj.isoformat()  # YYYY-MM-DD
    return obj

def upsert_activity(activity_id: str, user_id: str, payload: Dict[str, Any], status: str = "draft"):
    sup = get_supabase_client()
    try:
        clean_payload = convert_dates(payload)

        row = {
            "activity_id": activity_id,
            "user_id": user_id,
            "data": clean_payload,
            "status": status
        }
        
        res = sup.table("activities").upsert(row, on_conflict="activity_id").execute()
        data = res.data[0] if isinstance(res.data, list) and res.data else res.data
        return True, data

    except Exception as e:
        logger.exception("Exception in upsert_activity: %s", str(e))
        return False, None


def get_activity(activity_id: str) -> Optional[Dict]:
    """
    Fetch a single activity by id. Returns dict or None.
    """
    sup = get_supabase_client()
    try:
        res = sup.table("activities").select("*").eq("activity_id", activity_id).execute()
        if not res.data:
            return None

        return res.data[0]

    except Exception:
        logger.exception("Exception in get_activity")
        return None


def list_all_activities() -> List[Dict]:
    sup = get_supabase_client()
    try:
        res = sup.table("activities").select("*").order("updated_at", desc=True).execute()
        return res.data or []

    except Exception:
        logger.exception("Exception in list_all_activities")
        return []


def list_activities_for_user(user_id: str, status: Optional[str] = None, limit: int = 200) -> List[Dict]:
    sup = get_supabase_client()
    try:
        qry = (
            sup.table("activities")
            .select("*")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .limit(limit)
        )

        if status:
            qry = qry.eq("status", status)

        res = qry.execute()
        return res.data or []

    except Exception:
        logger.exception("Exception in list_activities_for_user")
        return []


def list_submitted_activities(limit: int = 500) -> List[Dict]:
    sup = get_supabase_client()
    try:
        res = (
            sup.table("activities")
            .select("*")
            .eq("status", "submitted")
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []

    except Exception:
        logger.exception("Exception in list_submitted_activities")
        return []


def mark_status(activity_id: str, status: str, verifier: Optional[str] = None, comment: Optional[str] = None) -> bool:
    sup = get_supabase_client()
    try:
        update_payload = {"status": status}

        if verifier:
            update_payload["verified_by"] = verifier
        if comment:
            update_payload["verifier_comment"] = comment

        sup.table("activities").update(update_payload).eq("activity_id", activity_id).execute()
        return True

    except Exception:
        logger.exception("Exception in mark_status")
        return False


def delete_activity(activity_id: str) -> bool:
    sup = get_supabase_client()
    try:
        sup.table("activities").delete().eq("activity_id", activity_id).execute()
        return True

    except Exception:
        logger.exception("Exception in delete_activity")
        return False


# -------------------------
#  Convenience helpers
# -------------------------
def submit_activity(activity_id: str, user_id: str) -> bool:
    current = get_activity(activity_id)
    if not current:
        logger.error("submit_activity: not found %s", activity_id)
        return False

    return mark_status(activity_id, "submitted")


def mark_verified(activity_id: str, verifier: str, comment: Optional[str] = None) -> bool:
    return mark_status(activity_id, "verified", verifier=verifier, comment=comment)


# -------------------------
#  Example usage (commented)
# -------------------------
# from supabase_client import upsert_activity, get_activity, list_activities_for_user
#
# success, row = upsert_activity("act-123", "user1", {"judul": "Test"}, status="draft")
# row = get_activity("act-123")
# activities = list_activities_for_user("user1")
