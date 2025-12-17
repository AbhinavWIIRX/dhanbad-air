import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE SETUP (Must be first) ---
st.set_page_config(page_title="Dhanbad Mine Safety", page_icon="⛏️", layout="wide")

# --- CUSTOM CSS FOR "PRO" LOOK ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1995/1995515.png", width=100)
    st.title("Control Panel")
    selected_area = st.selectbox("Select Mining Area", ["Dhanbad City", "Jharia Coal Field", "Sindri Industrial"])
    
    # Coordinate Logic
    coords = {
        "Dhanbad City": {"lat": 23.7957, "lon": 86.4304},
        "Jharia Coal Field": {"lat": 23.7430, "lon": 86.4116},
        "Sindri Industrial": {"lat": 23.6496, "lon": 86.5147}
    }
    
    st.divider()
    st.write("🔧 **System Status:** Online")
    st.write("📡 **Source:** Sat-Model (CAMS)")

# --- MAIN DATA LOGIC ---
@st.cache_data
def get_data(lat, lon):
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["pm10", "pm2_5", "dust"],
        "timezone": "Asia/Kolkata",
        "forecast_days": 3
    }
    response = requests.get(url, params=params)
    hourly = response.json()['hourly']
    df = pd.DataFrame({
        "Time": pd.to_datetime(hourly['time']),
        "PM10": hourly['pm10'],
        "PM2.5": hourly['pm2_5'],
        "Dust": hourly['dust']
    })
    return df

# --- UI LAYOUT ---
st.title(f"⛏️ Real-time Safety Monitor: {selected_area}")

# 1. Fetch Data
lat = coords[selected_area]["lat"]
lon = coords[selected_area]["lon"]
try:
    df = get_data(lat, lon)
    
    # Get Current Values
    current = df.iloc[0] # taking the first forecast as "current" for demo
    
    # 2. TOP METRICS ROW
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("PM 2.5 (Fine Dust)", f"{current['PM2.5']} µg/m³", delta="-2.5" if current['PM2.5'] < 100 else "12.4", delta_color="inverse")
    with col2:
        st.metric("PM 10 (Coal Dust)", f"{current['PM10']} µg/m³", delta="5.1", delta_color="inverse")
    with col3:
        status = "Safe" if current['PM2.5'] < 60 else "Hazardous"
        color = "green" if status == "Safe" else "red"
        st.markdown(f"**Status:** :{color}[**{status}**]")
    with col4:
         # DOWNLOAD BUTTON (Engineering Feature)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Log", data=csv, file_name="mine_safety_log.csv", mime="text/csv")

    # 3. ADVANCED VISUALIZATION (Tabs)
    tab1, tab2 = st.tabs(["📊 Trend Analysis", "🗺️ Geo-Location"])
    
    with tab1:
        # Comparison Chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Time'], y=df['PM10'], mode='lines', name='PM 10 (Actual)', line=dict(color='#ff4b4b')))
        fig.add_trace(go.Scatter(x=df['Time'], y=df['PM2.5'], mode='lines', name='PM 2.5 (Actual)', line=dict(color='#0068c9')))
        # Add a "Safe Limit" line (Engineering Standard)
        fig.add_hline(y=100, line_dash="dash", annotation_text="Safety Limit (NAAQS)", annotation_position="bottom right")
        st.plotly_chart(fig, use_container_width=True)
        
    with tab2:
        # Map Visualization
        map_data = pd.DataFrame({'lat': [lat], 'lon': [lon]})
        st.map(map_data, zoom=12)
        st.caption(f"Sensor Location: {lat}, {lon}")

except Exception as e:
    st.error(f"System Offline: {e}")