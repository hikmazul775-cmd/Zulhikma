import streamlit as st
import pandas as pd
import io
from sklearn.cluster import KMeans
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, HeatMap
import base64

st.set_page_config(page_title="Peta UMKM / Kampus", layout="wide")

def make_sample_data():
    # Lokasi dipindahkan ke Sulawesi Barat (Mamuju, Majene, Polewali Mandar)
    data = [
        {"name":"Warung Pantai Manakarra","type":"UMKM","latitude":-2.6773,"longitude":118.8867,"description":"Warung dekat Pantai Manakarra, Mamuju"},
        {"name":"Toko Mandar Jaya","type":"UMKM","latitude":-3.4325,"longitude":119.3430,"description":"Toko kelontong di Polewali Mandar"},
        {"name":"Universitas Sulawesi Barat","type":"Kampus","latitude":-2.6416,"longitude":118.9098,"description":"Kampus negeri di Kabupaten Majene"},
        {"name":"Kantin UNSULBAR","type":"UMKM","latitude":-2.6430,"longitude":118.9080,"description":"Kantin dalam area kampus"},
        {"name":"Cafe Bahari Mamuju","type":"UMKM","latitude":-2.6760,"longitude":118.8800,"description":"Kafe tepi laut"},
        {"name":"Politeknik Negeri Mamuju","type":"Kampus","latitude":-2.6700,"longitude":118.8905,"description":"Politeknik di Mamuju"},
        {"name":"Bakery Mandar","type":"UMKM","latitude":-3.4300,"longitude":119.3480,"description":"Toko roti khas Mandar"},
        {"name":"Studio Foto Majene","type":"UMKM","latitude":-2.6350,"longitude":118.9150,"description":"Jasa foto di Majene"},
    ]
    return pd.DataFrame(data)

def validate_df(df):
    needed = {"name","type","latitude","longitude"}
    if not needed.issubset(set(df.columns)):
        return False, f"File harus punya kolom: {', '.join(sorted(list(needed)))}"
    # ensure lat/lon numeric
    try:
        df["latitude"] = pd.to_numeric(df["latitude"])
        df["longitude"] = pd.to_numeric(df["longitude"])
    except Exception as e:
        return False, "Kolom latitude/longitude harus numeric."
    return True, ""

def dataframe_to_csv_bytes(df):
    return df.to_csv(index=False).encode('utf-8')

def get_table_download_link(df, name="data.csv"):
    csv = dataframe_to_csv_bytes(df)
    b64 = base64.b64encode(csv).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{name}">⬇️ Unduh CSV</a>'
    return href

def run_kmeans(df, n_clusters=3):
    coords = df[["latitude","longitude"]].values
    if len(coords) < n_clusters:
        # fallback: one cluster per point
        return [0]*len(df)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    labels = kmeans.fit_predict(coords)
    return labels

def create_folium_map(df, center=None, zoom_start=14, show_heatmap=False, cluster_markers=True):
    if center is None:
        # default center: mean coordinates
        center = [df["latitude"].mean(), df["longitude"].mean()]
    m = folium.Map(location=center, zoom_start=zoom_start)
    if show_heatmap:
        heat_data = df[["latitude","longitude"]].values.tolist()
        HeatMap(heat_data, radius=15, blur=10).add_to(m)
    if cluster_markers:
        mc = MarkerCluster()
        for _, r in df.iterrows():
            popup_html = f"<b>{r['name']}</b><br>Type: {r['type']}<br>{r.get('description','')}"
            folium.Marker(
                location=[r["latitude"], r["longitude"]],
                popup=popup_html,
                tooltip=r["name"],
                icon=folium.Icon(color="blue" if r["type"].lower()=="umkm" else "green", icon="info-sign")
            ).add_to(mc)
        mc.add_to(m)
    else:
        for _, r in df.iterrows():
            popup_html = f"<b>{r['name']}</b><br>Type: {r['type']}<br>{r.get('description','')}"
            folium.Marker(
                location=[r["latitude"], r["longitude"]],
                popup=popup_html,
                tooltip=r["name"],
                icon=folium.Icon(color="blue" if r["type"].lower()=="umkm" else "green")
            ).add_to(m)
    return m

# ---------- UI ----------
st.title("Peta Digital Lokasi UMKM / Kampus (Streamlit + Folium)")
st.markdown("Aplikasi contoh untuk tugas/proyek — upload data lokasi atau gunakan sample. Termasuk visualisasi clustering KMeans sebagai penerapan ML ringan.")

# Sidebar controls
st.sidebar.header("Kontrol Aplikasi")
uploaded = st.sidebar.file_uploader("Upload file CSV (kolom: name,type,latitude,longitude,description*)", type=["csv"])
use_sample = st.sidebar.checkbox("Gunakan data contoh (sample)", value=True if uploaded is None else False)
filter_type = st.sidebar.selectbox("Filter tipe lokasi", options=["Semua","UMKM","Kampus"])
search_name = st.sidebar.text_input("Cari nama lokasi (partial match)")
st.sidebar.markdown("---")

st.sidebar.subheader("Tampilan Peta / ML")
show_heatmap = st.sidebar.checkbox("Tampilkan Heatmap", False)
use_clustering = st.sidebar.checkbox("Gunakan KMeans clustering", True)
n_clusters = st.sidebar.slider("Jumlah cluster (KMeans)", 2, 8, 3) if use_clustering else None
marker_cluster = st.sidebar.checkbox("Kelompokkan marker (MarkerCluster)", True)

st.sidebar.markdown("---")
st.sidebar.subheader("Tambah lokasi manual")
with st.sidebar.form("tambah_form", clear_on_submit=True):
    new_name = st.text_input("Nama lokasi")
    new_type = st.selectbox("Tipe", ["UMKM","Kampus"])
    new_lat = st.text_input("Latitude (desimal)")
    new_lon = st.text_input("Longitude (desimal)")
    new_desc = st.text_area("Deskripsi (opsional)")
    submitted = st.form_submit_button("Tambah lokasi")
    if submitted:
        try:
            new_lat_f = float(new_lat)
            new_lon_f = float(new_lon)
            # we will append later to df
            st.session_state.setdefault("new_rows", []).append({
                "name": new_name, "type": new_type, "latitude": new_lat_f, "longitude": new_lon_f, "description": new_desc
            })
            st.success("Lokasi berhasil ditambahkan (sementara). Jangan lupa unduh atau upload sumber data final jika perlu.")
        except:
            st.error("Latitude/Longitude harus angka desimal (contoh: -6.914744)")

st.sidebar.markdown("---")
st.sidebar.info("Siap deploy ke Streamlit Cloud: push repository berisi file app.py dan requirements.txt.")

# Load data
if uploaded is not None:
    try:
        df = pd.read_csv(uploaded)
    except Exception as e:
        st.error(f"Gagal membaca file CSV: {e}")
        st.stop()
    ok, msg = validate_df(df)
    if not ok:
        st.error(msg)
        st.stop()
else:
    if use_sample:
        df = make_sample_data()
    else:
        st.info("Tidak ada data. Centang 'Gunakan data contoh' atau upload CSV.")
        df = make_sample_data()

# Append newly added rows from sidebar form in session_state
if "new_rows" in st.session_state and st.session_state["new_rows"]:
    df = pd.concat([df, pd.DataFrame(st.session_state["new_rows"])], ignore_index=True)

# Normalize type column
df["type"] = df["type"].astype(str)

# Apply filter
df_filtered = df.copy()
if filter_type != "Semua":
    df_filtered = df_filtered[df_filtered["type"].str.lower() == filter_type.lower()]

if search_name:
    df_filtered = df_filtered[df_filtered["name"].str.contains(search_name, case=False, na=False)]

if df_filtered.empty:
    st.warning("Tidak ada lokasi setelah filter/pencarian. Tampilkan sample/semua untuk melihat hasil.")
    
# Layout: map left, controls + table right
col1, col2 = st.columns([2,1])

with col1:
    st.subheader("Peta Lokasi")
    # center map on filtered data or overall
    if not df_filtered.empty:
        center = [df_filtered["latitude"].mean(), df_filtered["longitude"].mean()]
    else:
        center = [df["latitude"].mean(), df["longitude"].mean()]
    # If clustering requested, compute labels and add cluster column
    if use_clustering and not df_filtered.empty:
        try:
            labels = run_kmeans(df_filtered.reset_index(drop=True), n_clusters=n_clusters)
            df_filtered = df_filtered.reset_index(drop=True)
            df_filtered["cluster"] = labels
            # show cluster legend
            st.markdown("**Legenda cluster (KMeans)**")
            legend_html = "<div style='display:flex;gap:8px;flex-wrap:wrap;'>"
            palette = ["#e6194b","#3cb44b","#ffe119","#4363d8","#f58231","#911eb4","#46f0f0","#f032e6"]
            for i in range(n_clusters):
                color = palette[i % len(palette)]
                legend_html += f"<div style='display:flex;align-items:center;gap:6px;'><div style='width:14px;height:14px;background:{color};border:1px solid #222;'></div><div>Cluster {i}</div></div>"
            legend_html += "</div>"
            st.markdown(legend_html, unsafe_allow_html=True)
            # Create folium map and draw clustered markers colored by cluster
            m = folium.Map(location=center, zoom_start=14)
            for i in range(n_clusters):
                sub = df_filtered[df_filtered["cluster"]==i]
                mc = MarkerCluster(name=f"Cluster {i}")
                for _, r in sub.iterrows():
                    popup_html = f"<b>{r['name']}</b><br>Type: {r['type']}<br>{r.get('description','')}"
                    folium.Marker(
                        location=[r["latitude"], r["longitude"]],
                        popup=popup_html,
                        tooltip=r["name"],
                        icon=folium.Icon(color="white", icon_color="black", icon="info-sign")
                    ).add_to(mc)
                mc.add_to(m)
                # draw cluster centroid
                centroid = sub[["latitude","longitude"]].mean().values.tolist()
                folium.CircleMarker(location=centroid, radius=8, color=palette[i % len(palette)], fill=True, fill_opacity=0.7, popup=f"Centroid {i}").add_to(m)
            if show_heatmap:
                heat_data = df_filtered[["latitude","longitude"]].values.tolist()
                HeatMap(heat_data, radius=15, blur=10).add_to(m)
        except Exception as e:
            st.error(f"Gagal menjalankan clustering: {e}")
            m = create_folium_map(df_filtered, center=center, cluster_markers=marker_cluster, show_heatmap=show_heatmap)
    else:
        # no clustering
        m = create_folium_map(df_filtered, center=center, cluster_markers=marker_cluster, show_heatmap=show_heatmap)

    # Render folium map in streamlit
    st_data = st_folium(m, width="100%", height=600)

with col2:
    st.subheader("Data & Kontrol")
    st.markdown(f"Jumlah lokasi (setelah filter): **{len(df_filtered)}**")
    # Show table
    st.dataframe(df_filtered.reset_index(drop=True))

    # Download link
    st.markdown(get_table_download_link(df_filtered.reset_index(drop=True), name="lokasi_filtered.csv"), unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("Statistik Sederhana")
    st.write("Jumlah per tipe:")
    counts = df_filtered["type"].value_counts()
    st.bar_chart(counts)

    st.markdown("---")
    st.subheader("Preview Lokasi Teratas")
    st.table(df_filtered.reset_index(drop=True).head(10))

st.markdown("---")
st.markdown("### Cara pakai singkat")
st.markdown("""
1. Upload file CSV dengan kolom minimal: `name,type,latitude,longitude` (kolom `description` opsional).  
2. Atau centang *Gunakan data contoh* untuk mencoba.  
3. Gunakan filter, cari, atau tambahkan lokasi manual di sidebar.  
4. Aktifkan KMeans untuk melihat cluster lokasi (sebagai contoh penerapan ML).  
5. Klik *⬇️ Unduh CSV* untuk menyimpan data hasil filter.
""")

st.markdown("### Contoh format CSV (baris header + contoh):")
st.code("name,type,latitude,longitude,description\nWarung Maju,UMKM,-6.914744,107.609810,Warung dekat kampus A\nKampus Utama,Kampus,-6.922000,107.610000,Kampus negeri")

st.markdown("---")
st.markdown("**Catatan**: Untuk deploy ke Streamlit Cloud, buat repository berisi `app.py` dan `requirements.txt` (lihat di bawah).")

# Requirements snippet (show to user)
st.markdown("### requirements.txt (salin ke file `requirements.txt` dalam repo)")
st.code("""
streamlit>=1.18
pandas
scikit-learn
folium
streamlit-folium
""".strip())

st.success("Aplikasi siap dijalankan: `streamlit run app.py`")
