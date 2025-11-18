# supabase_client.py
from typing import Any, Dict, List, Optional, Tuple
import json
import logging
import streamlit as st

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
def upsert_activity(activity_id: str, user_id: str, payload: Dict[str, Any], status: str = "draft") -> Tuple[bool, Optional[Dict]]:
    """
    Insert or update an activity record in the 'activities' table.

    Arguments:
      - activity_id: unique id for the activity (uuid or string)
      - user_id: owner identifier
      - payload: dict -> will be stored in `data` jsonb column
      - status: draft/submitted/verified/rejected/etc.

    Returns: (success, row_dict_or_none)
    """
    sup = get_supabase_client()
    try:
        row = {
            "id": activity_id,
            "user_id": user_id,
            "data": payload,
            "status": status
        }
        res = sup.table("activities").upsert(row, on_conflict="id").execute()
        if res.error:
            logger.error("Upsert error: %s", res.error.message if getattr(res, "error", None) else res)
            return False, None
        # res.data may be a list
        data = res.data[0] if isinstance(res.data, list) and res.data else res.data
        return True, data
    except Exception as e:
        logger.exception("Exception in upsert_activity")
        return False, None


def get_activity(activity_id: str) -> Optional[Dict]:
    """
    Fetch a single activity by id. Returns dict or None.
    """
    sup = get_supabase_client()
    try:
        res = sup.table("activities").select("*").eq("id", activity_id).single().execute()
        if res.error:
            # Not found or other error
            logger.debug("get_activity error: %s", res.error.message if getattr(res, "error", None) else res)
            return None
        return res.data
    except Exception:
        logger.exception("Exception in get_activity")
        return None


def list_all_activities():
    """Return all activities without filtering by user or status."""
    sup = get_supabase_client()
    try:
        response = sup.table("activities").select("*").order("updated_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        print("❌ Error listing all activities:", e)
        return []


def list_activities_for_user(user_id: str, status: Optional[str] = None, limit: int = 200) -> List[Dict]:
    """
    List activities for a given user. Optionally filter by status.
    """
    sup = get_supabase_client()
    try:
        qry = sup.table("activities").select("*").eq("user_id", user_id).order("updated_at", desc=True).limit(limit)
        if status:
            qry = qry.eq("status", status)
        res = qry.execute()
        if res.error:
            logger.error("list_activities_for_user error: %s", res.error)
            return []
        return res.data or []
    except Exception:
        logger.exception("Exception in list_activities_for_user")
        return []


def list_submitted_activities(limit: int = 500) -> List[Dict]:
    """
    Return activities with status='submitted'. Used by verifier page.
    """
    sup = get_supabase_client()
    try:
        res = sup.table("activities").select("*").eq("status", "submitted").order("updated_at", desc=True).limit(limit).execute()
        if res.error:
            logger.error("list_submitted_activities error: %s", res.error)
            return []
        return res.data or []
    except Exception:
        logger.exception("Exception in list_submitted_activities")
        return []


def mark_status(activity_id: str, status: str, verifier: Optional[str] = None, comment: Optional[str] = None) -> bool:
    """
    Update status of an activity. Adds verifier and comment metadata if provided.
    """
    sup = get_supabase_client()
    try:
        update_payload = {"status": status}
        if verifier:
            update_payload["verified_by"] = verifier
        if comment:
            update_payload["verifier_comment"] = comment

        res = sup.table("activities").update(update_payload).eq("id", activity_id).execute()
        if res.error:
            logger.error("mark_status error: %s", res.error)
            return False
        return True
    except Exception:
        logger.exception("Exception in mark_status")
        return False


def delete_activity(activity_id: str) -> bool:
    sup = get_supabase_client()
    try:
        res = sup.table("activities").delete().eq("id", activity_id).execute()
        if res.error:
            logger.error("delete_activity error: %s", res.error)
            return False
        return True
    except Exception:
        logger.exception("Exception in delete_activity")
        return False


# -------------------------
#  Convenience helpers
# -------------------------
def submit_activity(activity_id: str, user_id: str) -> bool:
    """
    Mark an activity as submitted. Also sets submitted timestamp inside data if possible.
    """
    # try to attach submitted_at inside data jsonb (optional)
    current = get_activity(activity_id)
    if not current:
        logger.error("submit_activity: not found %s", activity_id)
        return False

    data = current.get("data", {}) or {}
    data["submitted_at"] = data.get("submitted_at") or None  # placeholder, will be replaced below

    # We will use server side timestamp by updating status; optional to store timestamp in data
    success = mark_status(activity_id, "submitted")
    return success


def mark_verified(activity_id: str, verifier: str, comment: Optional[str] = None) -> bool:
    """
    Mark activity as verified. Useful for automation that moves to company DB later.
    """
    return mark_status(activity_id, "verified", verifier=verifier, comment=comment)


# -------------------------
#  Example usage (commented)
# -------------------------
# from supabase_client import upsert_activity, get_activity, list_activities_for_user
#
# success, row = upsert_activity("act-123", "user1", {"judul": "Test"}, status="draft")
# row = get_activity("act-123")
# activities = list_activities_for_user("user1")