import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from datetime import datetime
import pandas as pd
import pvlib
from pvlib.location import Location

# Set app configuration
st.set_page_config(page_title="Building Shade Simulator", layout="wide")

# Title
st.title("Building Shade Simulation (3D)")
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
selected_date = st.date_input("Select Date", datetime(2024, 1, 15).date())

# Create a timezone-aware DatetimeIndex for the selected date
date_with_timezone = pd.date_range(start=selected_date, periods=1, freq="D", tz=timezone)

# Define the location
location = Location(latitude=latitude, longitude=longitude, tz=timezone, altitude=elevation)

# Calculate sunrise and sunset
sun_times = location.get_sun_rise_set_transit(date_with_timezone)
sunrise = sun_times['sunrise'].iloc[0]
sunset = sun_times['sunset'].iloc[0]

# Determine default time (midpoint between sunrise and sunset)
if pd.notna(sunrise) and pd.notna(sunset):
    default_time = sunrise + (sunset - sunrise) / 2
    default_time_str = default_time.strftime("%H:%M:%S")
else:
    default_time = datetime.now().time()
    default_time_str = "N/A"

# Display sunrise, sunset, and suggested time
st.write(f"**Sunrise**: {sunrise.strftime('%H:%M:%S') if pd.notna(sunrise) else 'N/A'}")
st.write(f"**Sunset**: {sunset.strftime('%H:%M:%S') if pd.notna(sunset) else 'N/A'}")
st.write(f"**Suggested Time (Midday)**: {default_time_str}")

# Time input with default as midday
selected_time = st.time_input("Select Time", default_time.time())

# Combine date and time into pandas.Timestamp with timezone
selected_datetime = pd.Timestamp(
    datetime.combine(selected_date, selected_time)
).tz_localize(timezone)

# Calculate solar position
solpos = pvlib.solarposition.get_solarposition(
    time=[selected_datetime],
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
    
    # Building coordinates
    building_vertices = [
        [0, 0, 0], [building_length, 0, 0], [building_length, building_width, 0], [0, building_width, 0],  # Base
        [0, 0, building_height], [building_length, 0, building_height],
        [building_length, building_width, building_height], [0, building_width, building_height]  # Top
    ]

    # Shadow coordinates on the ground
    shadow_vertices = [
        [building_length / 2, building_width / 2, 0],
        [building_length / 2 + shadow_dx, building_width / 2 + shadow_dy, 0]
    ]

    # Plot the results in 3D
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Plot building
    for i in range(4):  # Connect base to top
        ax.plot(
            [building_vertices[i][0], building_vertices[i + 4][0]],
            [building_vertices[i][1], building_vertices[i + 4][1]],
            [building_vertices[i][2], building_vertices[i + 4][2]],
            color='blue'
        )
    ax.plot(
        [building_vertices[0][0], building_vertices[1][0], building_vertices[2][0], building_vertices[3][0], building_vertices[0][0]],
        [building_vertices[0][1], building_vertices[1][1], building_vertices[2][1], building_vertices[3][1], building_vertices[0][1]],
        [building_vertices[0][2], building_vertices[1][2], building_vertices[2][2], building_vertices[3][2], building_vertices[0][2]],
        color='blue'
    )  # Base
    ax.plot(
        [building_vertices[4][0], building_vertices[5][0], building_vertices[6][0], building_vertices[7][0], building_vertices[4][0]],
        [building_vertices[4][1], building_vertices[5][1], building_vertices[6][1], building_vertices[7][1], building_vertices[4][1]],
        [building_vertices[4][2], building_vertices[5][2], building_vertices[6][2], building_vertices[7][2], building_vertices[4][2]],
        color='blue'
    )  # Top

    # Plot shadow
    ax.plot(
        [shadow_vertices[0][0], shadow_vertices[1][0]],
        [shadow_vertices[0][1], shadow_vertices[1][1]],
        [shadow_vertices[0][2], shadow_vertices[1][2]],
        color='gray',
        label="Shadow"
    )

    # Set labels and title
    ax.set_xlabel("X (meters)")
    ax.set_ylabel("Y (meters)")
    ax.set_zlabel("Z (meters)")
    ax.set_title("3D Shading Simulation")
    ax.legend()
    st.pyplot(fig)
else:
    st.warning("The sun is below the horizon. No shadow is visible.")

# Footer
st.write("---")
st.caption("Developed by Hawkar Abdulhaq")
