import streamlit as st
import pandas as pd
import io
from sklearn.cluster import KMeans
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, HeatMap
import base64

st.set_page_config(page_title="Peta UMKM / Kampus - Sulawesi Barat", layout="wide")

# ---------- Helper functions ----------
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
    try:
        df["latitude"] = pd.to_numeric(df["latitude"])
        df["longitude"] = pd.to_numeric(df["longitude"])
    except Exception:
        return False, "Kolom latitude/longitude harus numeric."
    return True, ""

def dataframe_to_csv_bytes(df):
    return df.to_csv(index=False).encode('utf-8')

def get_table_download_l