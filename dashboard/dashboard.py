import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

# ==============================
# CONFIGURATION & PAGE SETUP
# ==============================
st.set_page_config(
    page_title="E-Commerce Analytics Dashboard",
    page_icon="📦",
    layout="wide"
)
sns.set_theme(style="whitegrid")

# ==============================
# DATA LOADING & CACHING
# ==============================
@st.cache_data
def load_data():
    # Sesuaikan path sesuai struktur direktori submission
    # Jika main_data.csv ada di folder yang sama dengan dashboard.py
    df = pd.read_csv("dashboard/main_data.csv")
    
    # Pastikan tipe data datetime kembali normal setelah di-load dari CSV
    datetime_cols = ['order_purchase_timestamp', 'order_approved_at', 
                     'order_delivered_carrier_date', 'order_delivered_customer_date', 
                     'order_estimated_delivery_date']
    for col in datetime_cols:
        df[col] = pd.to_datetime(df[col])
    return df

all_df = load_data()

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.title("📦 Olist E-Commerce")
    st.write("Dashboard ini menganalisis performa logistik dan segmentasi pelanggan Olist dari tahun 2017 hingga 2018.")
    st.markdown("---")
    
    # Filter Interaktif: Rentang Waktu
    min_date = all_df["order_purchase_timestamp"].min().date()
    max_date = all_df["order_purchase_timestamp"].max().date()
    
    # Menangkap input dalam satu variabel untuk menghindari error unpacking
    # Batasan min_value dan max_value dihapus agar st.warning kuning kita bisa terpanggil 
    # saat pengguna menginput tanggal jauh di masa depan (misal: 2026)
    date_range = st.date_input(
        label='Rentang Waktu Transaksi',
        value=[min_date, max_date]
    )

# Error handling untuk pemilihan tanggal
if len(date_range) == 2:
    start_date, end_date = date_range
elif len(date_range) == 1:
    # Jika user baru memilih 1 tanggal, jadikan start dan end di hari yang sama
    start_date = date_range[0]
    end_date = date_range[0] 
else:
    # Fallback aman
    start_date = min_date
    end_date = max_date

# Filter dataset berdasarkan input sidebar
main_df = all_df[(all_df["order_purchase_timestamp"].dt.date >= start_date) & 
                 (all_df["order_purchase_timestamp"].dt.date <= end_date)]

# ==============================
# MAIN DASHBOARD CONTENT
# ==============================
st.title("Data Analytics Dashboard: E-Commerce Olist")
st.markdown("---")

# Menggunakan Tabs untuk memisahkan konteks analisis
tab1, tab2 = st.tabs(["🚚 Analisis Logistik & Geospasial", "💎 RFM & Segmentasi Pelanggan"])

# ------------------------------
# TAB 1: LOGISTIK & GEOSPASIAL
# ------------------------------
with tab1:
    st.header("Performa Logistik & Keterlambatan Wilayah")
    
    # Cegah error jika dataframe kosong (di luar rentang)
    if not main_df.empty:
        # Kalkulasi Metrik Logistik
        total_orders = len(main_df)
        delayed_orders = main_df['is_delayed'].sum()
        delay_rate = (delayed_orders / total_orders) * 100 if total_orders > 0 else 0
        
        # Menampilkan Summary Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Pesanan Berhasil", f"{total_orders:,}")
        col2.metric("Pesanan Terlambat", f"{delayed_orders:,}")
        col3.metric("Tingkat Keterlambatan", f"{delay_rate:.2f}%")
        
        st.markdown("---")
        
        st.subheader("Distribusi Keterlambatan Pengiriman")
        
        # Cegah error visualisasi jika pesanan terlambat = 0 (kinerja sempurna)
        if delayed_orders > 0:
            state_logistics = main_df.groupby('geolocation_state').agg(
                total_orders=('order_id', 'count'),
                delayed_orders=('is_delayed', 'sum')
            ).reset_index()
            state_logistics['delay_percentage'] = (state_logistics['delayed_orders'] / state_logistics['total_orders']) * 100
            state_logistics_sorted = state_logistics.sort_values(by='delay_percentage', ascending=False).head(10)
            
            # Render Plot
            fig1, ax = plt.subplots(1, 2, figsize=(18, 7))
            
            # Bar Chart
            sns.barplot(x='delay_percentage', y='geolocation_state', data=state_logistics_sorted, palette='Reds_r', ax=ax[0])
            ax[0].set_title('Top 10 Wilayah dengan Tingkat Keterlambatan Tertinggi', fontsize=14, weight='bold')
            ax[0].set_xlabel('Persentase Keterlambatan (%)', fontsize=12)
            ax[0].set_ylabel('State', fontsize=12)
            
            max_width = state_logistics_sorted['delay_percentage'].max()
            ax[0].set_xlim(0, max_width + 4 if pd.notna(max_width) else 100)
            
            for p in ax[0].patches:
                width = p.get_width()
                if width > 0:
                    ax[0].text(width + 0.3, p.get_y() + p.get_height()/2, f'{width:.2f}%', ha="left", va="center", fontsize=10)

            # Map Scatter
            brazil_geo = main_df[
                (main_df['geolocation_lat'] <= 5.274388) & 
                (main_df['geolocation_lat'] >= -33.751169) & 
                (main_df['geolocation_lng'] <= -34.793147) & 
                (main_df['geolocation_lng'] >= -73.982830)
            ]
            delayed_geo = brazil_geo[brazil_geo['is_delayed'] == True]
            
            ax[1].scatter(brazil_geo['geolocation_lng'], brazil_geo['geolocation_lat'], alpha=0.05, s=1, color='lightgray', label='Tepat Waktu')
            if not delayed_geo.empty:
                ax[1].scatter(delayed_geo['geolocation_lng'], delayed_geo['geolocation_lat'], alpha=0.3, s=3, color='red', label='Terlambat')
            
            ax[1].set_title('Peta Konsentrasi Keterlambatan di Brazil', fontsize=14, weight='bold')
            ax[1].set_xlabel('Longitude', fontsize=12)
            ax[1].set_ylabel('Latitude', fontsize=12)
            ax[1].legend(loc='upper right')

            sns.despine()
            plt.tight_layout()
            st.pyplot(fig1)
        else:
            st.info("Logistik 100% tepat waktu pada rentang tanggal ini. Tidak ada data keterlambatan untuk divisualisasikan.")
    else:
        st.warning("Tidak ada data transaksi pada rentang waktu yang dipilih. Silakan sesuaikan filter tanggal di sidebar.")

# ------------------------------
# TAB 2: RFM ANALYSIS
# ------------------------------
with tab2:
    st.header("Segmentasi Pelanggan Berdasarkan RFM")
    
    # Cegah error jika dataframe kosong (di luar rentang)
    if not main_df.empty:
        recent_date = main_df['order_purchase_timestamp'].max() + pd.Timedelta(days=1)
        rfm_df = main_df.groupby('customer_unique_id').agg({
            'order_purchase_timestamp': lambda x: (recent_date - x.max()).days,
            'order_id': 'count',
            'payment_value': 'sum'
        }).reset_index()
        rfm_df.columns = ['customer_unique_id', 'recency', 'frequency', 'monetary']
        
        # Algoritma qcut (kuintil 5) butuh minimal 5 pelanggan unik dengan sebaran data yang cukup
        if len(rfm_df) >= 5:
            try:
                rfm_df['r_rank'] = rfm_df['recency'].rank(ascending=False)
                rfm_df['r_score'] = pd.qcut(rfm_df['r_rank'], 5, labels=[1, 2, 3, 4, 5]).astype(int)
                rfm_df['f_rank'] = rfm_df['frequency'].rank(method='first')
                rfm_df['f_score'] = pd.qcut(rfm_df['f_rank'], 5, labels=[1, 2, 3, 4, 5]).astype(int)
                rfm_df['m_rank'] = rfm_df['monetary'].rank(method='first')
                rfm_df['m_score'] = pd.qcut(rfm_df['m_rank'], 5, labels=[1, 2, 3, 4, 5]).astype(int)
                
                def segment_customer(row):
                    if row['r_score'] in [4, 5] and row['f_score'] in [4, 5] and row['m_score'] in [4, 5]:
                        return 'Champions'
                    elif row['r_score'] in [1, 2] and row['f_score'] in [3, 4, 5] and row['m_score'] in [3, 4, 5]:
                        return 'At Risk'
                    elif row['r_score'] in [4, 5] and row['f_score'] in [1, 2]:
                        return 'New Customers'
                    elif row['r_score'] in [1, 2] and row['f_score'] in [1, 2]:
                        return 'Lost'
                    else:
                        return 'Regulars'
                
                rfm_df['customer_segment'] = rfm_df.apply(segment_customer, axis=1)
                segment_distribution = rfm_df['customer_segment'].value_counts(normalize=True) * 100
                
                champions_pct = segment_distribution.get('Champions', 0)
                at_risk_pct = segment_distribution.get('At Risk', 0)
                
                col1, col2 = st.columns(2)
                col1.metric("Pelanggan Loyal (Champions)", f"{champions_pct:.2f}%")
                col2.metric("Pelanggan Terancam Churn (At Risk)", f"{at_risk_pct:.2f}%", delta="Perlu Tindakan", delta_color="inverse")
                
                st.markdown("---")
                
                fig2, ax2 = plt.subplots(figsize=(10, 6))
                colors = ['#d3d3d3' if seg not in ['Champions', 'At Risk'] else ('#ff9999' if seg == 'At Risk' else '#66b3ff') for seg in segment_distribution.index]
                
                sns.barplot(x=segment_distribution.values, y=segment_distribution.index, palette=colors, ax=ax2)
                ax2.set_title('Distribusi Segmentasi Pelanggan (RFM)', fontsize=14, weight='bold')
                ax2.set_xlabel('Persentase Pelanggan (%)', fontsize=12)
                ax2.set_ylabel('Segmen', fontsize=12)
                
                for i, v in enumerate(segment_distribution.values):
                    ax2.text(v + 0.5, i + 0.1, f"{v:.2f}%", color='black', fontsize=11)
                
                sns.despine()
                plt.tight_layout()
                st.pyplot(fig2)
                
            except ValueError:
                # Menangani error jika data terlalu homogen (variasi terlalu kecil untuk dibagi 5 kuintil)
                st.warning("Variasi data transaksi terlalu kecil untuk dikelompokkan ke dalam 5 segmen RFM pada rentang waktu ini.")
        else:
            # Menangani error jika jumlah pelanggan kurang dari 5 orang
            st.warning("Jumlah pelanggan unik terlalu sedikit (< 5 orang) pada rentang waktu yang dipilih untuk melakukan pemodelan segmentasi.")
    else:
        st.warning("Tidak ada data transaksi pada rentang waktu yang dipilih. Silakan sesuaikan filter tanggal di sidebar.")