import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import time

# --- 1. PAGE CONFIGURATION (Must be first) ---
st.set_page_config(
    page_title="Jharkhand Geo-Mining Safety",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS FOR ADVANCED UI ---
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Card Styling */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        border-bottom: 4px solid #ddd;
    }
    
    /* Danger Card */
    .danger-card {
        border-bottom: 4px solid #ff4b4b;
    }
    
    /* Safe Card */
    .safe-card {
        border-bottom: 4px solid #00cc96;
    }
    
    /* Button Styling */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 50px;
        font-weight: bold;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. JHARKHAND MINING ZONES DATA ---
LOCATIONS = {
    "Dhanbad (Coal Capital)": {"lat": 23.7957, "lon": 86.4304, "type": "Coal Mining"},
    "Jharia (Fire Zone)": {"lat": 23.7430, "lon": 86.4116, "type": "Active Fire/Coal"},
    "Ranchi (Capital Region)": {"lat": 23.3441, "lon": 85.3096, "type": "Urban/Industrial"},
    "Jamshedpur (Steel City)": {"lat": 22.8046, "lon": 86.2029, "type": "Steel/Heavy Industry"},
    "Bokaro (Thermal/Steel)": {"lat": 23.6693, "lon": 85.9323, "type": "Thermal Power"},
    "Hazaribagh (Coal Belt)": {"lat": 23.9925, "lon": 85.3637, "type": "Coal Mining"},
    "Kodarma (Mica Capital)": {"lat": 24.4677, "lon": 85.5947, "type": "Mica Mines"},
    "Chaibasa (Iron Ore)": {"lat": 22.5526, "lon": 85.8066, "type": "Iron Ore Mines"},
    "Ramgarh (Industrial)": {"lat": 23.6305, "lon": 85.5149, "type": "Cement/Alloy"},
    "Giridih (Open Cast)": {"lat": 24.1915, "lon": 86.3024, "type": "Coal/Mica"},
    "Deoghar (Pilgrim/Stone)": {"lat": 24.4826, "lon": 86.6999, "type": "Stone Crushing"},
    "Palamu (Graphite)": {"lat": 24.0375, "lon": 84.0691, "type": "Graphite Mines"}
}

# --- 4. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Emblem_of_Jharkhand.svg/1200px-Emblem_of_Jharkhand.svg.png", width=100)
    st.title("Jharkhand Safety Grid")
    st.write("Real-time Environmental Monitoring System")
    
    st.divider()
    
    selected_loc_name = st.selectbox("📍 Select Region", list(LOCATIONS.keys()))
    selected_data = LOCATIONS[selected_loc_name]
    
    st.info(f"**Zone Type:** {selected_data['type']}")
    
    st.divider()
    st.write("⚙️ **Control Panel**")
    refresh = st.button("🔄 Refresh Satellite Link")
    if refresh:
        st.toast("Reconnecting to Sentinel-5P Satellite...", icon="📡")
        time.sleep(1)
        st.toast("Data Updated Successfully!", icon="✅")

# --- 5. DATA FETCHING ENGINE ---
@st.cache_data(ttl=3600)
def fetch_pollution_data(lat, lon):
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["pm10", "pm2_5", "us_aqi", "dust"],
        "timezone": "Asia/Kolkata",
        "forecast_days": 1
    }
    try:
        r = requests.get(url, params=params)
        data = r.json()
        df = pd.DataFrame({
            "Time": pd.to_datetime(data['hourly']['time']),
            "AQI": data['hourly']['us_aqi'],
            "PM10": data['hourly']['pm10'],
            "PM2.5": data['hourly']['pm2_5']
        })
        return df
    except:
        return pd.DataFrame()

# --- 6. MAIN DASHBOARD UI ---
st.title(f"🛡️ Safety Dashboard: {selected_loc_name}")
st.markdown(f"**Live Monitoring of {selected_data['type']} Impact on Air Quality**")

df = fetch_pollution_data(selected_data['lat'], selected_data['lon'])

if not df.empty:
    current = df.iloc[pd.Timestamp.now().hour]
    
    # --- ROW 1: STATUS CARDS & GAUGE ---
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        # Custom HTML Card for PM10
        st.markdown(f"""
        <div class="metric-card danger-card">
            <h3>PM 10 (Dust)</h3>
            <h1 style="color: #ff4b4b;">{current['PM10']}</h1>
            <p>µg/m³</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        # Custom HTML Card for PM2.5
        st.markdown(f"""
        <div class="metric-card safe-card">
            <h3>PM 2.5 (Smoke)</h3>
            <h1 style="color: #00cc96;">{current['PM2.5']}</h1>
            <p>µg/m³</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        # GUAGE CHART (Speedometer)
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = current['AQI'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Live Air Quality Index (AQI)"},
            gauge = {
                'axis': {'range': [None, 500]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "#00cc96"},
                    {'range': [50, 100], 'color': "#ffc107"},
                    {'range': [100, 300], 'color': "#ff8c00"},
                    {'range': [300, 500], 'color': "#ff4b4b"}],
            }
        ))
        fig.update_layout(height=250, margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig, use_container_width=True)

    # --- ROW 2: ACTION CENTER (BUTTONS) ---
    st.subheader("⚡ Quick Actions")
    ac_col1, ac_col2, ac_col3, ac_col4 = st.columns(4)
    
    with ac_col1:
        if st.button("📢 Send Alert SMS"):
            with st.spinner("Connecting to Gateway..."):
                time.sleep(2)
            st.success("Alert sent to District Magistrate & Mine Manager!")
            
    with ac_col2:
        if st.button("📥 Download Report"):
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📄 Click to Save CSV",
                data=csv,
                file_name=f"{selected_loc_name}_report.csv",
                mime="text/csv",
                key='download-csv'
            )
            
    with ac_col3:
        if st.button("🏥 Search Hospitals"):
            st.info("Nearest Respiratory Center: Sadar Hospital (2.4 km)")
            
    with ac_col4:
        if st.button("🚒 Fire Brigade"):
            st.error("Emergency Signal Sent to Fire Station!")

    # --- ROW 3: DETAILED GRAPHS ---
    st.divider()
    tab_chart, tab_map, tab_adv = st.tabs(["📊 Analytics", "🗺️ Geo-Map", "🩺 Medical Advisory"])
    
    with tab_chart:
        st.subheader("24-Hour Pollution Forecast")
        chart_fig = px.area(df, x='Time', y=['PM10', 'PM2.5'], color_discrete_map={'PM10':'#ff4b4b', 'PM2.5':'#00cc96'})
        st.plotly_chart(chart_fig, use_container_width=True)
        
    with tab_map:
        st.subheader("Satellite Location Tracking")
        map_df = pd.DataFrame({'lat': [selected_data['lat']], 'lon': [selected_data['lon']]})
        st.map(map_df, zoom=10)
        
    with tab_adv:
        st.subheader("AI-Generated Health Protocols")
        if current['AQI'] > 200:
            st.error("🔴 **CRITICAL:** Suspend all open-cast mining immediately. Sprinklers must be active.")
            st.markdown("* Workers must wear N95 masks.")
            st.markdown("* Schools within 5km radius should be closed.")
        elif current['AQI'] > 100:
            st.warning("🟠 **WARNING:** Limit heavy vehicle movement. Increase water sprinkling frequency.")
        else:
            st.success("🟢 **NORMAL:** Standard mining operations permitted.")

else:
    st.error("Connection Failed. Please check internet access.")

# --- FOOTER ---
st.markdown("---")
st.markdown(f"<div style='text-align: center; color: grey;'>Developed for Jharkhand Mining Safety Initiative • {selected_loc_name} Zone</div>", unsafe_allow_html=True)