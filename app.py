import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar

# 1. KONFIGURASI HALAMAN WEB
st.set_page_config(page_title="Sistem Pengurusan Jadual Staf", layout="wide")
st.title("📅 Sistem Pengurusan Jadual Kerja Staf Online (Official Connection)")
st.markdown("Sistem pengurusan jadual pintar yang dihubungkan terus bersama Google Sheets.")

# 2. SAMBUNGAN RASMI GOOGLE SHEETS
# Sila pastikan link di bawah adalah link Google Sheets anda yang telah di-SHARE sebagai EDITOR
URL_SHEETS = "PASANG_LINK_GOOGLE_SHEETS_ANDA_DI_SINI"

@st.cache_data(ttl=10)  # Menyegarkan data setiap 10 saat jika ada perubahan di Sheets
def muat_semua_data():
    try:
        # Menggunakan fungsi pembacaan data rasmi dari Streamlit
        df_rekod = st.connection("sheets", type=st.connections.SQLConnection).query(f'SELECT * FROM "{URL_SHEETS}" WHERE 1=1', sheet="Rekod")
        df_rekod['Tarikh'] = pd.to_datetime(df_rekod['Tarikh']).dt.date
    except Exception:
        df_rekod = pd.DataFrame(columns=['Tarikh', 'Nama Staff', 'Status', 'Catatan'])
        
    try:
        df_staff = st.connection("sheets", type=st.connections.SQLConnection).query(f'SELECT * FROM "{URL_SHEETS}" WHERE 1=1', sheet="Staff")
        senarai = list(df_staff['Nama Staff'].dropna().unique())
        kuota = pd.Series(df_staff['Kuota AL'].values, index=df_staff['Nama Staff']).to_dict()
    except Exception as e:
        st.error(f"⚠️ Sistem masih gagal membaca Google Sheets anda. Ralat: {e}")
        senarai = ["Sila Isi Nama Di Sheets"]
        kuota = {"Sila Isi Nama Di Sheets": 0}
        
    return df_rekod, senarai, kuota

# Panggil fungsi untuk dapatkan data terkini
df_asal, SENARAI_STAFF, KUOTA_AL_ASAL = muat_semua_data()

# 3. DATA PRA-PASANG CUTI UMUM MALAYSIA 2026
CUTI_UMUM_2026 = {
    date(2026, 1, 1): "New Year's Day",
    date(2026, 1, 30): "Thaipusam",
    date(2026, 2, 17): "Chinese New Year",
    date(2026, 2, 18): "Chinese New Year (Day 2)",
    date(2026, 3, 20): "Hari Raya Aidilfitri",
    date(2026, 3, 21): "Hari Raya Aidilfitri (Day 2)",
    date(2026, 5, 1): "Labour Day",
    date(2026, 5, 31): "Wesak Day",
    date(2026, 6, 1): "Agong's Birthday",
    date(2026, 8, 31): "Merdeka Day",
    date(2026, 9, 16): "Malaysia Day",
    date(2026, 11, 8): "Deepavali",
    date(2026, 12, 25): "Christmas Day"
}

PILIHAN_STATUS = ["Bekerja", "RD (Rest Day)", "AL (Annual Leave)", "SL (Sick Leave)", "EL (Emergency Leave)", "PH (Public Holiday)", "RLPH (Replace PH)"]

# 4. MENU SIDEBAR
menu = st.sidebar.radio("Menu Utama", ["Atur Jadual Staf", "Lihat Jadual Bulanan", "Ringkasan & Baki AL Staff"])

# --- MENU 1: ATUR JADUAL STAF ---
if menu == "Atur Jadual Staf":
    st.header("📝 Kemaskini / Masukkan Jadual")
    
    col1, col2 = st.columns(2)
    with col1:
        staf_dipilih = st.selectbox("Pilih Nama Staff", SENARAI_STAFF)
        tarikh_dipilih = st.date_input("Pilih Tarikh", date.today())
    
    is_ph = tarikh_dipilih in CUTI_UMUM_2026
    index_status_default = 5 if is_ph else 0 
    
    with col2:
        status_dipilih = st.selectbox("Pilih Status Tugasan/Cuti", PILIHAN_STATUS, index=index_status_default)
        catatan = st.text_input("Catatan (Opsional)", f"{CUTI_UMUM_2026[tarikh_dipilih]}" if is_ph else "")
        
    if is_ph:
        st.warning(f"📢 Nota: Tarikh ini adalah Cuti Umum: **{CUTI_UMUM_2026[tarikh_dipilih]}**")
        
    st.markdown("---")
    st.info("Sila klik butang di bawah, salin kod data, dan masukkan ke dalam Google Sheets pada sheet 'Rekod':")
    
    if st.button("Jana Kod Data untuk Sheet 'Rekod'"):
        tarikh_str = tarikh_dipilih.strftime("%Y-%m-%d")
        data_baru = f"{tarikh_str},{staf_dipilih},{status_dipilih},{catatan}"
        st.code(data_baru, language="text")
        st.success("Salin baris di atas dan paste ke dalam sheet 'Rekod' di baris paling bawah.")

# --- MENU 2: LIHAT JADUAL BULANAN ---
elif menu == "Lihat Jadual Bulanan":
    st.header("📊 Paparan Jadual Bekerja Bulanan")
    
    col1, col2 = st.columns(2)
    with col1:
        tahun_pilih = st.selectbox("Pilih Tahun", [2026, 2027], index=0)
    with col2:
        bulan_pilih = st.selectbox("Pilih Bulan", list(range(1, 13)), format_func=lambda x: calendar.month_name[x])
        
    ph_bulan_ini = [f"{k.day}hb: {v}" for k, v in CUTI_UMUM_2026.items() if k.month == bulan_pilih and k.year == tahun_pilih]
    if ph_bulan_ini:
        st.markdown(f"📌 **Cuti Umum Bulan Ini:** {', '.join(ph_bulan_ini)}")
        
    if not df_asal.empty and SENARAI_STAFF != ["Sila Isi Nama Di Sheets"]:
        df_asal['Tarikh'] = pd.to_datetime(df_asal['Tarikh'])
        df_tapis = df_asal[(df_asal['Tarikh'].dt.month == bulan_pilih) & (df_asal['Tarikh'].dt.year == tahun_pilih)]
        
        bil_hari = calendar.monthrange(tahun_pilih, bulan_pilih)[1]
        hari_kolum = list(range(1, bil_hari + 1))
        
        grid_jadual = pd.DataFrame("-", index=SENARAI_STAFF, columns=hari_kolum)
        
        for hari in hari_kolum:
            tarikh_semak = date(tahun_pilih, bulan_pilih, hari)
            if tarikh_semak in CUTI_UMUM_2026:
                grid_jadual[hari] = "[PH]"
        
        if not df_tapis.empty:
            for _, row in df_tapis.iterrows():
                nama = row['Nama Staff']
                hari_data = row['Tarikh'].day
                status_data = row['Status']
                
                singkatan = status_data.split(" ")[0]
                if nama in grid_jadual.index and hari_data in grid_jadual.columns:
                    grid_jadual.loc[nama, hari_data] = singkatan

        st.dataframe(grid_jadual, use_container_width=True)
        st.caption("Petunjuk: [PH] = Cuti Umum, Bekerja = Hari Kerja, RD = Rest Day, AL = Annual Leave, SL = Sick Leave")
    else:
        st.warning("Database jadual masih kosong atau senarai staf belum diisi di Google Sheets.")

# --- MENU 3: RINGKASAN & BAKI AL STAFF ---
elif menu == "Ringkasan & Baki AL Staff":
    st.header("🧮 Analisis Kehadiran & Penjejak Baki Cuti Tahunan (AL)")
    
    tahun_pilih = st.selectbox("Pilih Tahun Analisis", [2026, 2027], index=0)
    bulan_pilih = st.selectbox("Pilih Bulan Analisis", list(range(1, 13)), format_func=lambda x: calendar.month_name[x])
    
    st.subheader(f"Statistik Tugasan Bulan {calendar.month_name[bulan_pilih]} {tahun_pilih}")
    df_ringkasan = pd.DataFrame(0, index=SENARAI_STAFF, columns=PILIHAN_STATUS)
    
    if not df_asal.empty and SENARAI_STAFF != ["Sila Isi Nama Di Sheets"]:
        df_asal['Tarikh'] = pd.to_datetime(df_asal['Tarikh'])
        df_tapis = df_asal[(df_asal['Tarikh'].dt.month == bulan_pilih) & (df_asal['Tarikh'].dt.year == tahun_pilih)]
        
        if not df_tapis.empty:
            stats = df_tapis.groupby(['Nama Staff', 'Status']).size().unstack(fill_value=0)
            for col in stats.columns:
                if col in df_ringkasan.columns:
                    df_ringkasan[col] = stats[col]
                    
    st.dataframe(df_ringkasan, use_container_width=True)
    
    st.markdown("---")
    st.subheader(f"📉 Penjejak Baki Annual Leave (AL) Bagi Tahun {tahun_pilih}")
    
    data_baki_al = []
    if SENARAI_STAFF != ["Sila Isi Nama Di Sheets"]:
        for staff in SENARAI_STAFF:
            kuota_asal = KUOTA_AL_ASAL.get(staff, 0)
            
            if not df_asal.empty:
                al_diambil = len(df_asal[
                    (df_asal['Nama Staff'] == staff) & 
                    (df_asal['Status'] == "AL (Annual Leave)") & 
                    (df_asal['Tarikh'].dt.year == tahun_pilih)
                ])
            else:
                al_diambil = 0
                
            baki_semasa = kuota_asal - al_diambil
            data_baki_al.append({
                "Nama Staff": staff,
                "Kuota Asal Dari Sheets (Hari)": kuota_asal,
                "AL Telah Diambil": al_diambil,
                "Baki AL Semasa": baki_semasa
            })
            
        df_baki_al = pd.DataFrame(data_baki_al).set_index("Nama Staff")
        st.table(df_baki_al)
