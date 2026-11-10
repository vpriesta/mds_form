import streamlit as st
import hashlib
import json
from datetime import datetime

# Import Google Sheet client functions
from gsheet_client import (
    list_activities_for_user,
    list_all_activities,
    delete_activity,
)

def reset_form_state():
    keys_to_reset = [
        "halaman_awal",
        "blok_1_3",
        "variables",
        "blok_4",
        "blok_5",
        "blok_6_8",
        "indicators",
        "form_data",
        "current_activity_id"
    ]

    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]

# --- Function to hash passwords ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- Retrieve credentials from secrets.toml ---
users = st.secrets["users"]
roles = st.secrets["roles"]

# --- Session state for login ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None

# --- Login form ---
if not st.session_state.authenticated:
    st.title("🔐 Login")
    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")

    if st.button("Login"):
        if username_input in users and users[username_input] == hash_password(password_input):
            st.session_state.authenticated = True
            st.session_state.username = username_input
            st.session_state.user_id = st.session_state.username
            st.session_state.role = roles.get(username_input, "user")
            st.success(f"Welcome back, {username_input}!")
            st.rerun()
        else:
            st.error("Invalid username atau password")

    st.stop()  # Prevent rest of dashboard until logged in

# --- Sidebar / Logout ---
st.sidebar.markdown(f"👤 **Masuk sebagai:** {st.session_state.username}")
st.sidebar.markdown(f"🛡️ **Role:** {st.session_state.role}")
if st.sidebar.button("🚪 Logout"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.set_page_config(page_title="Kegiatan Statistik", page_icon="📋", layout="wide")

# === Fetch activities from Google Sheets ===
if st.session_state.role == "verifier":
    activities = list_all_activities()
else:
    activities = list_activities_for_user(st.session_state.user_id)

# Normalize entries into UI layout shape
form_list = []
for row in activities:
    data = row.get("data") or {}
    raw_meta = row.get("metadata") or {}

    # Safely decode metadata if it's returned as a raw JSON string
    if isinstance(raw_meta, str):
        try:
            meta = json.loads(raw_meta) if raw_meta.strip() else {}
        except Exception:
            meta = {}
    elif isinstance(raw_meta, dict):
        meta = raw_meta
    else:
        meta = {}

    activity_id = (
        row.get("activity_id")
        or row.get("id")
        or data.get("activity_id")
    )

    owner = (
        row.get("user_id")
        or data.get("owner")
        or "unknown"
    )

    status_raw = (
        row.get("status")
        or data.get("status")
        or "draft"
    )
    status = status_raw.replace("_", " ").title()

    title = (
        data.get("halaman_awal", {}).get("judul")
        or data.get("judul")
        or f"Activity {activity_id}"
    )

    last_saved = (
        meta.get("last_saved")
        or data.get("last_saved")
        or row.get("updated_at")
        or "Unknown"
    )

    form_list.append({
        "activity_id": activity_id,
        "owner": owner,
        "status": status,
        "title": title,
        "last_saved": last_saved,
        "raw": row,
    })

# UI helper for status icons
def status_color(status):
    st_lower = status.lower()
    if st_lower == "draft":
        return "⚙️"
    elif st_lower == "submitted":
        return "📤"
    elif st_lower in ["revision requested", "revision_requested"]:
        return "📝"
    elif st_lower == "verified":
        return "✅"
    elif st_lower == "rejected":
        return "❌"
    else:
        return "📋"

st.title("📋 Kegiatan Statistik")

if not form_list:
    st.info("Belum ada Kegiatan Statistik. Klik **Tambah Kegiatan** untuk memulai")
else:
    for idx, item in enumerate(form_list):
        activity_title = item.get("title", "(Tanpa Judul)")
        status = item.get("status", "Draft")
        last_saved = item.get("last_saved", "Unknown")

        with st.expander(f"{status_color(status)} {activity_title}", expanded=False):
            st.write(f"**Status:** {status}")
            st.write(f"**Produsen Data:** {item.get('owner', 'unknown')}")
            st.write(f"**Terakhir Disimpan:** {last_saved}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ Edit", key=f"edit_{idx}"):
                    reset_form_state()
                    st.session_state.edit_activity_id = item.get("activity_id")
                    st.switch_page("pages/1_Form_Page_.py")

            with col2:
                if st.button("🗑️ Hapus", key=f"delete_{idx}"):
                    aid = item.get("activity_id")
                    if not aid:
                        st.error("Tidak dapat menghapus: activity id tidak terdeteksi")
                    else:
                        ok = delete_activity(aid)
                        if ok:
                            st.success("Terhapus")
                        else:
                            st.error("Gagal menghapus kegiatan")
                        st.rerun()

st.markdown("---")

if st.button("➕ Tambah Kegiatan"):
    reset_form_state()
    st.session_state.edit_activity_id = None
    st.switch_page("pages/1_Form_Page_.py")
