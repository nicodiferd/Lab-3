# Folium map to visualize AQI data for California cities
# Here, AQI values are fetched from an API and displayed on a Folium map using Streamlit

# Import Libraries
import os
import requests
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Load environment variables from .env file
load_dotenv()

# Read the API key
api_key = os.getenv("AIRNOW_API_KEY")

# Load the California city names, zip codes, and coordinates from CSV file
ca_df = pd.read_csv("data/california_zip_codes.csv")

# ------------------------------------------------------------------
# Function 1: Get AQI data for a given location using the AirNow API
# ------------------------------------------------------------------
@st.cache_data
def get_aqi(zip_code):
    base_url = "https://www.airnowapi.org/aq/observation/zipCode/current/"
    parameters = {
        "format": "application/json",
        "zipCode": zip_code,
        "distance": "25",
        "API_KEY": api_key
    }
    response = requests.get(base_url, params = parameters)
    
    if response.status_code == 200:
        return response.json()
    else:
        return None

# ------------------------------------------------------------------
# Function 2: Get AQI data for all California cities in the DataFrame
# ------------------------------------------------------------------
@st.cache_data
def get_california_aqi(ca_df):
    pm25_aqi = []
    pm25_category = []
    for index, row in ca_df.iterrows():
        aqi_data = get_aqi(row['Zipcode'])
        for obs in aqi_data:
            if obs['ParameterName'] == 'PM2.5':
                pm25_aqi.append(obs['AQI'])
                pm25_category.append(obs['Category']['Name'])
    ca_df['PM2.5 AQI'] = pm25_aqi
    ca_df['PM2.5 AQI Category'] = pm25_category
    return ca_df

# Get AQI data for California cities
ca_aqi_df = get_california_aqi(ca_df)

# ------------------------------------------------------------------
# Function 3: Create a folium map
# ------------------------------------------------------------------
@st.cache_data
def create_california_map(aqi_data):
    # Create a folium map centered in California
    m = folium.Map(location = [36.7783, -119.4179], zoom_start = 6)
    
    # Add markers to the map for each city in California
    for index, row in aqi_data.iterrows():
        folium.Marker(
            location = [row['Latitude'], row['Longitude']],
            icon = folium.Icon(color = "darkred"),
            popup = folium.Popup(
            f"""
            City: {row['City']}<br>
            PM2.5 AQI: {row['PM2.5 AQI']}<br>
            Category: {row['PM2.5 AQI Category']}
            """, 
            max_width = 250)
        ).add_to(m)
    return m


# Streamlit app display
st.title("California Cities AQI Map")
st.write("This map shows the AQI (Air Quality Index) values of major cities in California along with their categories.")
with st.expander("See DataFrame"):  
    st.write(ca_aqi_df)
st_folium(create_california_map(ca_aqi_df), width = 700, height = 500)