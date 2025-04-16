import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient
from datetime import datetime
import plotly.express as px
import numpy as np
from sklearn.linear_model import LinearRegression
import google.generativeai as genai

# --- Setup Streamlit ---
st.set_page_config(page_title="AquaSync Dashboard", layout="wide")

# --- API Key dan Mongo URI ---
gemini_api_key = st.secrets["gcp"]["gemini_api_key"]
mongo_uri = st.secrets["mongo"]["uri"]

# --- Connect MongoDB ---
client = MongoClient(mongo_uri)
db = client["IotHatch"]
collection = db["aquasync"]
data = list(collection.find({}, {"_id": 0}))  # ambil semua kecuali _id

df = pd.DataFrame(data)

# --- Validasi data ---
if df.empty or "timestamp" not in df.columns or "volume" not in df.columns:
    st.warning("Data dari MongoDB kosong atau format tidak sesuai.")
    st.stop()

df["timestamp"] = pd.to_datetime(df["timestamp"])
df["date"] = df["timestamp"].dt.date

# --- Sidebar Filter Waktu ---
st.sidebar.header("📅 Filter Waktu")
min_date = df["date"].min()
max_date = df["date"].max()

start_date = st.sidebar.date_input("Tanggal mulai", min_value=min_date, max_value=max_date, value=min_date)
end_date = st.sidebar.date_input("Tanggal akhir", min_value=min_date, max_value=max_date, value=max_date)

filtered_df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
filtered_df["volume"] = filtered_df["volume"] / 1000  # dari ml ke liter

# --- Judul ---
st.title("💧 AquaSync Dashboard")

# --- Insight Otomatis ---
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("💡 Insight Otomatis dari Data")

if not filtered_df.empty:
    # Volume udah dalam liter, jadi gak perlu konversi lagi
    daily_sum = filtered_df.groupby("date")["volume"].sum()
    max_day = daily_sum.idxmax()
    max_val = daily_sum.max()
    trend = "naik" if filtered_df["volume"].iloc[-1] > filtered_df["volume"].iloc[0] else "turun"

    insight = f"""
    - Hari dengan penggunaan tertinggi: *{max_day}* sebesar *{max_val:.2f} liter*
    - Tren penggunaan air selama periode ini: *{trend}*
    """
    st.markdown(insight)
else:
    st.info("Belum cukup data untuk insight.")

# --- Ringkasan Data ---
if not filtered_df.empty:
    # Volume udah dalam liter, gak perlu dibagi 1000
    total_volume = filtered_df["volume"].sum()
    avg_volume = filtered_df["volume"].mean()

    col1, col2 = st.columns(2)
    col1.metric("🔢 Total Air Digunakan", f"{total_volume:.2f} Liter")
    col2.metric("📏 Rata-rata per Penggunaan", f"{avg_volume:.2f} Liter")
else:
    st.warning("Tidak ada data untuk rentang waktu yang dipilih.")

# --- Tabs UI Style ---
st.markdown("""
    <style>
    button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] p {
        font-size: 20px !important;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Total Penggunaan Air",
    "📈 Rata-rata per Hari",
    "📌 Proporsi Penggunaan",
    "🚨 Anomali",
    "🔮 Prediksi"
])

# --- Tab 1 ---
with tab1:
    st.subheader("📊 Total Penggunaan Air per Hari")
    if not filtered_df.empty:
        # Konversi volume ke liter dan pembulatan ke dua desimal
        filtered_df["volume"] = filtered_df["volume"].round(2)

        total_per_day = filtered_df.groupby("date")["volume"].sum().reset_index()
        total_per_day["volume"] = total_per_day["volume"].round(2)  # pembulatan volume

        fig = px.bar(
            total_per_day, x="date", y="volume",
            labels={"date": "Tanggal", "volume": "Total (Liter)"},
            title="Total Penggunaan Air per Hari",
            color_discrete_sequence=["#1f77b4"]
        )

        # Menambahkan satuan Liter di label
        fig.update_layout(
            yaxis_title="Total (Liter)",
            xaxis_title="Tanggal",
            font=dict(size=12),
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="white"
        )

        st.plotly_chart(fig, use_container_width=True)

# --- Tab 2 ---
with tab2:
    st.subheader("📈 Rata-rata Volume Air per Hari")
    if not filtered_df.empty:
        # Konversi volume ke liter dan pembulatan ke dua desimal
        filtered_df["volume"] = filtered_df["volume"].round(2)

        avg_df = filtered_df.groupby("date")["volume"].mean().reset_index()
        avg_df["volume"] = avg_df["volume"].round(2)  # pembulatan volume

        # Membuat grafik line chart
        st.line_chart(avg_df.set_index('date')["volume"], use_container_width=True)

# --- Tab 3 ---
with tab3:
    st.subheader("📌 Proporsi Penggunaan Air per Hari")
    if not filtered_df.empty:
        pie_df = filtered_df.groupby("date")["volume"].sum().reset_index()
        pie_df["volume"] = pie_df["volume"].round(2)  # pembulatan volume

        fig = px.pie(pie_df, names="date", values="volume", title="Persentase Penggunaan", hole=0.4)
        fig.update_layout(
            title="Proporsi Penggunaan Air per Hari",
            annotations=[dict(text='Liter', x=0.5, y=0.5, font_size=20, showarrow=False)],
            font=dict(size=12),
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="white"
        )

        st.plotly_chart(fig)

# --- Tab 4 ---
with tab4:
    st.subheader("🚨 Anomali Penggunaan Air")
    if not filtered_df.empty:
        anomalies = filtered_df[filtered_df["volume"] > 200]
        anomalies["volume"] = anomalies["volume"].round(2)  # pembulatan volume
        if not anomalies.empty:
            st.error("Anomali terdeteksi (>200 liter):")
            st.dataframe(anomalies[["timestamp", "volume"]])
        else:
            st.success("Tidak ada anomali.")
    else:
        st.info("Data kosong.")


# --- Tab 5 ---
with tab5:
    st.subheader("🔮 Prediksi Penggunaan Air (Linear Regression)")
    if len(filtered_df) >= 3:
        pred_df = filtered_df.groupby("date")["volume"].sum().reset_index()
        pred_df["ordinal"] = pd.to_datetime(pred_df["date"]).map(datetime.toordinal)

        X = pred_df["ordinal"].values.reshape(-1, 1)
        y = pred_df["volume"].values

        model = LinearRegression()
        model.fit(X, y)

        last_date = pred_df["date"].max()
        future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, 4)]
        future_ordinals = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
        preds = model.predict(future_ordinals)

        future_df = pd.DataFrame({"date": future_dates, "predicted_volume": preds})

        combined = pd.concat([
            pred_df[["date", "volume"]].rename(columns={"volume": "value"}).assign(type="Aktual"),
            future_df.rename(columns={"predicted_volume": "value"}).assign(type="Prediksi")
        ])

        fig = px.line(combined, x="date", y="value", color="type", markers=True, title="Aktual vs Prediksi")
        st.dataframe(future_df)
        st.plotly_chart(fig)
    else:
        st.info("Data kurang untuk prediksi.")


# --- AI Assistant ---
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel("models/gemini-2.0-flash")

with st.sidebar:
    st.markdown("## 🤖 AI AquaSync Assistant")

    if "last_ai_answer" not in st.session_state:
        st.session_state.last_ai_answer = ""

    with st.form("ai_form"):
        user_prompt = st.text_input("Tanya sesuatu tentang data air:")
        submit = st.form_submit_button("Tanya AI")

        if submit and user_prompt.strip():
            with st.spinner("AI sedang mikir..."):
                try:
                    response = model.generate_content(f"""
                    Kamu adalah AI di sistem IoT bernama AquaSync.
                    Berikut data penggunaan air: {filtered_df.to_dict(orient='records')}
                    Jawab pertanyaan ini: {user_prompt}
                    """)
                    st.session_state.last_ai_answer = response.text
                except Exception as e:
                    st.session_state.last_ai_answer = f"Error: {str(e)}"

    if st.session_state.last_ai_answer:
        st.markdown("**Jawaban AI:**")
        st.write(st.session_state.last_ai_answer)
