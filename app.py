import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import time

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Jharkhand Mine Safety Pro",
    page_icon="⛑️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API KEYS
OWM_API_KEY = "2bc68872279fa6ba34acf50fcfa6a559"
# Uses the key you provided previously
GEMINI_API_KEY = "AIzaSyC_W6xvfQ2pgRaPXfIly0ILSfAt7RU-ksE" 

# Configure Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error(f"AI Config Error: {e}")

# --- 2. CUSTOM CSS (UI POLISH) ---
st.markdown("""
<style>
    /* Main Background */
    .stApp { background-color: #f8f9fa; }
    
    /* Card Styling */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        border: 1px solid #e0e0e0;
    }
    
    /* AI Chat Box */
    .ai-response-box {
        background-color: #ffffff;
        border-left: 6px solid #4285F4; /* Google Blue */
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-top: 20px;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: white;
        border-radius: 5px;
        padding-top: 10px;
        padding-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---

def calculate_aqi(pm25):
    """Calculates US AQI from PM2.5 concentration"""
    if pm25 <= 12.0: return ((50 - 0) / (12.0 - 0)) * (pm25 - 0) + 0
    elif pm25 <= 35.4: return ((100 - 51) / (35.4 - 12.1)) * (pm25 - 12.1) + 51
    elif pm25 <= 55.4: return ((150 - 101) / (55.4 - 35.5)) * (pm25 - 35.5) + 101
    elif pm25 <= 150.4: return ((200 - 151) / (150.4 - 55.5)) * (pm25 - 55.5) + 151
    elif pm25 <= 250.4: return ((300 - 201) / (250.4 - 150.5)) * (pm25 - 150.5) + 201
    elif pm25 <= 350.4: return ((400 - 301) / (350.4 - 250.5)) * (pm25 - 250.5) + 301
    else: return ((500 - 401) / (500.4 - 350.5)) * (pm25 - 350.5) + 401

def get_aqi_status(aqi):
    if aqi <= 50: return "Good", "#00e400"
    elif aqi <= 100: return "Moderate", "#ffff00"
    elif aqi <= 150: return "Unhealthy for Sensitive", "#ff7e00"
    elif aqi <= 200: return "Unhealthy", "#ff0000"
    elif aqi <= 300: return "Very Unhealthy", "#8f3f97"
    else: return "Hazardous", "#7e0023"

@st.cache_data(ttl=300)
def get_mining_data(lat, lon):
    try:
        # Current Data
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OWM_API_KEY}"
        data = requests.get(url).json()
        
        # Forecast Data
        fore_url = f"http://api.openweathermap.org/data/2.5/air_pollution/forecast?lat={lat}&lon={lon}&appid={OWM_API_KEY}"
        fore = requests.get(fore_url).json()
        
        pm25 = data['list'][0]['components']['pm2_5']
        pm10 = data['list'][0]['components']['pm10']
        no2 = data['list'][0]['components']['no2']
        
        return {
            "aqi": int(calculate_aqi(pm25)),
            "pm25": pm25,
            "pm10": pm10,
            "no2": no2,
            "forecast": fore['list']
        }
    except:
        return None

def get_ai_advice(location, aqi, pm25, pm10):
    """Calls Gemini API for a safety report"""
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"""
    Act as a Senior Mine Safety Officer in {location}, Jharkhand.
    Current Sensor Readings:
    - AQI: {aqi}
    - PM2.5: {pm25} µg/m³
    - PM10: {pm10} µg/m³
    
    Provide a structured safety report in Markdown format:
    1. **Immediate Hazard Assessment**: (Safe/Warning/Critical)
    2. **Required Action for Workers**: (Masks, stop work, etc.)
    3. **Community Advisory**: (Schools, local villages)
    
    Keep it professional, urgent, and concise (under 100 words).
    """
    response = model.generate_content(prompt)
    return response.text

# --- 4. MAIN LAYOUT ---

# Sidebar
LOCATIONS = {
    "Dhanbad (Coal Capital)": {"lat": 23.7957, "lon": 86.4304},
    "Jharia (Fire Zone)": {"lat": 23.7430, "lon": 86.4116},
    "Bokaro (Thermal/Steel)": {"lat": 23.6693, "lon": 85.9323},
    "Chaibasa (Iron Ore)": {"lat": 22.5526, "lon": 85.8066},
    "Katras (Mining Belt)": {"lat": 23.8136, "lon": 86.2874},
}

with st.sidebar:
    st.title("🎛️ Control Panel")
    selected_loc = st.selectbox("Select Zone", list(LOCATIONS.keys()))
    st.divider()
    st.info("System Online • Satellite Connected")

# Title
st.title(f"🏭 {selected_loc} Safety Grid")

# Fetch Data
data = get_mining_data(LOCATIONS[selected_loc]['lat'], LOCATIONS[selected_loc]['lon'])

if data:
    aqi_text, aqi_color = get_aqi_status(data['aqi'])

    # --- TABS: THE "SECOND SCREEN" SOLUTION ---
    tab1, tab2 = st.tabs(["📊 Live Dashboard", "🤖 AI Safety Officer"])

    # === SCREEN 1: THE DASHBOARD ===
    with tab1:
        # Top Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("PM 2.5 (Fine)", f"{data['pm25']}", delta="Mining Dust")
        with col2:
            st.metric("PM 10 (Coarse)", f"{data['pm10']}", delta="Coal Dust")
        with col3:
            st.metric("NO2 (Gas)", f"{data['no2']}", delta="Explosives")

        st.divider()

        # Gauge & Graph
        c1, c2 = st.columns([1, 2])
        with c1:
            # Professional Gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=data['aqi'],
                title={'text': "<b>AQI LEVEL</b>"},
                gauge={
                    'axis': {'range': [0, 500]},
                    'bar': {'color': aqi_color},
                    'steps': [
                        {'range': [0, 50], 'color': "#00e400"},
                        {'range': [50, 100], 'color': "#ffff00"},
                        {'range': [100, 200], 'color': "#ff0000"},
                        {'range': [200, 500], 'color': "#7e0023"}],
                }
            ))
            fig.update_layout(height=300, margin=dict(t=40,b=20,l=20,r=20))
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            # Trend Graph
            times = [pd.to_datetime(x['dt'], unit='s') for x in data['forecast'][:24]]
            vals = [x['components']['pm2_5'] for x in data['forecast'][:24]]
            df_chart = pd.DataFrame({"Time": times, "PM2.5": vals})
            
            fig2 = px.area(df_chart, x="Time", y="PM2.5", title="24-Hour Pollution Trend", color_discrete_sequence=[aqi_color])
            st.plotly_chart(fig2, use_container_width=True)

    # === SCREEN 2: THE AI OFFICER (GEMINI) ===
    with tab2:
        st.subheader("🤖 AI Safety Officer Analysis")
        st.write("Generate a real-time safety report based on current sensor readings.")
        
        col_ai_1, col_ai_2 = st.columns([1, 3])
        
        with col_ai_1:
            # Context for the user
            st.markdown(f"""
            <div class="metric-card">
                <b>Current Context</b><br>
                📍 {selected_loc}<br>
                🌪️ AQI: {data['aqi']}<br>
                ⚠️ Status: <span style='color:{aqi_color}'><b>{aqi_text}</b></span>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📝 Generate Report", type="primary", use_container_width=True):
                with st.spinner("Contacting Safety HQ..."):
                    # Call the AI Function
                    report = get_ai_advice(selected_loc, data['aqi'], data['pm25'], data['pm10'])
                    st.session_state['ai_report'] = report
        
        with col_ai_2:
            # Display Report
            if 'ai_report' in st.session_state:
                st.markdown(f"""
                <div class="ai-response-box">
                    {st.session_state['ai_report']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("👈 Click 'Generate Report' to analyze current hazards.")

else:
    st.error("Connection Error: Could not fetch sensor data. Check API Key.")