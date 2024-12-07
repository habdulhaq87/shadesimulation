import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import pvlib
from shapely.geometry import Polygon, Point
from pvlib.location import Location

# Set app configuration
st.set_page_config(page_title="Building Shade Simulator", layout="wide")

# Title
st.title("Building Shade Simulation")
st.subheader("Location: Iraq Kurdistan, Winter Season")

# User input
latitude = 36.7
longitude = 44.0
timezone = "Asia/Baghdad"
elevation = 0  # Elevation above sea level (meters)

building_length = 20  # Meters
building_width = 10   # Meters
building_height = 4   # Meters

# Date input
selected_date = st.date_input("Select Date", datetime(2024, 1, 15))

# Calculate sunrise and sunset for the selected date
location = Location(latitude=latitude, longitude=longitude, tz=timezone, altitude=elevation)
sun_times = location.get_sun_rise_set_transit(selected_date)
sunrise = sun_times['sunrise']
sunset = sun_times['sunset']

# Determine default time (midpoint between sunrise and sunset)
if sunrise is not pd.NaT and sunset is not pd.NaT:
    default_time = sunrise + (sunset - sunrise) / 2
    default_time_str = default_time.strftime("%H:%M:%S")
else:
    default_time = datetime.now()
    default_time_str = "N/A"

st.write(f"**Sunrise**: {sunrise.strftime('%H:%M:%S') if sunrise is not pd.NaT else 'N/A'}")
st.write(f"**Sunset**: {sunset.strftime('%H:%M:%S') if sunset is not pd.NaT else 'N/A'}")
st.write(f"**Suggested Time (Midday)**: {default_time_str}")

# Time input with default as midday
selected_time = st.time_input("Select Time", default_time.time())

# Combine date and time into pandas DatetimeIndex with timezone
selected_datetime = pd.DatetimeIndex([datetime.combine(selected_date, selected_time)]).tz_localize(timezone)

# Calculate solar position
solpos = pvlib.solarposition.get_solarposition(
    time=selected_datetime,
    latitude=latitude,
    longitude=longitude,
    altitude=elevation
)

# Get solar altitude and azimuth
solar_altitude = solpos['apparent_elevation'].iloc[0]
solar_azimuth = solpos['azimuth'].iloc[0]

# Display solar position
st.write(f"**Solar Altitude**: {solar_altitude:.2f}°")
st.write(f"**Solar Azimuth**: {solar_azimuth:.2f}°")

# Check if the sun is above the horizon
if solar_altitude > 0:
    # Shade calculation
    shadow_length = building_height / np.tan(np.radians(solar_altitude))
    
    # Calculate shadow geometry
    shadow_direction = solar_azimuth + 180 if solar_azimuth < 180 else solar_azimuth - 180
    shadow_dx = shadow_length * np.sin(np.radians(shadow_direction))
    shadow_dy = shadow_length * np.cos(np.radians(shadow_direction))
    
    # Building and shadow coordinates
    building_coords = [
        (0, 0), (building_length, 0),
        (building_length, building_width), (0, building_width), (0, 0)
    ]
    shadow_coords = [
        (building_length / 2, building_width / 2),
        (building_length / 2 + shadow_dx, building_width / 2 + shadow_dy)
    ]

    # Plot the results
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(*zip(*building_coords), label="Building", color="blue")
    ax.plot([shadow_coords[0][0], shadow_coords[1][0]],
            [shadow_coords[0][1], shadow_coords[1][1]],
            label="Shadow", color="gray")
    ax.fill(*zip(*building_coords), alpha=0.3, color="blue")
    ax.annotate("Building", xy=(1, 1), color="blue")
    ax.annotate("Shadow", xy=(shadow_dx / 2, shadow_dy / 2), color="gray")

    # Set axis limits
    ax.set_xlim(-50, 50)
    ax.set_ylim(-50, 50)
    ax.set_xlabel("X (meters)")
    ax.set_ylabel("Y (meters)")
    ax.set_title("Shading Simulation")
    ax.legend()
    ax.grid(True)
    
    st.pyplot(fig)
else:
    st.warning("The sun is below the horizon. No shadow is visible.")

# Footer
st.write("---")
st.caption("Developed by Hawkar Abdulhaq")
