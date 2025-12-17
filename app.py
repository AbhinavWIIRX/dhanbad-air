import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import time

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Jharkhand Geo-Mining Safety",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CONFIGURATION & NEW API KEY ---
# Updated with the key you provided
API_KEY = "2bc68872279fa6ba34acf50fcfa6a559"  
BASE_URL = "http://api.openweathermap.org/data/2.5/air_pollution"

# --- 3. CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        border-bottom: 4px solid #ddd;
    }
    .danger-card { border-bottom: 4px solid #ff4b4b; }
    .safe-card { border-bottom: 4px solid #00cc96; }
    .stButton>button { width: 100%; border-radius: 8px; height: 50px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 4. JHARKHAND MINING ZONES ---
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

# --- 5. SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Emblem_of_Jharkhand.svg/1200px-Emblem_of_Jharkhand.svg.png", width=100)
    st.title("Jharkhand Safety Grid")
    st.write("Real-time OpenWeatherMap Link")
    st.divider()
    selected_loc_name = st.selectbox("📍 Select Region", list(LOCATIONS.keys()))
    selected_data = LOCATIONS[selected_loc_name]
    st.info(f"**Zone Type:** {selected_data['type']}")
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()

# --- 6. DATA FETCHING (Improved Error Handling) ---
@st.cache_data(ttl=300)
def fetch_owm_data(lat, lon):
    try:
        # 1. Get Current Data
        current_url = f"{BASE_URL}?lat={lat}&lon={lon}&appid={API_KEY}"
        curr_resp = requests.get(current_url).json()
        
        # DEBUG CHECK: If API returns error message
        if 'message' in curr_resp:
            st.error(f"OpenWeatherMap Error: {curr_resp['message']}")
            return None, pd.DataFrame()
            
        # 2. Get Forecast Data (for graphs)
        forecast_url = f"{BASE_URL}/forecast?lat={lat}&lon={lon}&appid={API_KEY}"
        fore_resp = requests.get(forecast_url).json()
        
        # Process Current
        current_data = {
            "aqi": curr_resp['list'][0]['main']['aqi'], # 1 to 5 scale
            "pm2_5": curr_resp['list'][0]['components']['pm2_5'],
            "pm10": curr_resp['list'][0]['components']['pm10'],
            "co": curr_resp['list'][0]['components']['co'],
            "no2": curr_resp['list'][0]['components']['no2']
        }
        
        # Process Forecast (Next 24 hours)
        forecast_list = []
        for item in fore_resp['list'][:24]:
            forecast_list.append({
                "Time": pd.to_datetime(item['dt'], unit='s'),
                "PM2.5": item['components']['pm2_5'],
                "PM10": item['components']['pm10'],
                "NO2": item['components']['no2']
            })
        
        return current_data, pd.DataFrame(forecast_list)
    except Exception as e:
        st.error(f"System Error: {e}")
        return None, pd.DataFrame()

# --- 7. MAIN DASHBOARD ---
st.title(f"🛡️ Safety Dashboard: {selected_loc_name}")
st.markdown(f"**Live Monitoring via OpenWeatherMap API**")

current, df_forecast = fetch_owm_data(selected_data['lat'], selected_data['lon'])

if current:
    # --- ROW 1: CARDS ---
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        st.markdown(f"""
        <div class="metric-card danger-card">
            <h3>PM 10 (Dust)</h3>
            <h1 style="color: #ff4b4b;">{current['pm10']}</h1>
            <p>µg/m³</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="metric-card safe-card">
            <h3>PM 2.5 (Fine)</h3>
            <h1 style="color: #00cc96;">{current['pm2_5']}</h1>
            <p>µg/m³</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        # GAUGE for OWM AQI (Scale 1-5)
        aqi_labels = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}
        aqi_val = current['aqi']
        aqi_text = aqi_labels.get(aqi_val, "Unknown")
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = aqi_val,
            title = {'text': f"Air Quality Index (1-5 Scale)<br><span style='font-size:0.8em;color:gray'>{aqi_text}</span>"},
            gauge = {
                'axis': {'range': [0, 5], 'tickvals': [1,2,3,4,5]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 1.5], 'color': "#00cc96"}, # Good
                    {'range': [1.5, 3.5], 'color': "#ffc107"}, # Moderate
                    {'range': [3.5, 5], 'color': "#ff4b4b"}], # Poor
            }
        ))
        fig.update_layout(height=250, margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig, use_container_width=True)

    # --- ROW 2: ACTIONS ---
    st.subheader("⚡ Quick Actions")
    ac1, ac2, ac3, ac4 = st.columns(4)
    with ac1: 
        if st.button("📢 Alert"): st.success("Alert Sent!")
    with ac2:
        if st.button("📥 Report"):
            if not df_forecast.empty:
                st.download_button("Save CSV", df_forecast.to_csv().encode('utf-8'), "report.csv", "text/csv")
    with ac3: st.button("🏥 Hospitals")
    with ac4: st.button("🚒 Emergency")

    # --- ROW 3: GRAPHS & MAP ---
    st.divider()
    tab1, tab2, tab3 = st.tabs(["📊 Forecast Trend", "🗺️ Map Location", "🩺 Health Advice"])
    
    with tab1:
        if not df_forecast.empty:
            fig = px.area(df_forecast, x='Time', y=['PM10', 'PM2.5', 'NO2'], 
                          title="24-Hour Pollutant Forecast",
                          color_discrete_map={'PM10':'#ff4b4b', 'PM2.5':'#00cc96', 'NO2':'#ffa500'})
            st.plotly_chart(fig, use_container_width=True)
            
    with tab2:
        st.map(pd.DataFrame({'lat': [selected_data['lat']], 'lon': [selected_data['lon']]}), zoom=12)
        
    with tab3:
        if current['aqi'] >= 4:
            st.error("🔴 **HIGH RISK:** Air quality is Poor/Very Poor. Wear masks and stop outdoor work.")
        elif current['aqi'] == 3:
            st.warning("🟠 **MODERATE:** Sensitive groups should avoid exertion.")
        else:
            st.success("🟢 **SAFE:** Air quality is Good or Fair.")

elif API_KEY == "YOUR_API_KEY":
    st.warning("⚠️ Please replace 'YOUR_API_KEY' in the code with your actual OpenWeatherMap API Key.")
else:
    st.error("Could not connect to OpenWeatherMap. If you just created the key, please wait 30 minutes for activation.")