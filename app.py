import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import time

# --- 1. CONFIGURATION (API KEYS) ---
# Weather Data Key
OWM_API_KEY = "2bc68872279fa6ba34acf50fcfa6a559"
# Gemini AI Key
GEMINI_API_KEY = "AIzaSyC_W6xvfQ2pgRaPXfIly0ILSfAt7RU-ksE"

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# --- 2. PAGE SETUP ---
st.set_page_config(
    page_title="Jharkhand Mine Safety AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 3. CUSTOM CSS (Alarm Colors) ---
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    
    /* AI Report Box */
    .ai-box {
        padding: 20px;
        border-radius: 12px;
        background-color: #ffffff;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    /* Alarm Borders */
    .border-green { border-left: 8px solid #00e400; }
    .border-orange { border-left: 8px solid #ff7e00; }
    .border-red { border-left: 8px solid #ff0000; }
    
    /* Metric Cards */
    .metric-container {
        background: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# --- 4. HELPER FUNCTIONS ---

def calculate_aqi(pm25):
    """Calculates US AQI from PM2.5 concentration"""
    if pm25 <= 12.0: return ((50 - 0) / (12.0 - 0)) * (pm25 - 0) + 0
    elif pm25 <= 35.4: return ((100 - 51) / (35.4 - 12.1)) * (pm25 - 12.1) + 51
    elif pm25 <= 55.4: return ((150 - 101) / (55.4 - 35.5)) * (pm25 - 35.5) + 101
    elif pm25 <= 150.4: return ((200 - 151) / (150.4 - 55.5)) * (pm25 - 55.5) + 151
    elif pm25 <= 250.4: return ((300 - 201) / (250.4 - 150.5)) * (pm25 - 150.5) + 201
    elif pm25 <= 350.4: return ((400 - 301) / (350.4 - 250.5)) * (pm25 - 250.5) + 301
    else: return ((500 - 401) / (500.4 - 350.5)) * (pm25 - 350.5) + 401

def get_aqi_color(aqi):
    """Returns color hex and CSS class based on AQI"""
    if aqi <= 50: return "#00e400", "border-green", "Safe"
    elif aqi <= 100: return "#ffff00", "border-orange", "Moderate"
    elif aqi <= 150: return "#ff7e00", "border-orange", "Unhealthy for Sensitive"
    elif aqi <= 200: return "#ff0000", "border-red", "Unhealthy"
    elif aqi <= 300: return "#8f3f97", "border-red", "Very Unhealthy"
    else: return "#7e0023", "border-red", "Hazardous"

@st.cache_data(ttl=600)
def get_sensor_data(lat, lon):
    try:
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OWM_API_KEY}"
        data = requests.get(url).json()
        
        # Forecast for graph
        fore_url = f"http://api.openweathermap.org/data/2.5/air_pollution/forecast?lat={lat}&lon={lon}&appid={OWM_API_KEY}"
        fore_data = requests.get(fore_url).json()
        
        pm25 = data['list'][0]['components']['pm2_5']
        pm10 = data['list'][0]['components']['pm10']
        no2 = data['list'][0]['components']['no2']
        
        aqi_score = int(calculate_aqi(pm25))
        
        return {
            "aqi": aqi_score,
            "pm25": pm25,
            "pm10": pm10,
            "no2": no2,
            "forecast": fore_data['list']
        }
    except:
        return None

def generate_ai_report(location, aqi, pm25, pm10):
    """Uses Gemini to generate a safety report"""
    try:
        model = genai.GenerativeModel('gemini-pro')
        prompt = (
            f"Act as a strict Mine Safety Officer in {location}, Jharkhand. "
            f"Current stats: AQI is {aqi}, PM2.5 is {pm25}, PM10 is {pm10}. "
            "Write a short, urgent safety advisory. "
            "Include: 1. Health Risk. 2. Instructions for Mine Workers. 3. Advice for local schools. "
            "Keep it under 60 words. Use emojis."
        )
        response = model.generate_content(prompt)
        return response.text
    except:
        return "AI System Busy. Please rely on standard operating procedures."

# --- 5. SIDEBAR & LOCATIONS ---
LOCATIONS = {
    "Dhanbad (Coal Capital)": {"lat": 23.7957, "lon": 86.4304},
    "Jharia (Fire Zone)": {"lat": 23.7430, "lon": 86.4116},
    "Bokaro (Thermal)": {"lat": 23.6693, "lon": 85.9323},
    "Chaibasa (Iron Ore)": {"lat": 22.5526, "lon": 85.8066},
    "Kodarma (Mica)": {"lat": 24.4677, "lon": 85.5947}
}

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712009.png", width=80)
    st.title("Safety Grid")
    selected_loc = st.selectbox("Select Zone", list(LOCATIONS.keys()))
    st.divider()
    st.caption("Powered by Google Gemini & OpenWeather")

# --- 6. MAIN DASHBOARD ---
st.title(f"🏭 Safety Dashboard: {selected_loc}")

# Fetch Data
data = get_sensor_data(LOCATIONS[selected_loc]['lat'], LOCATIONS[selected_loc]['lon'])

if data:
    aqi = data['aqi']
    hex_color, css_class, status_text = get_aqi_color(aqi)
    
    # --- SECTION 1: AI SAFETY OFFICER (The New Feature) ---
    st.subheader("🤖 AI Safety Officer's Report")
    
    # Dynamic styling for the AI box
    ai_box_html = f"""
    <div class="ai-box {css_class}">
        <h3 style="color:{hex_color}; margin-top:0;">⚠ Status: {status_text} (AQI: {aqi})</h3>
        <p><strong>System Analysis:</strong> Generating live report from Gemini AI...</p>
    </div>
    """
    
    # We use a placeholder to show the report loading
    report_container = st.empty()
    
    # Generate the AI text (only if not cached)
    if 'last_loc' not in st.session_state or st.session_state.last_loc != selected_loc:
        with st.spinner('AI Officer is analyzing sensor data...'):
            ai_text = generate_ai_report(selected_loc, aqi, data['pm25'], data['pm10'])
            st.session_state.ai_report = ai_text
            st.session_state.last_loc = selected_loc
    
    # Update the box with the real AI text
    report_container.markdown(f"""
    <div class="ai-box {css_class}">
        <h3 style="color:{hex_color}; margin-top:0;">⚠ Status: {status_text} (AQI: {aqi})</h3>
        <p style="font-size:18px;">{st.session_state.ai_report}</p>
    </div>
    """, unsafe_allow_html=True)

    # --- SECTION 2: LIVE METRICS ---
    c1, c2, c3 = st.columns(3)
    c1.metric("PM 2.5 (Fine Dust)", f"{data['pm25']} µg/m³", delta="Dangerous" if data['pm25'] > 60 else "Normal", delta_color="inverse")
    c2.metric("PM 10 (Coal Dust)", f"{data['pm10']} µg/m³", delta="High" if data['pm10'] > 100 else "Normal", delta_color="inverse")
    c3.metric("NO2 (Explosive Gas)", f"{data['no2']} µg/m³")

    # --- SECTION 3: DOWNLOAD REPORT ---
    st.subheader("📋 Data Logs")
    
    # Create a DataFrame for the download
    forecast_df = pd.DataFrame([
        {
            "Time": pd.to_datetime(x['dt'], unit='s'),
            "PM2.5": x['components']['pm2_5'],
            "PM10": x['components']['pm10'],
            "AQI_Predicted": calculate_aqi(x['components']['pm2_5'])
        } for x in data['forecast']
    ])
    
    col_dl1, col_dl2 = st.columns([3, 1])
    with col_dl1:
        st.caption("Download the official 24-hour sensor forecast log for compliance records.")
    with col_dl2:
        csv = forecast_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Official Report",
            data=csv,
            file_name=f"{selected_loc}_Safety_Log.csv",
            mime="text/csv"
        )

    # --- SECTION 4: VISUALS ---
    tab1, tab2 = st.tabs(["📈 24h Trend Graph", "🧭 AQI Gauge"])
    
    with tab1:
        fig = px.area(forecast_df, x='Time', y=['PM10', 'PM2.5'], color_discrete_map={'PM10': hex_color, 'PM2.5': '#cccccc'})
        st.plotly_chart(fig, use_container_width=True)
        
    with tab2:
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = aqi,
            title = {'text': "Live Danger Level"},
            gauge = {'axis': {'range': [0, 500]}, 'bar': {'color': hex_color}}
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

else:
    st.error("Server Disconnected. Please check API Keys.")