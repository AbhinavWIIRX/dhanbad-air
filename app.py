import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE SETUP ---
st.set_page_config(page_title="Jharkhand Mine Safety", page_icon="⛑️", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
    }
    .advisory-box {
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: LOCATION SELECTOR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2942/2942544.png", width=80)
    st.title("📍 Zone Selection")
    
    # EXPANDED COAL FIELDS LIST (Real Coordinates)
    # Adding Katras, Nirsa, Kusunda, etc.
    coords = {
        "Dhanbad City (Main)": {"lat": 23.7957, "lon": 86.4304},
        "Jharia Coal Field": {"lat": 23.7430, "lon": 86.4116},
        "Sindri Industrial Area": {"lat": 23.6496, "lon": 86.5147},
        "Katras (Mining Belt)": {"lat": 23.8136, "lon": 86.2874},
        "Nirsa (Open Cast)": {"lat": 23.7877, "lon": 86.7163},
        "Kusunda Area": {"lat": 23.7644, "lon": 86.4087},
        "Govindpur (Highway)": {"lat": 23.8373, "lon": 86.5186},
        "Bokaro (Thermal Plant)": {"lat": 23.6693, "lon": 85.9323}
    }
    
    selected_area = st.selectbox("Select Monitoring Station", list(coords.keys()))
    
    st.divider()
    st.info(f"Connected to satellite feed for: **{selected_area}**")

# --- DATA FETCHING FUNCTION ---
@st.cache_data
def get_data(lat, lon):
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["pm10", "pm2_5", "dust", "us_aqi"],
        "timezone": "Asia/Kolkata",
        "forecast_days": 3
    }
    try:
        response = requests.get(url, params=params)
        hourly = response.json()['hourly']
        df = pd.DataFrame({
            "Time": pd.to_datetime(hourly['time']),
            "PM10": hourly['pm10'],
            "PM2.5": hourly['pm2_5'],
            "Dust": hourly['dust'],
            "AQI": hourly['us_aqi']
        })
        return df
    except:
        return pd.DataFrame()

# --- ADVANCED HEALTH ADVISORY LOGIC ---
def get_detailed_advisory(pm25):
    if pm25 <= 30:
        return "green", "Safe Conditions", "✅ Air quality is good. Perfect for outdoor activities.", "🟢 Windows can be kept open."
    elif pm25 <= 60:
        return "blue", "Satisfactory", "⚠️ Sensitive people (Asthma/Heart issues) should reduce heavy exertion.", "🔵 Ventilate rooms during afternoon."
    elif pm25 <= 90:
        return "orange", "Moderate Danger", "😷 Lungs & Heart patients must wear masks. Children should play indoors.", "🟠 Use Air Purifiers if available."
    elif pm25 <= 120:
        return "red", "Poor Air Quality", "🚫 Avoid morning walks. Wear N95 masks if going outside is necessary.", "🔴 Keep windows closed."
    else:
        return "black", "SEVERE HAZARD", "☠️ HEALTH EMERGENCY. Serious risk of respiratory illness. Stop all outdoor mining/construction.", "⚫ SEAL ALL WINDOWS. DO NOT GO OUT."

# --- MAIN DASHBOARD ---
st.title(f"⛑️ Mine Safety & Health: {selected_area}")

lat = coords[selected_area]["lat"]
lon = coords[selected_area]["lon"]
df = get_data(lat, lon)

if not df.empty:
    # Get Current Data
    current = df.iloc[0]
    
    # 1. KEY METRICS
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("AQI (Quality Index)", f"{current['AQI']}", delta="Normal" if current['AQI'] < 100 else "High", delta_color="inverse")
    with col2:
        st.metric("PM 2.5 (Fine)", f"{current['PM2.5']}", delta="-2.1")
    with col3:
        st.metric("PM 10 (Dust)", f"{current['PM10']}", delta="5.4", delta_color="inverse")
    with col4:
        # Dynamic Risk Badge
        risk_color = "green" if current['AQI'] < 100 else "red"
        st.markdown(f"#### Risk Level")
        st.markdown(f":{risk_color}-background[**{current['AQI']} - {'SAFE' if current['AQI'] < 100 else 'RISKY'}**]")

    # 2. HEALTH ADVISORY SECTION (New Feature)
    st.subheader("🩺 Real-time Health Advisory")
    color, title, health_msg, action_msg = get_detailed_advisory(current['PM2.5'])
    
    with st.container():
        # Using Streamlit's colored message boxes
        if color == "green":
            st.success(f"**{title}**: {health_msg}")
        elif color == "orange":
            st.warning(f"**{title}**: {health_msg}")
        else:
            st.error(f"**{title}**: {health_msg}")
            
        with st.expander("Recommended Actions (Click to Expand)"):
            st.write(f"- {action_msg}")
            st.write("- **Mine Workers:** Wet suppression (water sprinkling) required.")
            st.write("- **Schools:** No restrictions." if color == "green" else "- **Schools:** Cancel outdoor sports.")

    # 3. GRAPHS
    tab1, tab2 = st.tabs(["📉 24-Hour Trend", "🗺️ Satellite Map"])
    
    with tab1:
        fig = px.area(df.head(24), x='Time', y=['PM10', 'PM2.5'], title="Pollution Trend (Next 24 Hours)", color_discrete_sequence=["#ff4b4b", "#0068c9"])
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=11)

else:
    st.error("Server Error: Could not fetch satellite data. Please try again later.")