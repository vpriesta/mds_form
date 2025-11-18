import streamlit as st
# import json
# from pathlib import Path
from datetime import datetime
import uuid
from supabase_client import (get_activity, upsert_activity, mark_status)

st.set_page_config(page_title="Formulir MS Kegiatan", page_icon="📝", layout="wide")

# =====================================================
# 0️⃣ AUTH CHECK
# =====================================================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("⚠️ Please log in first.")
    st.stop()

if st.sidebar.button("🚪 Logout"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# =====================================================
# 1️⃣ DEFAULT STATE SETUP
# =====================================================
st.session_state.setdefault("form_data", {})
st.session_state.setdefault("current_activity_id", None)
st.session_state.setdefault("username", "unknown_user")
st.session_state.setdefault("role", "user")

# ===================================================== 
# 2️⃣ HELPER LOAD & SAVE SUPABASE 
# ===================================================== 
def load_form(activity_id, username): """Ambil data dari Supabase.""" 
    row = get_activity(activity_id) 
    if not row: 
        return None # wajib cocok owner 
    if row.get("user_id") != username: 
        return None return row.get("data", None) 
        
def save_form(activity_id, username, data): 
    """Simpan draft ke Supabase.""" 
    success, row = upsert_activity(activity_id=activity_id, user_id=username,
                                   payload=data, status="draft",) 
    return success 
    
def submit_form(activity_id): 
    """Submit final ke Supabase.""" 
    return upsert_activity(activity_id=activity_id, user_id=username,
                           payload=st.session_state.form_data,
                           status="submitted", )[0]

# ===================================================== 
# 3️⃣ LOAD STORAGE (EDIT MODE) 
# ===================================================== 
edit_id = st.session_state.get("edit_activity_id") 
if edit_id: 
    supa_data = load_form(edit_id, username) 
    
    if supa_data: 
        st.session_state.current_activity_id = edit_id
        st.session_state.form_data = supa_data.copy() 
    else: 
        st.warning("⚠️ Data di Supabase tidak ditemukan. Membuat draft baru.")
        edit_id = None

# ===================================================== 
# 4️⃣ IF NEW ACTIVITY 
# ===================================================== 
if not edit_id: 
    if not st.session_state.current_activity_id: 
        new_id = str(uuid.uuid4()) 
        st.session_state.current_activity_id = new_id
        st.session_state.form_data = {
            "activity_id": new_id,
            "owner": username,
            "status": "draft",
            "last_saved": "",
            "revision_note": "",
            "revision_requested_at": "",
            "rejection_reason": "",
            "verified_by": "",
            "verifier_comment": "",
        }

# ===================================================== 
# 5️⃣ STATUS DISPLAY 
# ===================================================== 
status = st.session_state.form_data.get("status", "Draft") 
is_submitted = status == "Submitted" 
st.write("### 📄 Activity Form") 
if is_submitted: 
    st.info("This activity has been **submitted** and cannot be edited.") 
else: 
    st.success("You can edit and save this activity before submission.")

# ===================================================== 
# 6️⃣ ALWAYS GUARANTEE FORM STRUCTURE (PAKAI STRUKTUR KAMU) 
# ===================================================== 
sections = [
    "halaman_awal",
    "blok_1_3",
    "variables",
    "blok_4",
    "blok_5",
    "blok_6_8",
    "indicators",] 
for sec in sections: 
    if sec not in st.session_state.form_data: 
        st.session_state.form_data[sec] = [] if sec == "variables" else {} 
# streamlit state untuk input 
st.session_state.setdefault(sec, st.session_state.form_data[sec])

# ===== Page tabs =====
tab1, tab2, tab3 = st.tabs(["📘 MS Kegiatan", "📊 MS Indikator", "📈 MS Variabel"])

# ============================
# 📘 TAB 1: MS KEGIATAN
# ============================
with tab1:
    st.header("📘 MS Kegiatan")

    with st.form("form_halaman_awal"):
        st.subheader("🧾 Halaman Awal")

        # 1. Jenis Statistik
        jenis_options = ["Statistik Dasar", "Statistik Sektoral", "Statistik Khusus"]
        stored_value = st.session_state["halaman_awal"].get("jenis_statistik", "")
        jenis_statistik = st.radio(
            "Jenis Statistik",
            jenis_options,
            index = jenis_options.index(stored_value) if stored_value in jenis_options else None,
            key="jenis_statistik",
            horizontal=True,
            disabled = is_submitted
        )
        st.session_state["halaman_awal"]["jenis_statistik"] = jenis_statistik

        # 2. Rekomendasi
        rekomendasi_options = ["Ya", "Tidak"]
        stored_value = st.session_state["halaman_awal"].get("rekomendasi", "")
        rekomendasi = st.radio(
            "Apakah kegiatan ini merupakan rekomendasi?",
            rekomendasi_options,
            index = rekomendasi_options.index(stored_value) if stored_value in rekomendasi_options else None,
            key="rekomendasi",
            horizontal=True,
            disabled = is_submitted            
        )
        st.session_state["halaman_awal"]["rekomendasi"] = rekomendasi

        if rekomendasi == "Ya":
            rekomendasi_id = st.text_input("Masukkan ID Rekomendasi", value=st.session_state["halaman_awal"].get("rekomendasi_id", ""), placeholder="Wajib diisi jika kegiatan ini adalah rekomendasi", disabled = is_submitted)
        else:
            rekomendasi_id = st.text_input("Masukkan ID Rekomendasi", value="", placeholder="Wajib diisi jika kegiatan ini adalah rekomendasi", disabled = is_submitted)
        st.session_state["halaman_awal"]["rekomendasi_id"] = rekomendasi_id

        # 3. Judul
        judul = st.text_input("Judul Kegiatan", value=st.session_state["halaman_awal"].get("judul", None), key = "judul", disabled = is_submitted)
        st.session_state["halaman_awal"]["judul"] = judul

        # 4. Tahun
        tahun = st.number_input("Tahun", min_value=0, max_value=3000, step=1, value=st.session_state["halaman_awal"].get("tahun", 0), key = "tahun", disabled = is_submitted)
        st.session_state["halaman_awal"]["tahun"] = tahun

        # 5. Cara Pengumpulan
        pengumpulan_options = ["Pencacahan Lengkap", "Survei", "Kompilasi Produk Administrasi", "Cara Lain Sesuai dengan Perkembangan TI"]
        stored_value = st.session_state["halaman_awal"].get("cara_pengumpulan", "")
        cara_pengumpulan = st.selectbox(
            "Cara Pengumpulan Data",
            pengumpulan_options,
            index = pengumpulan_options.index(stored_value) if stored_value in pengumpulan_options else None,
            key="cara_pengumpulan",
            disabled = is_submitted
        )
        st.session_state["halaman_awal"]["cara_pengumpulan"] = cara_pengumpulan

        # 6. Sektor
        sektor_options = ["Pertanian dan Perikanan", "Demografi dan Kependudukan", "Pembangunan", "Proyeksi Ekonomi", "Pendidikan dan Pelatihan",
                "Lingkungan", "Keuangan", "Globalisasi", "Kesehatan", "Industri dan Jasa",
                "Teknologi Informasi dan Komunikasi", "Perdagangan Internasional dan Neraca Perdagangan", "Ketenagakerjaan", "Neraca Nasional",
                "Indikator Ekonomi Bulanan", "Produktivitas", "Harga dan Paritas Daya Beli", 
                "Sektor Publik, Perpajakan, dan Regulasi Pasar", "Perwilayahan dan Perkotaan",
                "Ilmu Pengetahuan dan Hak Paten", "Perlindungan Sosial dan Kesejahteraan", "Transportasi"]
        stored_value = st.session_state["halaman_awal"].get("sektor", "")
        sektor = st.selectbox(
            "Sektor",
            sektor_options,
            index = sektor_options.index(stored_value) if stored_value in sektor_options else None,
            key="sektor",
            disabled = is_submitted
        )
        st.session_state["halaman_awal"]["sektor"] = sektor

        submit_halaman_awal = st.form_submit_button("💾 Simpan Halaman Awal", disabled = is_submitted)

        if submit_halaman_awal: 
            new_entry = {
                "halaman_awal" : {
                    "jenis_statistik": jenis_statistik,
                    "rekomendasi": rekomendasi,
                    "rekomendasi_id": rekomendasi_id,
                    "judul": judul,
                    "tahun": tahun,
                    "cara_pengumpulan": cara_pengumpulan,
                    "sektor": sektor,
                    "status": "Draft",
                    "last_saved": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            } 
            success = save_form(
                activity_id=st.session_state.current_activity_id, 
                username=username, 
                data=new_entry,) 
            
            if success: 
                st.success("✅ Tersimpan di Supabase!") 
            else: 
                st.error("❌ Gagal menyimpan ke Supabase.")
    
        # if submit_halaman_awal:            
        #     new_entry = {
        #         "halaman_awal" : {
        #             "jenis_statistik": jenis_statistik,
        #             "rekomendasi": rekomendasi,
        #             "rekomendasi_id": rekomendasi_id,
        #             "judul": judul,
        #             "tahun": tahun,
        #             "cara_pengumpulan": cara_pengumpulan,
        #             "sektor": sektor,
        #             "status": "Draft",
        #             "last_saved": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #         }
        #     }
            
        #     if data_path.exists():
        #         try:
        #             form_list = json.loads(data_path.read_text())
        #             if not isinstance(form_list, list):
        #                 form_list = []
        #         except json.JSONDecodeError:
        #             form_list = []
        #     else:
        #         form_list = []
            
        #     # Determine whether editing an existing activity
        #     if st.session_state.get("edit_index") is not None:
        #         form_list[st.session_state.edit_index] = new_entry
        #     else:
        #         form_list.append(new_entry)
            
        #     # Save back to file
        #     data_path.write_text(json.dumps(form_list, indent=2, ensure_ascii=False, default=str))
            
        #     # st.success("✅ Semua progress disimpan ke file JSON!")
        #     # st.session_state["submit_halaman_awal"] = new_entry
        #     st.success("Halaman Awal disimpan!")

    # st.divider()

    if "blok_1_3" not in st.session_state:
            st.session_state["blok_1_3"] = {}
    
    with st.expander("📘 BLOK 1 – PENYELENGGARA", expanded=False):
    
        # You can later pull these values dynamically from a config file or API if needed
        instansi_default = {
            "i_instansi_penyelenggara": "Kementerian PPN/Bappenas",
            "i_alamat": "Jalan Taman Suropati Nomor 2, Jakarta 10310",
            "i_telepon": "(+6221) 31936207, 3905650",
            "i_faksimile": "(+6221) 3145374",
            "i_email": "-"
        }
        
        # 1.1 Instansi
        st.text_input(
            "1.1 Instansi Penyelenggara",
            value=instansi_default["i_instansi_penyelenggara"],
            disabled=True
        )
        
        # 1.2 Alamat Lengkap (sub-questions)
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Alamat", value=instansi_default["i_alamat"], disabled=True)
            st.text_input("Telepon", value=instansi_default["i_telepon"], disabled=True)
        with col2:
            st.text_input("Faksimile", value=instansi_default["i_faksimile"], disabled=True)
            st.text_input("Email", value=instansi_default["i_email"], disabled=True)

    # st.divider()

    with st.expander("📘 BLOK 2 – PENANGGUNG JAWAB", expanded=False):
        
        st.markdown("#### 2.1 Unit Eselon Penanggung Jawab", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            ii_unit_eselon1 = st.text_input("Eselon I", value=st.session_state["blok_1_3"].get("ii_unit_eselon1", ""), key="ii_unit_eselon1", disabled = is_submitted)
            st.session_state["blok_1_3"]["ii_unit_eselon1"] = ii_unit_eselon1
        with col2:
            ii_unit_eselon2 = st.text_input("Eselon II", value=st.session_state["blok_1_3"].get("ii_unit_eselon2", ""), key="ii_unit_eselon2", disabled = is_submitted)
            st.session_state["blok_1_3"]["ii_unit_eselon2"] = ii_unit_eselon2
    
        st.markdown("#### 2.2 Penanggung Jawab Teknis", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            ii_pj_nama = st.text_input("Nama", value=st.session_state["blok_1_3"].get("ii_pj_nama", ""), key="ii_pj_nama", disabled = is_submitted)
            st.session_state["blok_1_3"]["ii_pj_nama"] = ii_pj_nama
            ii_pj_jabatan = st.text_input("Jabatan", value=st.session_state["blok_1_3"].get("ii_pj_jabatan", ""), key="ii_pj_jabatan", disabled = is_submitted)
            st.session_state["blok_1_3"]["ii_pj_jabatan"] = ii_pj_jabatan
            ii_pj_alamat = st.text_area("Alamat", value=st.session_state["blok_1_3"].get("ii_pj_alamat", ""), key="ii_pj_alamat", disabled = is_submitted)
            st.session_state["blok_1_3"]["ii_pj_alamat"] = ii_pj_alamat
        with col2:
            ii_pj_telepon = st.text_input("Telepon", value=st.session_state["blok_1_3"].get("ii_pj_telepon", ""), key="ii_pj_telepon", disabled = is_submitted)
            st.session_state["blok_1_3"]["ii_pj_telepon"] = ii_pj_telepon
            ii_pj_email = st.text_input("Email", value=st.session_state["blok_1_3"].get("ii_pj_email", ""), key="ii_pj_email", disabled = is_submitted)
            st.session_state["blok_1_3"]["ii_pj_email"] = ii_pj_email
            ii_pj_faksimile = st.text_input("Faksimile", value=st.session_state["blok_1_3"].get("ii_pj_faksimile", ""), key="ii_pj_faksimile", disabled = is_submitted)
            st.session_state["blok_1_3"]["ii_pj_faksimile"] = ii_pj_faksimile

    # st.divider()
    
    with st.expander("📘 BLOK 3 – PERENCANAAN DAN PERSIAPAN", expanded=False):
            
        # --- 3.1 Background ---
        st.markdown("#### 3.1 Latar Belakang Kegiatan", unsafe_allow_html=True)
        iii_latar_belakang_kegiatan = st.text_area("Tuliskan latar belakang kegiatan", value=st.session_state["blok_1_3"].get("iii_latar_belakang_kegiatan", ""), key="iii_latar_belakang_kegiatan", disabled = is_submitted)
        st.session_state["blok_1_3"]["iii_latar_belakang_kegiatan"] = iii_latar_belakang_kegiatan
    
        # --- 3.2 Objective ---
        st.markdown("#### 3.2 Tujuan Kegiatan", unsafe_allow_html=True)
        iii_tujuan_kegiatan = st.text_area("Tuliskan tujuan kegiatan", value=st.session_state["blok_1_3"].get("iii_tujuan_kegiatan", ""), key="iii_tujuan_kegiatan", disabled = is_submitted)
        st.session_state["blok_1_3"]["iii_tujuan_kegiatan"] = iii_tujuan_kegiatan
    
        # --- 3.3 Schedule ---
        st.markdown("#### 3.3 Rencana Jadwal Kegiatan", unsafe_allow_html=True)
        st.caption("Isi tanggal mulai dan selesai untuk setiap tahap kegiatan.")
    
        # with st.form("A. Perencanaan"):
        def schedule_row(label, start_key, end_key):
            col1, col_, col2 = st.columns([0.45, 0.1, 0.45])
            with col1:
                st.session_state["blok_1_3"][start_key] = st.date_input(
                    label,
                    value=st.session_state["blok_1_3"].get(start_key, None),
                    key=start_key,
                    disabled = is_submitted
                )
            with col_:
                st.text_input("", value="hingga", disabled=True, key=f"hingga_{label}")
            with col2:
                st.session_state["blok_1_3"][end_key] = st.date_input(
                    "",
                    value=st.session_state["blok_1_3"].get(end_key, None),
                    key=end_key,disabled = is_submitted
                )

        def save_date(start_key, end_key):
            start = st.session_state["blok_1_3"].get(start_key)
            start_date = start.strftime("%d %B %Y") if start else ""
            end = st.session_state["blok_1_3"].get(end_key)
            end_date = end.strftime("%d %B %Y") if end else ""
            date_range = start_date + str(" hingga ") + end_date
            return date_range
    
        st.markdown("##### A. Perencanaan", unsafe_allow_html=True)
        schedule_row("1. Perencanaan Kegiatan", "iii_jadwal_perencanaan_kegiatan_start", "iii_jadwal_perencanaan_kegiatan_end")
        st.session_state["blok_1_3"]["iii_jadwal_perencanaan_kegiatan"] = save_date("iii_jadwal_perencanaan_kegiatan_start", "iii_jadwal_perencanaan_kegiatan_end")
        schedule_row("2. Desain", "iii_jadwal_desain_start", "iii_jadwal_desain_end")
        st.session_state["blok_1_3"]["iii_jadwal_desain"] = save_date("iii_jadwal_desain_start", "iii_jadwal_desain_end")
    
        st.markdown("##### B. Pengumpulan", unsafe_allow_html=True)
        schedule_row("3. Pengumpulan Data", "iii_jadwal_pengumpulan_data_start", "iii_jadwal_pengumpulan_data_end")
        st.session_state["blok_1_3"]["iii_jadwal_pengumpulan_data"] = save_date("iii_jadwal_pengumpulan_data_start", "iii_jadwal_pengumpulan_data_end")
        
    
        st.markdown("##### C. Pemeriksaan", unsafe_allow_html=True)
        schedule_row("4. Pengolahan Data", "iii_jadwal_pengolahan_data_start", "iii_jadwal_pengolahan_data_end")
        st.session_state["blok_1_3"]["iii_jadwal_pengolahan_data"] = save_date("iii_jadwal_pengolahan_data_start", "iii_jadwal_pengolahan_data_end")
    
        st.markdown("##### D. Penyebarluasan", unsafe_allow_html=True)
        schedule_row("5. Analisis", "iii_jadwal_analisis_start", "iii_jadwal_analisis_end")
        st.session_state["blok_1_3"]["iii_jadwal_analisis"] = save_date("iii_jadwal_analisis_start", "iii_jadwal_analisis_end")
        schedule_row("6. Diseminasi Hasil", "iii_jadwal_diseminasi_hasil_start", "iii_jadwal_diseminasi_hasil_end")
        st.session_state["blok_1_3"]["iii_jadwal_diseminasi_hasil"] = save_date("iii_jadwal_diseminasi_hasil_start", "iii_jadwal_diseminasi_hasil_end")
        schedule_row("7. Evaluasi", "iii_jadwal_evaluasi_start", "iii_jadwal_evaluasi_end")
        st.session_state["blok_1_3"]["iii_jadwal_evaluasi"] = save_date("iii_jadwal_evaluasi_start", "iii_jadwal_evaluasi_end")
        
        st.markdown("#### 3.4 Variabel")
        st.caption("Tambahkan satu atau lebih variabel berikut dengan informasi lengkap.")
        
        # ✅ Ensure variables list exists but don't reset it every rerun
        if "variables" not in st.session_state or not isinstance(st.session_state.variables, list):
            st.session_state.variables = []
        
        # --- Add new variable ---
        def add_variable():
            st.session_state.variables.append({
                "name": "",
                "concept": "",
                "definition": "",
                "reference": ""
            })
        
        st.button("➕ Tambah Variabel", on_click=add_variable, disabled=is_submitted)
        
        remove_var_index = None
        
        # --- Display existing variables ---
        for i, var in enumerate(st.session_state.variables):
            st.markdown(f"**Variabel {i+1}**")
            with st.container():
                c1, c2 = st.columns(2)
                with c1:
                    st.session_state.variables[i]["name"] = st.text_input(
                        "Nama Variabel", value=var.get("name", ""), key=f"var_name_{i}", disabled=is_submitted
                    )
                    st.session_state.variables[i]["concept"] = st.text_input(
                        "Konsep", value=var.get("concept", ""), key=f"var_concept_{i}", disabled=is_submitted
                    )
                    st.session_state.variables[i]["reference"] = st.text_input(
                        "Referensi Waktu", value=var.get("reference", ""), key=f"var_reference_{i}", disabled=is_submitted
                    )
                with c2:
                    st.session_state.variables[i]["definition"] = st.text_area(
                        "Definisi", value=var.get("definition", ""), key=f"var_definition_{i}", disabled=is_submitted
                    )
        
                if st.button(f"🗑️ Hapus Variabel {i+1}", key=f"remove_var_{i}", disabled=is_submitted):
                    remove_var_index = i
        
        # --- Remove variable if requested ---
        if remove_var_index is not None:
            st.session_state.variables.pop(remove_var_index)
            st.rerun()
        
        # Optional: Submit all variables
    #     if st.button("💾 Simpan Semua Variabel"):
    #         st.write("Variabel tersimpan:")
    #         st.json(st.session_state.variables)

    # # ===== Save form button =====
    #     submit_1_3 = st.button("💾 Simpan Blok 1 - 3")

    #     if submit_1_3:            
    #         new_entry = {
    #             "i_instansi_penyelenggara": instansi_default["i_instansi_penyelenggara"],
    #             "i_alamat": instansi_default["i_alamat"],
    #             "i_telepon": instansi_default["i_telepon"],
    #             "i_faksimile": instansi_default["i_faksimile"],
    #             "i_email": instansi_default["i_email"],
    #             "ii_unit_eselon1": ii_unit_eselon1,
    #             "ii_unit_eselon2": ii_unit_eselon2,
    #             "ii_pj_nama": ii_pj_nama,
    #             "ii_pj_jabatan": ii_pj_jabatan,
    #             "ii_pj_alamat": ii_pj_alamat,
    #             "ii_pj_telepon": ii_pj_telepon,
    #             "ii_pj_email": ii_pj_email,
    #             "ii_pj_faksimile": ii_pj_faksimile,
    #             "iii_latar_belakang_kegiatan": iii_latar_belakang_kegiatan,
    #             "iii_tujuan_kegiatan": iii_tujuan_kegiatan,
    #             "iii_jadwal_perencanaan_kegiatan": save_date("iii_jadwal_perencanaan_kegiatan_start", "iii_jadwal_perencanaan_kegiatan_end"),
    #             "iii_jadwal_desain" : save_date("iii_jadwal_desain_start", "iii_jadwal_desain_end"),
    #             "iii_jadwal_pengumpulan_data" : save_date("iii_jadwal_pengumpulan_data_start", "iii_jadwal_pengumpulan_data_end"),
    #             "iii_jadwal_pengolahan_data" : save_date("iii_jadwal_pengolahan_data_start", "iii_jadwal_pengolahan_data_end"),
    #             "iii_jadwal_analisis" : save_date("iii_jadwal_analisis_start", "iii_jadwal_analisis_end"),
    #             "iii_jadwal_diseminasi_hasil" : save_date("iii_jadwal_diseminasi_hasil_start", "iii_jadwal_diseminasi_hasil_end"),
    #             "iii_jadwal_evaluasi" : save_date("iii_jadwal_evaluasi_start", "iii_jadwal_evaluasi_end"),
    #             "status": "Draft",
    #             "last_saved": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #         }
    #         st.session_state["blok_1_3"] = new_entry
    #         st.success("Blok 1 - 3 disimpan!")

    # st.divider()
    
    if "blok_4" not in st.session_state:
            st.session_state["blok_4"] = {}
    with st.expander("📘 BLOK 4 – DESAIN KEGIATAN", expanded=False):

        # Q4.1 & Q4.2
        frekuensi_options = ["Hanya Sekali", "Harian", "Mingguan", "Bulanan", "Triwulanan", "Empat Bulanan", "Semesteran", "Tahunan", "Lebih dari Dua Tahunan"]
        stored_value = st.session_state["blok_4"].get("iv_frekuensi_penyelenggaraan", "")
        st.markdown("##### 4.1 - 4.2 Frekuensi Penyelenggaraan", unsafe_allow_html=True)
        iv_frekuensi_penyelenggaraan = st.radio(
            "4.2 Frekuensi Penyelenggaraan",
            frekuensi_options, 
            index = frekuensi_options.index(stored_value) if stored_value in frekuensi_options else None,
            key="iv_frekuensi_penyelenggaraan",
            label_visibility = "collapsed",
            horizontal = True,
            disabled = is_submitted
        )

        if iv_frekuensi_penyelenggaraan == "Hanya Sekali":
            iv_kegiatan_ini_dilakukan = "Hanya Sekali"
        else:
            iv_kegiatan_ini_dilakukan = "Berulang"

        st.session_state["blok_4"]["iv_frekuensi_penyelenggaraan"] = iv_frekuensi_penyelenggaraan
        st.session_state["blok_4"]["iv_kegiatan_ini_dilakukan"] = iv_kegiatan_ini_dilakukan

        # Q4.3
        pengumpulan_options = ["Longitudinal Panel", "Longitudinal Cross Sectional", "Cross Sectional"]
        stored_value = st.session_state["blok_4"].get("iv_tipe_pengumpulan_data", "")
        st.markdown("##### 4.3 Tipe Pengumpulan Data", unsafe_allow_html=True)
        iv_tipe_pengumpulan_data = st.radio(
            "4.3 Tipe Pengumpulan Data",
            pengumpulan_options,
            index = pengumpulan_options.index(stored_value) if stored_value in pengumpulan_options else None,
            key="iv_tipe_pengumpulan_data",
            label_visibility = "collapsed",
            horizontal=True,
            disabled = is_submitted
        )
        st.session_state["blok_4"]["iv_tipe_pengumpulan_data"] = iv_tipe_pengumpulan_data

        # Q4.4 & Q4.5
        st.markdown("##### 4.4 - 4.5 Cakupan Wilayah Pengumpulan Data", unsafe_allow_html=True)
        wilayah_options = ['SELURUH WILAYAH INDONESIA', 'ACEH', 'SUMATERA UTARA', 'SUMATERA BARAT', 'RIAU', 'JAMBI', 'SUMATERA SELATAN', 'BENGKULU',
                           'LAMPUNG','KEP. BANGKA BELITUNG', 'KEP. RIAU', 'DKI JAKARTA', 'JAWA BARAT', 'JAWA TENGAH', 'DI YOGYAKARTA', 'JAWA TIMUR',
                           'BANTEN', 'BALI', 'NUSA TENGGARA BARAT', 'NUSA TENGGARA TIMUR', 'KALIMANTAN BARAT', 'KALIMANTAN TENGAH',
                           'KALIMANTAN SELATAN', 'KALIMANTAN TIMUR', 'KALIMANTAN UTARA', 'SULAWESI UTARA', 'SULAWESI TENGAH', 'SULAWESI SELATAN',
                           'SULAWESI TENGGARA', 'GORONTALO', 'SULAWESI BARAT', 'MALUKU', 'MALUKU UTARA', 'PAPUA', 'PAPUA BARAT', 'PAPUA SELATAN',
                           'PAPUA TENGAH', 'PAPUA PEGUNUNGAN', 'PAPUA BARAT DAYA']
        stored_value = st.session_state["blok_4"].get("iv_sebagian_cakupan_wilayah_pengumpulan_data", "")
        iv_sebagian_cakupan_wilayah_pengumpulan_data = st.multiselect(
            "4.5 Wilayah Kegiatan",
            wilayah_options, 
            default = stored_value if isinstance(stored_value, list) else [],
            label_visibility = "collapsed",
            key="iv_sebagian_cakupan_wilayah_pengumpulan_data",
            disabled = is_submitted
        )

        if iv_sebagian_cakupan_wilayah_pengumpulan_data == "SELURUH WILAYAH INDONESIA":
            iv_cakupan_wilayah_pengumpulan_data = "Seluruh Wilayah Indonesia"
        else:
            iv_cakupan_wilayah_pengumpulan_data = "Sebagian Wilayah Indonesia"           
        
        st.session_state["blok_4"]["iv_cakupan_wilayah_pengumpulan_data"] = iv_cakupan_wilayah_pengumpulan_data
        st.session_state["blok_4"]["iv_sebagian_cakupan_wilayah_pengumpulan_data"] = iv_sebagian_cakupan_wilayah_pengumpulan_data

        # Q4.6
        metode_options = ["Wawancara", "Mengisi Kuesioner Sendiri", "Pengamatan", "Pengumpulan Data Sekunder", "Lainnya"]
        stored_value = st.session_state["blok_4"].get("metode_utama", "")
        if isinstance(stored_value, list):
            valid_default = [m for m in stored_value if m in metode_options]
        else:
            valid_default = []
        st.markdown("##### 4.6 Metode Pengumpulan Data", unsafe_allow_html=True)
        metode_utama = st.multiselect(
            "4.6 Metode Pengumpulan Data",
            metode_options,
            default = stored_value if isinstance(stored_value, list) else [],
            label_visibility = "collapsed",
            key="metode_utama",
            disabled = is_submitted
        )
        st.session_state["blok_4"]["metode_utama"] = metode_utama

        metode_lain = st.text_input("Lainnya: Sebutkan metode pengumpulan lain", value=st.session_state["blok_4"].get("metode_lain", ""), key="metode_lain", placeholder = "Wajib diisi jika memilih opsi 'Lainnya'", disabled = is_submitted)
        st.session_state["blok_4"]["metode_lain"] = metode_lain
        iv_metode_pengumpulan_data = metode_utama.copy()
        if "Lainnya" in iv_metode_pengumpulan_data:
            if metode_lain.strip():  # only replace if user actually typed something
                iv_metode_pengumpulan_data = [
                    metode_lain if item == "Lainnya" else item
                    for item in iv_metode_pengumpulan_data
                ]
            else:
                iv_metode_pengumpulan_data.remove("Lainnya")

        st.session_state["blok_4"]["iv_metode_pengumpulan_data"] = iv_metode_pengumpulan_data
        # iv_metode_pengumpulan_data = metode_utama.append(f"Lainnya: {metode_lain}")

        # Q4.7
        sarana_options = ["Paper-assisted Personal Interviewing (PAPI)", "Computer-assisted Personal Interviewing (CAPI)", "Computer-assisted Telephones Interviewing (CATI)", "Computer Aided Web Interviewing (CAWI)", "Mail", "Lainnya"]
        stored_value = st.session_state["blok_4"].get("sarana_utama", "")
        st.markdown("##### 4.7 Sarana Pengumpulan Data", unsafe_allow_html=True)
        sarana_utama = st.multiselect(
            "4.7 Sarana Pengumpulan Data",
            sarana_options,
            default = stored_value if isinstance(stored_value, list) else [],
            label_visibility = "collapsed",
            key="sarana_utama",
            disabled = is_submitted
        )
        st.session_state["blok_4"]["sarana_utama"] = sarana_utama

        sarana_lain = st.text_input("Lainnya: Sebutkan sarana pengumpulan lain", value=st.session_state["blok_4"].get("sarana_lain", ""), key="sarana_lain", placeholder = "Wajib diisi jika memilih opsi 'Lainnya'", disabled = is_submitted)
        st.session_state["blok_4"]["sarana_lain"] = sarana_lain
        iv_sarana_pengumpulan_data = sarana_utama.copy()
        if "Lainnya" in iv_sarana_pengumpulan_data:
            if sarana_lain.strip():  # only replace if user actually typed something
                iv_sarana_pengumpulan_data = [
                    sarana_lain if item == "Lainnya" else item
                    for item in iv_sarana_pengumpulan_data
                ]
            else:
                iv_sarana_pengumpulan_data.remove("Lainnya")

        st.session_state["blok_4"]["iv_sarana_pengumpulan_data"] = iv_sarana_pengumpulan_data

        # Q4.8
        unit_options = ["Individu", "Rumah Tangga", "Usaha/Perusahaan", "Lainnya"]
        stored_value = st.session_state["blok_4"].get("unit_utama", "")
        st.markdown("##### 4.8 Unit Pengumpulan Data", unsafe_allow_html=True)
        unit_utama = st.multiselect(
            "4.8 Unit Pengumpulan Data",
            unit_options,
            default = stored_value if isinstance(stored_value, list) else [],
            label_visibility = "collapsed",
            key="unit_utama",
            disabled = is_submitted
        )
        st.session_state["blok_4"]["unit_utama"] = unit_utama

        unit_lain = st.text_input("Lainnya: Sebutkan unit pengumpulan lain", value=st.session_state["blok_4"].get("unit_lain", ""), key="unit_lain", placeholder = "Wajib diisi jika memilih opsi 'Lainnya'", disabled = is_submitted)
        st.session_state["blok_4"]["unit_lain"] = unit_lain
        iv_unit_pengumpulan_data = unit_utama.copy()
        if "Lainnya" in iv_unit_pengumpulan_data:
            if unit_lain.strip():  # only replace if user actually typed something
                iv_unit_pengumpulan_data = [
                    unit_lain if item == "Lainnya" else item
                    for item in iv_unit_pengumpulan_data
                ]
            else:
                iv_unit_pengumpulan_data.remove("Lainnya")

        st.session_state["blok_4"]["iv_unit_pengumpulan_data"] = iv_unit_pengumpulan_data

        # submit_4 = st.button("💾 Simpan Blok 4")
    
        # if submit_4:            
        #     new_entry = {
        #         "iv_kegiatan_ini_dilakukan": iv_kegiatan_ini_dilakukan,
        #         "iv_frekuensi_penyelenggaraan": iv_frekuensi_penyelenggaraan,
        #         "iv_tipe_pengumpulan_data": iv_tipe_pengumpulan_data,
        #         "iv_cakupan_wilayah_pengumpulan_data": iv_cakupan_wilayah_pengumpulan_data,
        #         "iv_sebagian_cakupan_wilayah_pengumpulan_data": iv_sebagian_cakupan_wilayah_pengumpulan_data,
        #         "metode_utama": metode_utama,
        #         "iv_metode_pengumpulan_data": iv_metode_pengumpulan_data,
        #         "sarana_utama": sarana_utama,
        #         "iv_sarana_pengumpulan_data": iv_sarana_pengumpulan_data,
        #         "unit_utama": unit_utama,
        #         "iv_unit_pengumpulan_data": iv_unit_pengumpulan_data,
        #         "status": "Draft",
        #         "last_saved": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #     }
        #     st.session_state["blok_4"] = new_entry
        #     st.success("Blok 4 disimpan!")

    # st.divider()

    if "blok5" not in st.session_state:
        st.session_state["blok5"] = {}
    
    # --- CONDITIONAL BLOCK 5 ---
    if st.session_state["halaman_awal"].get("cara_pengumpulan") == "Survei":
        with st.expander("📘 BLOK 5 - DESAIN SAMPEL", expanded=False):        
    
            # 5.1 Jenis Rancangan Sampel
            rancangan_options = ["Single Stage atau Phase Dasar", "Multi Stage atau Phase"]
            stored_value = st.session_state["blok_5"].get("v_jenis_rancangan_sampel", "")
            st.markdown("##### 5.1 Jenis Rancangan Sampel")
            v_jenis_rancangan_sampel = st.radio(
                "5.1 Jenis Rancangan Sampel",
                rancangan_options,
                index = rancangan_options.index(stored_value) if stored_value in rancangan_options else None,
                key="v_jenis_rancangan_sampel",
                label_visibility = "collapsed",
                horizontal=True,
                disabled = is_submitted
            )
            st.session_state["blok_5"]["v_jenis_rancangan_sampel"] = v_jenis_rancangan_sampel
    
            # 5.2 Metode Pemilihan Sampel Tahap Terakhir
            stored_sampel_prob = st.session_state["blok_5"].get("sampel_prob", "")
            stored_sampel_nonprob = st.session_state["blok_5"].get("sampel_nonprob", "")
            st.markdown("##### 5.2 Metode Pemilihan Sampel Tahap Terakhir")
            st.markdown("Pilih salah satu")
            sampel_prob = st.checkbox("Sampel Probabilitas", value=st.session_state["blok_5"].get("sampel_prob", ""), disabled = is_submitted)
            sampel_nonprob = st.checkbox("Sampel Nonprobabilitas", value=st.session_state["blok_5"].get("sampel_nonprob", ""), disabled = is_submitted)
            st.session_state["blok_5"]["sampel_prob"] = sampel_prob
            st.session_state["blok_5"]["sampel_nonprob"] = sampel_nonprob
    
            # 5.2 Metode Pemilihan Sampel Tahap Terakhir
            v_kerangka_sampel_tahap_akhir = ""
            v_metode_yang_digunakan = ""
            v_fraksi_sampel_keseluruhan = ""
            v_nilai_perkiraan_sampling_error_variabel_utama = ""
            if sampel_prob:
                st.session_state["blok_5"]["pemilihan_sampel"] = "Sampel Probabilitas"
                prob_options = ["Simple Random Sampling", "Systematic Random Sampling", "Stratified Random Sampling", "Cluster Sampling",
                               "Probability Proportional to Size Sampling"] 
                stored_value = st.session_state["blok_5"].get("v_metode_yang_digunakan", "")
                st.markdown("##### 5.3 Metode yang Digunakan")
                v_metode_yang_digunakan = st.radio(
                    "5.3 Metode yang Digunakan",
                    prob_options,
                    index = prob_options.index(stored_value) if stored_value in prob_options else None,
                    key="v_metode_yang_digunakan",
                    label_visibility = "collapsed",
                    horizontal=True,
                    disabled = is_submitted
                )
                st.session_state["blok_5"]["v_metode_yang_digunakan"] = v_metode_yang_digunakan
    
                kerangka_options = ["List Frame", "Area Frame"] 
                stored_value = st.session_state["blok_5"].get("v_kerangka_sampel_tahap_akhir", "")
                st.markdown("##### 5.4 Kerangka Sampel Tahap Terakhir")
                v_kerangka_sampel_tahap_akhir = st.radio(
                    "5.3 Metode yang Digunakan",
                    kerangka_options,
                    index = kerangka_options.index(stored_value) if stored_value in kerangka_options else None,
                    key="v_kerangka_sampel_tahap_akhir",
                    label_visibility = "collapsed",
                    horizontal=True,
                    disabled = is_submitted
                )
                st.session_state["blok_5"]["v_kerangka_sampel_tahap_akhir"] = v_kerangka_sampel_tahap_akhir
    
                st.markdown("#### 5.5 Fraksi Sampel Keseluruhan", unsafe_allow_html=True)
                v_fraksi_sampel_keseluruhan = st.text_area("Tuliskan latar belakang kegiatan",
                                                           value=st.session_state["blok_5"].get("v_fraksi_sampel_keseluruhan", ""),
                                                           label_visibility = "collapsed",
                                                           placeholder = "Tuliskan fraksi sampel keseluruhan",
                                                           key="v_fraksi_sampel_keseluruhan",
                                                          disabled = is_submitted)
                st.session_state["blok_5"]["v_fraksi_sampel_keseluruhan"] = v_fraksi_sampel_keseluruhan
    
                st.markdown("#### 5.6 Nilai Perkiraan Sampling Error Variabel Utama", unsafe_allow_html=True)
                v_nilai_perkiraan_sampling_error_variabel_utama = st.text_area("5.6 Nilai Perkiraan Sampling Error Variabel Utama", 
                                                                        value=st.session_state["blok_5"].get("v_nilai_perkiraan_sampling_error_variabel_utama", ""),
                                                                        label_visibility = "collapsed",
                                                                        placeholder = "Tuliskan nilai perkiraan sampling error variabel utama",
                                                                        key="v_nilai_perkiraan_sampling_error_variabel_utama",
                                                                              disabled = is_submitted)
                st.session_state["blok_5"]["v_nilai_perkiraan_sampling_error_variabel_utama"] = v_nilai_perkiraan_sampling_error_variabel_utama
    
            if sampel_nonprob:
                st.session_state["blok_5"]["pemilihan_sampel"] = "Sampel Nonprobabilitas"
                nonprob_options = ["Quota Sampling", "Accidental Sampling", "Purposive Sampling", "Snowball Sampling", "Saturation Sampling"] 
                stored_value = st.session_state["blok_5"].get("v_metode_yang_digunakan", "")
                st.markdown("##### 5.3 Metode yang Digunakan")
                v_metode_yang_digunakan = st.radio(
                    "5.3 Metode yang Digunakan",
                    nonprob_options,
                    index = nonprob_options.index(stored_value) if stored_value in nonprob_options else None,
                    key="v_metode_yang_digunakan",
                    label_visibility = "collapsed",
                    horizontal=True,
                    disabled = is_submitted
                )
                st.session_state["blok_5"]["v_metode_yang_digunakan"] = v_metode_yang_digunakan
    
            st.markdown("#### 5.7 Unit Sampel", unsafe_allow_html=True)
            v_unit_sampel = st.text_area("5.7 Unit Sampel", value=st.session_state["blok_5"].get("v_unit_sampel", ""), label_visibility = "collapsed",
                                         placeholder = "Tuliskan unit sampel", key="v_unit_sampel", disabled = is_submitted)
            st.session_state["blok_5"]["v_unit_sampel"] = v_unit_sampel
    
            st.markdown("#### 5.8 Unit Observasi", unsafe_allow_html=True)
            v_unit_observasi = st.text_area("5.8 Unit Observasi", value=st.session_state["blok_5"].get("v_unit_observasi", ""), label_visibility = "collapsed",
                                         placeholder = "Tuliskan unit observasi", key="v_unit_observasi", disabled = is_submitted)
            st.session_state["blok_5"]["v_unit_observasi"] = v_unit_observasi
    
                
        
            # Save Block 5
            # if st.button("💾 Simpan Blok 5"):
            #     st.session_state["blok_5"] = {
            #         "v_jenis_rancangan_sampel": v_jenis_rancangan_sampel,
            #         "sampel_prob": sampel_prob,
            #         "sampel_nonprob": sampel_nonprob,
            #         "v_metode_pemilihan_sampel_tahap_terakhir": sampel_prob or sampel_nonprob,
            #         "v_kerangka_sampel_tahap_akhir": v_kerangka_sampel_tahap_akhir,
            #         "v_metode_yang_digunakan": v_metode_yang_digunakan,
            #         "v_fraksi_sampel_keseluruhan": v_fraksi_sampel_keseluruhan,
            #         "v_nilai_perkiraan_sampling_error_variabel_utama": v_nilai_perkiraan_sampling_error_variabel_utama,
            #         "v_unit_sampel": v_unit_sampel,
            #         "v_unit_observasi": v_unit_observasi,
            #         "last_saved": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            #     }
            #     st.success("Blok 5 disimpan!")
    else:
        st.info("➡️ Karena cara pengumpulan bukan 'Survei', BLOK 5 dilewati. Silakan lanjut ke BLOK 6.")

    # st.divider()

    if "blok_6_8" not in st.session_state:
            st.session_state["blok_6_8"] = {}
    
    with st.expander("📘 BLOK 6 – PENGUMPULAN DATA", expanded=False):

        col1, col2 = st.columns(2)

        #Q6.1
        with col1:
            stored_value = st.session_state["blok_6_8"].get("vi_apakah_melakukan_uji_coba", "")
            vi_apakah_melakukan_uji_coba = st.checkbox("Melakukan Uji Coba (Pilot Survey)", value=st.session_state["blok_6_8"].get("vi_apakah_melakukan_uji_coba", ""), disabled = is_submitted)
            st.session_state["blok_6_8"]["vi_apakah_melakukan_uji_coba"] = vi_apakah_melakukan_uji_coba

        #Q6.3
        with col2:

            stored_value = st.session_state["blok_6_8"].get("vi_apakah_melakukan_penyesuaian_nonrespon", "")
            vi_apakah_melakukan_penyesuaian_nonrespon = st.checkbox("Melakukan Penyesuaian Nonrespon",
                                                                    value=st.session_state["blok_6_8"].get("vi_apakah_melakukan_penyesuaian_nonrespon", ""), disabled = is_submitted)
            st.session_state["blok_6_8"]["vi_apakah_melakukan_penyesuaian_nonrespon"] = vi_apakah_melakukan_penyesuaian_nonrespon
            
        
        #Q6.2
        qc_options = ["Kunjungan Kembali", "Supervisi", "Task Force", "Lainnya"]
        stored_value = st.session_state["blok_6_8"].get("qc_utama", "")
        st.markdown("##### 6.2 Metode Pemeriksaan Kualitas Pengumpulan Data", unsafe_allow_html=True)
        qc_utama = st.multiselect(
            "6.2 Metode Pemeriksaan Kualitas Pengumpulan Data",
            qc_options,
            default = stored_value if isinstance(stored_value, list) else [],
            label_visibility = "collapsed",
            key="vi_metode_pemeriksaan_kualitas_pengumpulan_data",
            disabled = is_submitted
        )
        st.session_state["blok_6_8"]["qc_utama"] = qc_utama

        qc_lain = st.text_input("Lainnya: Sebutkan metode pemeriksaan kualitas lain", value=st.session_state["blok_6_8"].get("qc_lain", ""), key="qc_lain", placeholder = "Wajib diisi jika memilih opsi 'Lainnya'", disabled = is_submitted)
        st.session_state["blok_6_8"]["qc_lain"] = qc_lain
        vi_metode_pemeriksaan_kualitas_pengumpulan_data = qc_utama.copy()
        if "Lainnya" in vi_metode_pemeriksaan_kualitas_pengumpulan_data:
            if qc_lain.strip():  # only replace if user actually typed something
                vi_metode_pemeriksaan_kualitas_pengumpulan_data = [
                    qc_lain if item == "Lainnya" else item
                    for item in vi_metode_pemeriksaan_kualitas_pengumpulan_data
                ]
            else:
                vi_metode_pemeriksaan_kualitas_pengumpulan_data.remove("Lainnya")

        st.session_state["blok_6_8"]["vi_metode_pemeriksaan_kualitas_pengumpulan_data"] = vi_metode_pemeriksaan_kualitas_pengumpulan_data

        interview_based = ["Paper-assisted Personal Interviewing (PAPI)", "Computer-assisted Personal Interviewing (CAPI)",
                           "Computer-assisted Telephones Interviewing (CATI)"]
        
        # Check if user selected one of the interview-based methods
        vi_petugas_pengumpulan_data = ""
        vi_persyaratan_pendidikan_terendah_petugas_pengumpulan_data = ""
        vi_jumlah_petugas_supervisor = 0
        vi_jumlah_petugas_enumerator = 0
        if any(opt in st.session_state["blok_4"].get("sarana_utama") for opt in interview_based):
            #Q6.4
            st.markdown("##### 6.4 Petugas Pengumpulan Data")
            petugas_options = ["Staf Instansi Penyelenggara", "Mitra Atau Tenaga Kontrak", "Staf Instansi Penyelenggara & Mitra Atau Tenaga Kontrak"] 
            stored_value = st.session_state["blok_6_8"].get("vi_petugas_pengumpulan_data", "")
            vi_petugas_pengumpulan_data = st.radio(
                "6.4 Petugas Pengumpulan Data",
                petugas_options,
                index = petugas_options.index(stored_value) if stored_value in petugas_options else None,
                key="vi_petugas_pengumpulan_data",
                label_visibility = "collapsed",
                horizontal=True,
                disabled = is_submitted
            )
            st.session_state["blok_6_8"]["vi_petugas_pengumpulan_data"] = vi_petugas_pengumpulan_data

            #Q6.5
            st.markdown("##### 6.5 Persyaratan Pendidikan Terendah Petugas Pengumpulan Data")
            petugas_options = ["Kurang Dari Atau Sama Dengan SMP", "SMA Atau SMK", "Diploma I/II/III", "Diploma IV atau S1/S2/S3"] 
            stored_value = st.session_state["blok_6_8"].get("vi_persyaratan_pendidikan_terendah_petugas_pengumpulan_data", "")
            vi_persyaratan_pendidikan_terendah_petugas_pengumpulan_data = st.radio(
                "6.5 Persyaratan Pendidikan Terendah Petugas Pengumpulan Data",
                petugas_options,
                index = petugas_options.index(stored_value) if stored_value in petugas_options else None,
                key="vi_persyaratan_pendidikan_terendah_petugas_pengumpulan_data",
                label_visibility = "collapsed",
                horizontal=True,
                disabled = is_submitted
            )
            st.session_state["blok_6_8"]["vi_persyaratan_pendidikan_terendah_petugas_pengumpulan_data"] = vi_persyaratan_pendidikan_terendah_petugas_pengumpulan_data

            #Q6.6
            st.markdown("##### 6.6 Jumlah Petugas")
            vi_jumlah_petugas_supervisor = st.number_input("Supervisor/Penyelia/Pengawas", min_value=0, max_value=3000, step=1, value=st.session_state["blok_6_8"].get("vi_jumlah_petugas_supervisor", None), key = "vi_jumlah_petugas_supervisor", disabled = is_submitted)
            st.session_state["blok_6_8"]["vi_jumlah_petugas_supervisor"] = vi_jumlah_petugas_supervisor
            vi_jumlah_petugas_enumerator = st.number_input("Pengumpul Data/Enumerator", min_value=0, max_value=3000, step=1, value=st.session_state["blok_6_8"].get("vi_jumlah_petugas_enumerator", None), key = "vi_jumlah_petugas_enumerator", placeholder = "Tidak boleh kurang dari jumlah Supervisor/Penyelia/Pengawas", disabled = is_submitted)
            st.session_state["blok_6_8"]["vi_jumlah_petugas_enumerator"] = vi_jumlah_petugas_enumerator          

        #Q6.7
        stored_value = st.session_state["blok_6_8"].get("vi_apakah_melakukan_pelatihan_petugas", "")
        vi_apakah_melakukan_pelatihan_petugas = st.checkbox("Melakukan Pelatihan Tugas",
                                                                value=st.session_state["blok_6_8"].get("vi_apakah_melakukan_pelatihan_petugas", ""), disabled = is_submitted)
        st.session_state["blok_6_8"]["vi_apakah_melakukan_pelatihan_petugas"] = vi_apakah_melakukan_pelatihan_petugas      
   
    # st.divider()
    
    with st.expander("📘 BLOK 7 – PENGOLAHAN DAN ANALISIS", expanded=False):

        #Q7.1
        tahapan_list = []
        st.markdown("##### 7.1 Tahapan Pengolahan Data")
        stored_value = st.session_state["blok_6_8"].get("penyuntingan", "")
        penyuntingan = st.checkbox("Penyuntingan (Editing)", value=st.session_state["blok_6_8"].get("penyuntingan", ""), disabled = is_submitted)
        st.session_state["blok_6_8"]["penyuntingan"] = penyuntingan
        if penyuntingan:
            tahapan_list.append("Penyuntingan (Editing)")

        stored_value = st.session_state["blok_6_8"].get("penyandian", "")
        penyandian = st.checkbox("Penyandian (Coding)", value=st.session_state["blok_6_8"].get("penyandian", ""), disabled = is_submitted)
        st.session_state["blok_6_8"]["penyandian"] = penyandian
        if penyandian:
            tahapan_list.append("Penyandian (Coding)")
        
        stored_value = st.session_state["blok_6_8"].get("entry", "")
        entry = st.checkbox("Data Entry", value=st.session_state["blok_6_8"].get("entry", ""), disabled = is_submitted)
        st.session_state["blok_6_8"]["entry"] = entry
        if entry:
            tahapan_list.append("Data Entry")

        st.session_state["blok_6_8"]["vii_tahapan_pengolahan_data"] = tahapan_list

        stored_value = st.session_state["blok_6_8"].get("penyahihan", "")
        penyahihan = st.checkbox("Penyahihan (Validasi)", value=st.session_state["blok_6_8"].get("penyahihan", ""), disabled = is_submitted)
        st.session_state["blok_6_8"]["penyahihan"] = penyahihan
        if penyahihan:
            tahapan_list.append("Penyahihan (Validasi)")

        #Q7.2
        st.markdown("##### 7.2 Metode Analisis")
        analisis_options = ["Deskriptif", "Inferensia", "Deskriptif dan Inferensia"] 
        stored_value = st.session_state["blok_6_8"].get("vii_metode_analisis", "")
        vii_metode_analisis = st.radio(
            "7.2 Metode Analisis",
            analisis_options,
            index = analisis_options.index(stored_value) if stored_value in analisis_options else None,
            key="vii_metode_analisis",
            label_visibility = "collapsed",
            horizontal=True,
            disabled = is_submitted
        )
        st.session_state["blok_6_8"]["vii_metode_analisis"] = vii_metode_analisis

        #Q7.3
        unit_analisis_options = ["Individu", "Rumah Tangga", "Usaha/Perusahaan", "Lainnya"]
        stored_value = st.session_state["blok_6_8"].get("unit_analisis_utama", "")
        st.markdown("##### 7.3 Unit Analisis", unsafe_allow_html=True)
        unit_analisis_utama = st.multiselect(
            "7.3 Unit Analisis",
            unit_analisis_options,
            default = stored_value if isinstance(stored_value, list) else [],
            label_visibility = "collapsed",
            key="unit_analisis_utama",
            disabled = is_submitted
        )
        st.session_state["blok_6_8"]["unit_analisis_utama"] = unit_analisis_utama

        unit_analisis_lain = st.text_input("Lainnya: Sebutkan unit analisis lain", value=st.session_state["blok_6_8"].get("unit_analisis_lain", ""), key="unit_analisis_lain", placeholder = "Wajib diisi jika memilih opsi 'Lainnya'")
        st.session_state["blok_6_8"]["unit_analisis_lain"] = unit_analisis_lain

        vii_unit_analisis = unit_analisis_utama.copy()
        if "Lainnya" in vii_unit_analisis:
            if unit_analisis_lain.strip():  # only replace if user actually typed something
                vii_unit_analisis = [
                    unit_analisis_lain if item == "Lainnya" else item
                    for item in vii_unit_analisis
                ]
            else:
                vii_unit_analisis.remove("Lainnya")

        st.session_state["blok_6_8"]["vii_unit_analisis"] = vii_unit_analisis

        #Q7.4
        penyajian_options = ["Nasional", "Provinsi", "Kabupaten/Kota", "Lainnya"]
        stored_value = st.session_state["blok_6_8"].get("penyajian_utama", "")
        st.markdown("##### 7.4  Tingkat Penyajian Hasil Analisis", unsafe_allow_html=True)
        penyajian_utama = st.multiselect(
            "7.4  Tingkat Penyajian Hasil Analisis",
            penyajian_options,
            default = stored_value if isinstance(stored_value, list) else [],
            label_visibility = "collapsed",
            key="penyajian_utama",
            disabled = is_submitted
        )
        st.session_state["blok_6_8"]["penyajian_utama"] = penyajian_utama

        penyajian_lain = st.text_input("Lainnya: Sebutkan tingkat penyajian lain", value=st.session_state["blok_6_8"].get("penyajian_lain", ""), key="penyajian_lain", placeholder = "Wajib diisi jika memilih opsi 'Lainnya'")
        st.session_state["blok_6_8"]["penyajian_lain"] = penyajian_lain

        vii_tingkat_penyajian_hasil_analisis = penyajian_utama.copy()
        if "Lainnya" in vii_tingkat_penyajian_hasil_analisis:
            if penyajian_lain.strip():  # only replace if user actually typed something
                vii_tingkat_penyajian_hasil_analisis = [
                    penyajian_lain if item == "Lainnya" else item
                    for item in vii_tingkat_penyajian_hasil_analisis
                ]
            else:
                vii_tingkat_penyajian_hasil_analisis.remove("Lainnya")

        st.session_state["blok_6_8"]["vii_tingkat_penyajian_hasil_analisis"] = vii_tingkat_penyajian_hasil_analisis
  
    # st.divider()
    
    with st.expander("📘 BLOK 8 – DISEMINASI HASIL", expanded=False):

        #Q8.1
        st.markdown("##### 8.1 Produk Kegiatan yang Tersedia untuk Umum")
        stored_value = st.session_state["blok_6_8"].get("viii_ketersediaan_produk_tercetak", "")
        viii_ketersediaan_produk_tercetak = st.checkbox("Tercetak (Hardcopy)", value=st.session_state["blok_6_8"].get("viii_ketersediaan_produk_tercetak", ""), disabled = is_submitted)
        st.session_state["blok_6_8"]["viii_ketersediaan_produk_tercetak"] = viii_ketersediaan_produk_tercetak
        viii_rencana_jadwal_rilis_produk_tercetak = ""
        if viii_ketersediaan_produk_tercetak:
            viii_rencana_jadwal_rilis_produk_tercetak = st.date_input("8.2 Rencana Rilis Produk Kegiatan", value=st.session_state["blok_6_8"].get("viii_rencana_jadwal_rilis_produk_tercetak", None), key="viii_rencana_jadwal_rilis_produk_tercetak", disabled = is_submitted)
            st.session_state["blok_6_8"]["viii_rencana_jadwal_rilis_produk_tercetak"] = viii_rencana_jadwal_rilis_produk_tercetak

        stored_value = st.session_state["blok_6_8"].get("viii_ketersediaan_produk_digital", "")
        viii_ketersediaan_produk_digital = st.checkbox("Digital (Softcopy)", value=st.session_state["blok_6_8"].get("viii_ketersediaan_produk_digital", ""), disabled = is_submitted)
        st.session_state["blok_6_8"]["viii_ketersediaan_produk_digital"] = viii_ketersediaan_produk_digital
        viii_rencana_jadwal_rilis_produk_digital = ""
        if viii_ketersediaan_produk_digital:
            viii_rencana_jadwal_rilis_produk_digital = st.date_input("8.2 Rencana Rilis Produk Kegiatan", value=st.session_state["blok_6_8"].get("viii_rencana_jadwal_rilis_produk_digital", None), key="viii_rencana_jadwal_rilis_produk_digital", disabled = is_submitted)
            st.session_state["blok_6_8"]["viii_rencana_jadwal_rilis_produk_digital"] = viii_rencana_jadwal_rilis_produk_digital

        stored_value = st.session_state["blok_6_8"].get("viii_ketersediaan_produk_mikrodata", "")
        viii_ketersediaan_produk_mikrodata = st.checkbox("Data Mikro", value=st.session_state["blok_6_8"].get("viii_ketersediaan_produk_mikrodata", ""), disabled = is_submitted)
        st.session_state["blok_6_8"]["viii_ketersediaan_produk_mikrodata"] = viii_ketersediaan_produk_mikrodata
        viii_rencana_jadwal_rilis_produk_mikrodata = ""
        if viii_ketersediaan_produk_mikrodata:
            viii_rencana_jadwal_rilis_produk_mikrodata= st.date_input("8.2 Rencana Rilis Produk Kegiatan", value=st.session_state["blok_6_8"].get("viii_rencana_jadwal_rilis_produk_mikrodata", None), key="viii_rencana_jadwal_rilis_produk_mikrodata", disabled = is_submitted)
            st.session_state["blok_6_8"]["viii_rencana_jadwal_rilis_produk_mikrodata"] = viii_rencana_jadwal_rilis_produk_mikrodata

        # if st.button("💾 Simpan Blok 6 - 8"):
        #         st.session_state["blok_6_8"] = {
        #             "vi_apakah_melakukan_uji_coba": vi_apakah_melakukan_uji_coba,
        #             "qc_utama": qc_utama,
        #             "qc_lain": qc_lain,
        #             "vi_metode_pemeriksaan_kualitas_pengumpulan_data": qc_utama.append(f"Lainnya: {qc_lain}"),
        #             "vi_apakah_melakukan_penyesuaian_nonrespon": vi_apakah_melakukan_penyesuaian_nonrespon,
        #             "vi_petugas_pengumpulan_data": vi_petugas_pengumpulan_data,
        #             "vi_persyaratan_pendidikan_terendah_petugas_pengumpulan_data": vi_persyaratan_pendidikan_terendah_petugas_pengumpulan_data,
        #             "vi_jumlah_petugas_supervisor": vi_jumlah_petugas_supervisor,
        #             "vi_jumlah_petugas_enumerator": vi_jumlah_petugas_enumerator,
        #             "vi_apakah_melakukan_pelatihan_petugas": vi_apakah_melakukan_pelatihan_petugas,
        #             "vii_tahapan_pengolahan_data": tahapan_list,
        #             "vii_metode_analisis": vii_metode_analisis,
        #             "unit_analisis_utama": unit_analisis_utama,
        #             "unit_analisis_lain": unit_analisis_lain,
        #             "vii_unit_analisis": unit_analisis_utama.append(f"Lainnya: {unit_analisis_lain}"),
        #             "vii_tingkat_penyajian_hasil_analisis": penyajian_utama.append(f"Lainnya: {penyajian_lain}"),
        #             "viii_ketersediaan_produk_tercetak": viii_ketersediaan_produk_tercetak,
        #             "viii_ketersediaan_produk_digital": viii_ketersediaan_produk_digital,
        #             "viii_ketersediaan_produk_mikrodata": viii_ketersediaan_produk_mikrodata,
        #             "viii_rencana_jadwal_rilis_produk_tercetak": viii_rencana_jadwal_rilis_produk_tercetak,
        #             "viii_rencana_jadwal_rilis_produk_digital": viii_rencana_jadwal_rilis_produk_digital,
        #             "viii_rencana_jadwal_rilis_produk_mikrodata": viii_rencana_jadwal_rilis_produk_mikrodata,
        #             "last_saved": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #         }
        #         st.success("Blok 6 - 8 disimpan!")
    
    # st.divider()

with tab2:
    st.header("📊 MS Indikator")
    if "indicators" not in st.session_state or not isinstance(st.session_state.indicators, list):
        # If it's an empty dict or string from old saves, reset to []
        st.session_state.indicators = []
        
        # Add a new indicators
    if st.button("➕ Tambah Indikator", disabled = is_submitted):
        st.session_state.indicators.append({
            "nama": "",
            "definisi": "",
            "konsep": "",
            "interpretasi": "",
            "metode": "",
            "ukuran": "",
            "satuan": "",
            "klasifikasi_penyajian": "",
            "indikator_komposit": False,
            "indikator_pembangun": [],
            "variabel_pembangun": [],
            "level_estimasi": "",
            "indikator_diakses_umum": ""               
        })
    
    # Track which variable to remove
    remove_ind_index = None
    
    # Safety: handle string corruption case
    if isinstance(st.session_state.indicators, str):
        try:
            st.session_state.indicators = json.loads(st.session_state.indicators)
        except json.JSONDecodeError:
            st.session_state.indicators = []
    
    # Display all variables
    for i, ind in enumerate(st.session_state.indicators):
        ind.setdefault("indikator_pembangun", [])
        ind.setdefault("variabel_pembangun", [])
        with st.expander(f"📘 Indikator {i+1}: {ind.get('nama', '(Belum diisi)')}"):
            ind["nama"] = st.text_input(
                "Nama Indikator", value=ind.get("nama", ""), key=f"ind_nama_{i}", disabled = is_submitted
            )
            ind["definisi"] = st.text_area(
                "Definisi", value=ind.get("definisi", ""), key=f"ind_definisi_{i}", disabled = is_submitted
            )
            ind["konsep"] = st.text_input(
                "Konsep", value=ind.get("konsep", ""), key=f"ind_konsep_{i}", disabled = is_submitted
            )
            ind["interpretasi"] = st.text_area(
                "Interpretasi", value=ind.get("interpretasi", ""), key=f"ind_interpretasi_{i}", disabled = is_submitted
            )
            ind["metode"] = st.text_input(
                "Metode", value=ind.get("metode", ""), key=f"ind_metode_{i}", disabled = is_submitted
            )
            ind["ukuran"] = st.text_input(
                "Ukuran", value=ind.get("ukuran", ""), key=f"ind_ukuran_{i}", disabled = is_submitted
            )
            ind["satuan"] = st.text_input(
                "Satuan", value=ind.get("satuan", ""), key=f"ind_satuan_{i}", disabled = is_submitted
            )
            ind["klasifikasi_penyajian"] = st.text_input(
                "Klasifikasi Penyajian", value=ind.get("klasifikasi_penyajian", ""), key=f"ind_klasifikasi_penyajian_{i}", disabled = is_submitted
            )
            ind["indikator_komposit"] = st.checkbox(
                "Merupakan Indikator Komposit", value=ind.get("indikator_komposit", False), key=f"ind_indikator_komposit_{i}", disabled = is_submitted
            )

            #================================
            # CASE 1: Indikator Komposit
            #================================
            if ind["indikator_komposit"]:
                st.caption("Jika merupakan indikator komposit, tambahkan satu atau lebih indikator pembangun")
                with st.popover("Indikator Pembangun"):  
                    if st.button("➕ Tambah Indikator Pembangun", key = f"add_ind_build_{i}", disabled = is_submitted):
                        ind["indikator_pembangun"].append({
                            "nama_indikator_pembangun": "",
                            "publikasi_ketersediaan": ""
                        })
    
                    remove_sub_index = None
                    for j, sub in enumerate(ind["indikator_pembangun"]):
                        st.markdown(f"🔹 Indikator Pembangun {j+1}")
                        col1, col2 = st.columns(2)
                        with col1:
                            sub["nama_indikator_pembangun"] = st.text_input("Nama Indikator Pembangun", value = sub.get("nama_indikator_pembangun", ""), key = f"ind_build_name_{i}_{j}", disabled = is_submitted
                                                                           )
                        with col2:
                            sub["publikasi_ketersediaan"] = st.text_input("Publikasi Ketersediaan", value = sub.get("publikasi_ketersediaan", ""), key = f"ind_avail_pub{i}_{j}", disabled = is_submitted
                                                                         )
                        if st.button(f"🗑️ Hapus Indikator Pembangun {j+1}", key=f"remove_build_{i}_{j}", disabled = is_submitted):
                            remove_sub_index = j
    
                    if remove_sub_index is not None:
                        ind["indikator_pembangun"].pop(remove_sub_index)
    
            else:
                st.caption("Jika bukan merupakan indikator komposit, tambahkan satu atau lebih variabel pembangun")
                with st.popover("Variabel Pembangun"):
                    if st.button("➕ Tambah Variabel Pembangun", key=f"add_var_build_{i}", disabled = is_submitted):
                        ind["variabel_pembangun"].append({
                            "nama_variabel_pembangun": "",
                            "kegiatan_penghasil": ""
                        })
        
                    remove_var_index = None
                    for j, var in enumerate(ind["variabel_pembangun"]):
                        st.markdown(f"🔹 Variabel Pembangun {j+1}")
                        col1, col2 = st.columns(2)
                        with col1:
                            var["nama_variabel_pembangun"] = st.text_input(
                                "Nama Variabel Pembangun",
                                value=var.get("nama_variabel_pembangun", ""),
                                key=f"var_build_name_{i}_{j}", disabled = is_submitted
                            )
                        with col2:
                            var["kegiatan_penghasil"] = st.text_input(
                                "Kegiatan Penghasil Variabel",
                                value=var.get("kegiatan_penghasil", ""),
                                key=f"var_build_source_{i}_{j}", disabled = is_submitted
                            )
        
                        if st.button(f"🗑️ Hapus Variabel Pembangun {j+1}", key=f"remove_var_{i}_{j}", disabled = is_submitted):
                            remove_var_index = j
        
                    if remove_var_index is not None:
                        ind["variabel_pembangun"].pop(remove_var_index)
            
            ind["level_estimasi"] = st.text_area(
                "Level Estimasi", value=ind.get("level_estimasi", ""), key=f"ind_level_estimasi_{i}", disabled = is_submitted
            )
            ind["indikator_diakses_umum"] = st.checkbox(
                "Indikator Dapat Diakses Umum", value=ind.get("indikator_diakses_umum", False), key=f"ind_dapat_diakses_umum_{i}", disabled = is_submitted
            )            
            # Remove variable button
            if st.button(f"🗑️ Hapus Indikator {i+1}", key=f"remove_ind_{i}", disabled = is_submitted):
                remove_ind_index = i
      
            st.divider()
    
    # Actually remove the indicators after the loop
    if remove_ind_index is not None:
        st.session_state.indicators.pop(remove_ind_index)
    
    # Optional: Submit all variables
    # if st.button("💾 Simpan Semua Indikator"):
        # st.write("Indikator tersimpan:")
        # st.json(st.session_state.indicators)

with tab3:
    st.header("📈 MS Variabel")
    if "variables" in st.session_state and isinstance(st.session_state.variables, list) and len(st.session_state.variables) > 0:
        for i, var in enumerate(st.session_state.variables):
    
            with st.container():
                with st.expander(f"📘 Variabel {i+1}: {var.get('name', '(Belum diisi)')}"):
                    alias = st.text_input(
                        "Alias",
                        value=var.get("alias", ""),
                        key=f"alias_{i}", disabled = is_submitted
                    )
                    var["alias"] = alias  # store in session_state
                    
                    st.write(f"**Definisi Variabel:** {var.get('definition', '-')}")
                    st.write(f"**Konsep:** {var.get('concept', '-')}")
                    st.write(f"**Referensi Waktu:** {var.get('reference', '-')}")
                    
                    referensi_pemilihan = st.text_input(
                        "Referensi Pemilihan",
                        value=var.get("referensi_pemilihan", ""),
                        key=f"referensi_pemilihan_{i}", disabled = is_submitted
                    )
                    var["referensi_pemilihan"] = referensi_pemilihan  # store in session_state
                    
                    ukuran = st.text_input(
                        "Ukuran",
                        value=var.get("ukuran", ""),
                        key=f"ukuran_{i}", disabled = is_submitted
                    )
                    var["ukuran"] = ukuran  # store in session_state
                    
                    satuan = st.text_input(
                        "Satuan",
                        value=var.get("satuan", ""),
                        key=f"satuan_{i}", disabled = is_submitted
                    )
                    var["satuan"] = satuan  # store in session_state
                
                    tipe_data = st.text_area(
                        "Tipe Data",
                        value=var.get("tipe_data", ""),
                        key=f"interpretasi_{i}", disabled = is_submitted
                    )
                    var["tipe_data"] = tipe_data  # store in session_state

                    isian_klasifikasi = st.text_area(
                        "Isian Klasifikasi",
                        value=var.get("isian_klasifikasi", ""),
                        key=f"isian_klasifikasi_{i}", disabled = is_submitted
                    )
                    var["isian_klasifikasi"] = isian_klasifikasi

                    aturan_validasi = st.text_area(
                        "Aturan Validasi",
                        value=var.get("aturan_validasi", ""),
                        key=f"aturan_validasi_{i}", disabled = is_submitted
                    )
                    var["aturan_validasi"] = aturan_validasi

                    kalimat_pertanyaan = st.text_area(
                        "Kalimat Pertanyaan",
                        value=var.get("kalimat_perntanyaan", ""),
                        key=f"kalimat_perntanyaan{i}", disabled = is_submitted
                    )
                    var["kalimat_perntanyaan"] = kalimat_pertanyaan
                    
                    var["dapat_diakses_umum"] = st.checkbox(
                "Variabel Dapat Diakses Umum", value=var.get("dapat_diakses_umum", False), key=f"var_dapat_diakses_umum_{i}", disabled = is_submitted)  
                    
            # st.divider()
    
        # Optional: show updated full structure
        # if st.button("💾 Simpan Lengkap"):
        #     st.success("Semua variabel dan informasi tambahan tersimpan!")
        #     st.json(st.session_state.variables)
    
    else:
        st.info("Belum ada variabel yang terdeteksi pada MS Kegiatan. Input daftar variabel pada MS Kegiatan BLOK 3")
    
if st.button("💾 Simpan Semua Progress", disabled=is_submitted): 
    combined_entry = {
        "activity_id": st.session_state.current_activity_id,
        "owner": username,
        "status": st.session_state.form_data.get("status", "Draft"),
        "last_saved": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
        
        # all sections 
        "halaman_awal": st.session_state.halaman_awal, 
        "blok_1_3": st.session_state.blok_1_3, 
        "variables": st.session_state.variables, 
        "blok_4": st.session_state.blok_4, 
        "blok_5": st.session_state.blok_5, 
        "blok_6_8": st.session_state.blok_6_8, 
        "indicators": st.session_state.indicators, 
        
        # metadata 
        "revision_note": st.session_state.form_data.get("revision_note", ""),
        "revision_requested_at": st.session_state.form_data.get("revision_requested_at", ""),
        "rejection_reason": st.session_state.form_data.get("rejection_reason", ""), 
        "verified_by": st.session_state.form_data.get("verified_by", ""),
        "verifier_comment": st.session_state.form_data.get("verifier_comment", "") 
    } 
    success = save_form(
        activity_id=st.session_state.current_activity_id, 
        username=username, 
        data=combined_entry,) 
    
    if success: 
        st.success("✅ Tersimpan di Supabase!") 
    else: 
        st.error("❌ Gagal menyimpan ke Supabase.")


if st.button("📤 Submit", disabled=is_submitted): 
    ok = submit_form(st.session_state.current_activity_id) 
    if ok: 
        st.session_state.form_data["status"] = "Submitted" 
        st.success("🎉 Submitted ke Supabase!") 
        st.rerun() 
    else: 
        st.error("❌ Submit gagal.")