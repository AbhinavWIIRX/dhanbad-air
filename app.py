import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import time

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Jharkhand Mine Safety Pro",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. ADVANCED SETUP ---
API_KEY = "2bc68872279fa6ba34acf50fcfa6a559"
BASE_URL = "http://api.openweathermap.org/data/2.5/air_pollution"

# --- 3. ALGORITHM: CALCULATE REAL AQI (0-500 Scale) ---
# This makes your project technically "Advanced" 
def calculate_aqi(pm25):
    # Standard breakpoints for PM2.5 (US EPA Standard)
    if pm25 <= 12.0:
        return ((50 - 0) / (12.0 - 0)) * (pm25 - 0) + 0
    elif pm25 <= 35.4:
        return ((100 - 51) / (35.4 - 12.1)) * (pm25 - 12.1) + 51
    elif pm25 <= 55.4:
        return ((150 - 101) / (55.4 - 35.5)) * (pm25 - 35.5) + 101
    elif pm25 <= 150.4:
        return ((200 - 151) / (150.4 - 55.5)) * (pm25 - 55.5) + 151
    elif pm25 <= 250.4:
        return ((300 - 201) / (250.4 - 150.5)) * (pm25 - 150.5) + 201
    elif pm25 <= 350.4:
        return ((400 - 301) / (350.4 - 250.5)) * (pm25 - 250.5) + 301
    else:
        return ((500 - 401) / (500.4 - 350.5)) * (pm25 - 350.5) + 401

def get_aqi_status(aqi):
    if aqi <= 50: return "Good", "#00e400"        # Green
    elif aqi <= 100: return "Moderate", "#ffff00" # Yellow
    elif aqi <= 150: return "Unhealthy for Sensitive", "#ff7e00" # Orange
    elif aqi <= 200: return "Unhealthy", "#ff0000" # Red
    elif aqi <= 300: return "Very Unhealthy", "#8f3f97" # Purple
    else: return "Hazardous", "#7e0023"           # Maroon

# --- 4. CSS STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; }
    .main-metric {
        background: white;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        text-align: center;
    }
    .big-font { font-size: 3rem !important; font-weight: 800; margin: 0; }
    .sub-font { font-size: 1.2rem; color: #666; }
</style>
""", unsafe_allow_html=True)

# --- 5. SIDEBAR & ZONES ---
LOCATIONS = {
    "Dhanbad (Coal Capital)": {"lat": 23.7957, "lon": 86.4304, "type": "Coal Mining"},
    "Jharia (Fire Zone)": {"lat": 23.7430, "lon": 86.4116, "type": "Active Fire/Coal"},
    "Ranchi (Capital Region)": {"lat": 23.3441, "lon": 85.3096, "type": "Urban/Industrial"},
    "Bokaro (Thermal/Steel)": {"lat": 23.6693, "lon": 85.9323, "type": "Thermal Power"},
    "Chaibasa (Iron Ore)": {"lat": 22.5526, "lon": 85.8066, "type": "Iron Ore Mines"},
    "Katras (Mining Belt)": {"lat": 23.8136, "lon": 86.2874, "type": "Coal Mines"},
}

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3061/3061341.png", width=80)
    st.header("Control Station")
    selected_loc = st.selectbox("Select Zone", list(LOCATIONS.keys()))
    if st.button("🔄 Refresh System"): st.cache_data.clear()

# --- 6. DATA ENGINE ---
@st.cache_data(ttl=300)
def get_mining_data(lat, lon):
    try:
        # Current
        url = f"{BASE_URL}?lat={lat}&lon={lon}&appid={API_KEY}"
        data = requests.get(url).json()
        
        # Forecast
        fore_url = f"{BASE_URL}/forecast?lat={lat}&lon={lon}&appid={API_KEY}"
        fore = requests.get(fore_url).json()
        
        # Process
        pm25 = data['list'][0]['components']['pm2_5']
        pm10 = data['list'][0]['components']['pm10']
        
        # Calculate Advanced AQI
        real_aqi = calculate_aqi(pm25)
        
        return {
            "aqi": int(real_aqi),
            "pm25": pm25,
            "pm10": pm10,
            "no2": data['list'][0]['components']['no2'],
            "forecast": fore['list']
        }
    except:
        return None

# --- 7. UI LAYOUT ---
st.title(f"🏭 {selected_loc}")
st.caption("Real-Time Mining Environmental Monitoring System")

data = get_mining_data(LOCATIONS[selected_loc]['lat'], LOCATIONS[selected_loc]['lon'])

if data:
    aqi_text, aqi_color = get_aqi_status(data['aqi'])
    
    # --- TOP ROW: THE BIG AQI GAUGE ---
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Display the Status Text prominently
        st.markdown(f"""
        <div class="main-metric" style="border-top: 10px solid {aqi_color};">
            <p class="sub-font">Current Air Quality</p>
            <p class="big-font" style="color:{aqi_color};">{data['aqi']}</p>
            <h3>{aqi_text}</h3>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        # Professional Gauge Chart
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = data['aqi'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "<b>AQI METER (0-500)</b>", 'font': {'size': 20}},
            gauge = {
                'axis': {'range': [0, 500], 'tickwidth': 1, 'tickcolor': "black"},
                'bar': {'color': aqi_color},
                'steps': [
                    {'range': [0, 50], 'color': "#00e400"},
                    {'range': [50, 100], 'color': "#ffff00"},
                    {'range': [100, 150], 'color': "#ff7e00"},
                    {'range': [150, 200], 'color': "#ff0000"},
                    {'range': [200, 300], 'color': "#8f3f97"},
                    {'range': [300, 500], 'color': "#7e0023"}],
            }
        ))
        fig.update_layout(height=250, margin=dict(t=30,b=10,l=10,r=10))
        st.plotly_chart(fig, use_container_width=True)

    # --- ROW 2: POLLUTANT BREAKDOWN ---
    st.subheader("🧪 Pollutant Concentration")
    m1, m2, m3 = st.columns(3)
    m1.metric("PM 2.5 (Fine Dust)", f"{data['pm25']} µg/m³", delta="Mining Dust")
    m2.metric("PM 10 (Coarse Dust)", f"{data['pm10']} µg/m³", delta="Coal Dust")
    m3.metric("NO2 (Explosives Gas)", f"{data['no2']} µg/m³", delta="Blasting Fumes")

    # --- ROW 3: FORECAST GRAPH ---
    st.divider()
    st.subheader("📈 24-Hour Prediction Curve")
    
    # Prepare data for graph
    times = [pd.to_datetime(x['dt'], unit='s') for x in data['forecast'][:24]]
    pm25_vals = [x['components']['pm2_5'] for x in data['forecast'][:24]]
    
    chart_data = pd.DataFrame({"Time": times, "PM2.5": pm25_vals})
    
    fig2 = px.area(chart_data, x="Time", y="PM2.5", color_discrete_sequence=[aqi_color])
    fig2.add_hline(y=60, line_dash="dash", annotation_text="Safety Limit")
    st.plotly_chart(fig2, use_container_width=True)
    
    # --- ROW 4: MAP ---
    st.map(pd.DataFrame({'lat': [LOCATIONS[selected_loc]['lat']], 'lon': [LOCATIONS[selected_loc]['lon']]}))

else:
    st.error("Server Connection Error. Please wait 30 minutes for API Key activation.")