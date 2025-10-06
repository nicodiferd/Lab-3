# Real-Time AQI Dashboard with Streamlit and AirNow API
# This app displays AQI data for California cities and allows ZIP code lookup
# Additional Feature: Pollutant Breakdown showing all pollutant levels

# Import Libraries
import os
import requests
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go

POLLUTANT_DICTIONARY = {
    "PM2.5": {
        "label": "PM2.5 (Fine Particles)",
        "definition": (
            "Tiny pieces of soot, smoke, or dust that are small enough to travel deep "
            "into your lungs."
        ),
        "example": (
            "Wildfire smoke or exhaust from diesel trucks releases PM2.5 into the air."
        ),
    },
    "PM10": {
        "label": "PM10 (Dust Particles)",
        "definition": (
            "Slightly larger dust and dirt particles that you can breathe in even though "
            "you cannot see them."
        ),
        "example": (
            "Construction work, unpaved roads, or windy days on farm fields lift PM10 "
            "into the air."
        ),
    },
    "O3": {
        "label": "O3 (Ground-Level Ozone)",
        "definition": (
            "A gas that forms near the ground when sunlight reacts with pollution from "
            "vehicles and factories."
        ),
        "example": (
            "On hot sunny afternoons, car exhaust and industrial fumes react in sunlight "
            "to create ozone."
        ),
    },
    "NO2": {
        "label": "NO2 (Nitrogen Dioxide)",
        "definition": (
            "A reddish-brown gas made when fuel burns at high temperatures; it can "
            "irritate your lungs."
        ),
        "example": (
            "Traffic on busy highways and power plants that burn fuel release NO2."
        ),
    },
    "SO2": {
        "label": "SO2 (Sulfur Dioxide)",
        "definition": (
            "A sharp, biting gas produced when fuels that contain sulfur are burned."
        ),
        "example": (
            "Coal-fired power plants and metal smelters release SO2 into the air."
        ),
    },
    "CO": {
        "label": "CO (Carbon Monoxide)",
        "definition": (
            "A colorless, odorless gas formed when fuel does not burn completely."
        ),
        "example": (
            "Idling cars, furnaces, or gas-powered tools in enclosed spaces can build up "
            "CO."
        ),
    },
}

# Page configuration
st.set_page_config(page_title="AQI Dashboard", page_icon="🌍", layout="wide")

# Streamlit app display
st.title("🌍 Real-Time Air Quality Index (AQI) Dashboard")
st.markdown("Track air quality across California and look up AQI data by ZIP code")

# Load environment variables from .env file
load_dotenv()

# API Key Input
st.sidebar.header("🔑 API Configuration")
default_api_key = os.getenv("AQI_API_KEY", "")
api_key = st.sidebar.text_input(
    "Enter your AirNow API Key",
    value=default_api_key,
    type="password",
    help="Get your free API key from https://docs.airnowapi.org/"
)

if not api_key:
    st.warning("⚠️ Please enter your AirNow API key in the sidebar to continue.")
    st.info("Don't have an API key? Sign up for free at [AirNow API](https://docs.airnowapi.org/)")
    st.stop()

# ------------------------------------------------------------------
# Helper Function: Get color based on AQI category
# ------------------------------------------------------------------
def get_aqi_color(category):
    """Return color based on AQI category"""
    color_map = {
        'Good': 'green',
        'Moderate': 'yellow',
        'Unhealthy for Sensitive Groups': 'orange',
        'Unhealthy': 'red',
        'Very Unhealthy': 'purple',
        'Hazardous': 'darkred'
    }
    return color_map.get(category, 'gray')

# ------------------------------------------------------------------
# Helper Function: Get AQI category from value
# ------------------------------------------------------------------
def get_aqi_category(aqi):
    """Return AQI category based on AQI value"""
    if aqi is None:
        return "Unknown"
    elif aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"

# ------------------------------------------------------------------
# Function 1: Get AQI data for a given location using the AirNow API
# ------------------------------------------------------------------
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_aqi(zip_code, api_key):
    """Fetch AQI data from AirNow API for a given ZIP code"""
    base_url = "https://www.airnowapi.org/aq/observation/zipCode/current/"
    parameters = {
        "format": "application/json",
        "zipCode": zip_code,
        "distance": "25",
        "API_KEY": api_key
    }
    try:
        response = requests.get(base_url, params=parameters, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# ------------------------------------------------------------------
# Function 2: Get AQI data for all California cities in the DataFrame
# ------------------------------------------------------------------
@st.cache_data(ttl=3600)
def get_california_aqi(ca_df, api_key):
    """Fetch AQI data for all California cities"""
    overall_aqi = []
    overall_category = []
    latitudes = []
    longitudes = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, row in ca_df.iterrows():
        status_text.text(f"Fetching AQI data for {row['City']}... ({idx + 1}/{len(ca_df)})")
        progress_bar.progress((idx + 1) / len(ca_df))

        aqi_data = get_aqi(row['ZIP Code'], api_key)

        if aqi_data and len(aqi_data) > 0:
            # Get the maximum AQI among all pollutants
            max_aqi = max(obs['AQI'] for obs in aqi_data)
            max_obs = max(aqi_data, key=lambda x: x['AQI'])

            overall_aqi.append(max_aqi)
            overall_category.append(max_obs['Category']['Name'])
            latitudes.append(max_obs['Latitude'])
            longitudes.append(max_obs['Longitude'])
        else:
            overall_aqi.append(None)
            overall_category.append(None)
            latitudes.append(None)
            longitudes.append(None)

    progress_bar.empty()
    status_text.empty()

    ca_df['AQI'] = overall_aqi
    ca_df['AQI Category'] = overall_category
    ca_df['Latitude'] = latitudes
    ca_df['Longitude'] = longitudes

    return ca_df

# ------------------------------------------------------------------
# Function 3: Create a folium map with color-coded markers
# ------------------------------------------------------------------
@st.cache_data
def create_california_map(aqi_data):
    """Create an interactive Folium map with AQI markers"""
    # Create a folium map centered in California
    m = folium.Map(location=[36.7783, -119.4179], zoom_start=6)

    # Add markers to the map for each city in California
    for _, row in aqi_data.iterrows():
        if pd.notna(row['Latitude']) and pd.notna(row['Longitude']):
            # Get color based on category
            marker_color = get_aqi_color(row['AQI Category'])

            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                icon=folium.Icon(color=marker_color, icon='info-sign'),
                popup=folium.Popup(
                    f"""
                    <b>City:</b> {row['City']}<br>
                    <b>ZIP Code:</b> {row['ZIP Code']}<br>
                    <b>AQI:</b> {row['AQI']}<br>
                    <b>Category:</b> {row['AQI Category']}
                    """,
                    max_width=250
                )
            ).add_to(m)

    return m

# ------------------------------------------------------------------
# Helper Function: Render pollutant dictionary
# ------------------------------------------------------------------
def render_pollutant_dictionary(container=None, *, show_header=True):
    """Display plain-language pollutant definitions and examples."""
    container = container or st

    if show_header:
        container.subheader("📘 Pollutant Dictionary")

    container.markdown(
        "Use this quick dictionary to understand what each pollutant means and how it "
        "usually gets into the air."
    )

    for info in POLLUTANT_DICTIONARY.values():
        container.markdown(
            f"**{info['label']}**\n"
            f"Definition: {info['definition']}\n"
            f"How it gets into the air: {info['example']}\n"
        )

# ------------------------------------------------------------------
# Function 4: Display pollutant breakdown (ADDITIONAL FEATURE)
# ------------------------------------------------------------------
def display_pollutant_breakdown(aqi_data):
    """Display detailed breakdown of all pollutants - ADDITIONAL FEATURE"""
    st.subheader("🔬 Pollutant Breakdown")
    st.markdown("Detailed information about individual pollutants contributing to the AQI")

    if not aqi_data or len(aqi_data) == 0:
        st.warning("No pollutant data available for this location.")
        return

    # Create columns for each pollutant
    cols = st.columns(len(aqi_data))

    for idx, pollutant in enumerate(aqi_data):
        with cols[idx]:
            param_name = pollutant['ParameterName']
            aqi = pollutant['AQI']
            category = pollutant['Category']['Name']
            color = get_aqi_color(category)

            # Display pollutant card
            st.markdown(f"""
            <div style="padding: 10px; border-radius: 5px; border: 2px solid {color};">
                <h4 style="margin: 0;">{param_name}</h4>
                <p style="font-size: 24px; font-weight: bold; margin: 5px 0;">{aqi}</p>
                <p style="margin: 0; color: {color};">{category}</p>
            </div>
            """, unsafe_allow_html=True)

    # Create a bar chart showing all pollutants
    st.markdown("#### Pollutant Comparison")

    pollutant_names = [p['ParameterName'] for p in aqi_data]
    pollutant_aqis = [p['AQI'] for p in aqi_data]
    pollutant_colors = [get_aqi_color(p['Category']['Name']) for p in aqi_data]

    # Map color names to actual colors for plotly
    color_map = {
        'green': '#00e400',
        'yellow': '#ffff00',
        'orange': '#ff7e00',
        'red': '#ff0000',
        'purple': '#8f3f97',
        'darkred': '#7e0023',
        'gray': '#808080'
    }

    bar_colors = [color_map.get(c, '#808080') for c in pollutant_colors]

    fig = go.Figure(data=[
        go.Bar(
            x=pollutant_names,
            y=pollutant_aqis,
            marker_color=bar_colors,
            text=pollutant_aqis,
            textposition='auto',
        )
    ])

    fig.update_layout(
        title="AQI by Pollutant",
        xaxis_title="Pollutant",
        yaxis_title="AQI Value",
        height=400,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    render_pollutant_dictionary(show_header=True)

# ------------------------------------------------------------------
# MAIN APP LAYOUT
# ------------------------------------------------------------------

# Tabs for different features
tab1, tab2 = st.tabs(["📍 California AQI Map", "🔍 ZIP Code Lookup"])

# Tab 1: California AQI Map
with tab1:
    st.header("California Cities AQI Map")
    st.markdown("Real-time air quality data for major cities across California")

    # Load the California city data
    try:
        ca_df = pd.read_csv("data/california_zip_codes.csv")

        # Get AQI data for California cities
        ca_aqi_df = get_california_aqi(ca_df, api_key)

        # Display summary statistics
        col1, col2, col3, col4 = st.columns(4)

        valid_data = ca_aqi_df[ca_aqi_df['AQI'].notna()]

        with col1:
            st.metric("Cities Monitored", len(valid_data))
        with col2:
            avg_aqi = valid_data['AQI'].mean() if len(valid_data) > 0 else 0
            st.metric("Average AQI", f"{avg_aqi:.0f}")
        with col3:
            max_aqi = valid_data['AQI'].max() if len(valid_data) > 0 else 0
            st.metric("Highest AQI", f"{max_aqi:.0f}")
        with col4:
            good_count = len(valid_data[valid_data['AQI Category'] == 'Good'])
            st.metric("Good Quality", f"{good_count} cities")

        # Display the map
        st.subheader("Interactive Map")
        st_folium(create_california_map(ca_aqi_df), width=None, height=500)

        # Show data table
        with st.expander("📊 View Data Table"):
            display_df = ca_aqi_df[['City', 'ZIP Code', 'AQI', 'AQI Category']].copy()
            display_df = display_df.sort_values('AQI', ascending=False, na_position='last')
            st.dataframe(display_df, use_container_width=True)

    except FileNotFoundError:
        st.error("❌ California ZIP codes CSV file not found. Please ensure 'data/california_zip_codes.csv' exists.")

# Tab 2: ZIP Code Lookup
with tab2:
    st.header("ZIP Code AQI Lookup")
    st.markdown("Enter any U.S. ZIP code to view current air quality data")

    # ZIP code input
    col1, col2 = st.columns([2, 1])

    with col1:
        zip_input = st.text_input(
            "Enter ZIP Code",
            max_chars=5,
            placeholder="e.g., 90210"
        )

    with col2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)

    if search_button and zip_input:
        if len(zip_input) != 5 or not zip_input.isdigit():
            st.error("❌ Please enter a valid 5-digit ZIP code.")
        else:
            with st.spinner(f"Fetching AQI data for ZIP code {zip_input}..."):
                aqi_data = get_aqi(zip_input, api_key)

                if aqi_data and len(aqi_data) > 0:
                    # Get overall AQI (maximum among all pollutants)
                    max_aqi = max(obs['AQI'] for obs in aqi_data)
                    category = get_aqi_category(max_aqi)
                    color = get_aqi_color(category)

                    # Display overall AQI
                    st.success(f"✅ Data retrieved for ZIP code {zip_input}")

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("ZIP Code", zip_input)
                    with col2:
                        st.metric("Overall AQI", max_aqi)
                    with col3:
                        st.markdown(f"**Category:** <span style='color: {color}; font-size: 20px;'>{category}</span>", unsafe_allow_html=True)

                    st.markdown("---")

                    # Display pollutant breakdown (ADDITIONAL FEATURE)
                    display_pollutant_breakdown(aqi_data)

                else:
                    st.warning(f"⚠️ No AQI data available for ZIP code {zip_input}. This could mean:")
                    st.markdown("""
                    - The ZIP code is invalid
                    - There are no monitoring stations within 25 miles
                    - Data is temporarily unavailable
                    """)

# Sidebar information
st.sidebar.markdown("---")
st.sidebar.header("ℹ️ About")
st.sidebar.markdown("""
This dashboard displays real-time Air Quality Index (AQI) data using the AirNow API.

**Features:**
- 📍 California cities AQI map
- 🔍 ZIP code lookup
- 🔬 Pollutant breakdown (additional feature)

**AQI Categories:**
- 🟢 Good (0-50)
- 🟡 Moderate (51-100)
- 🟠 Unhealthy for Sensitive Groups (101-150)
- 🔴 Unhealthy (151-200)
- 🟣 Very Unhealthy (201-300)
- 🔴 Hazardous (301+)
""")

st.sidebar.markdown("---")
st.sidebar.markdown("Data provided by [AirNow API](https://www.airnow.gov/)")
