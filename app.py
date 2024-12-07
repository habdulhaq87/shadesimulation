import streamlit as st
import numpy as np
import pandas as pd
import trimesh
import plotly.graph_objects as go
from datetime import datetime
import pvlib
from pvlib.location import Location

# Set app configuration
st.set_page_config(page_title="Building Shade Simulator", layout="wide")

# Title
st.title("Building Shade Simulation (3D with Custom Model and Rotation)")
st.subheader("Location: Iraq Kurdistan, Winter Season")

# User input
latitude = 36.7
longitude = 44.0
timezone = "Asia/Baghdad"
elevation = 0  # Elevation above sea level (meters)

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

# Load the 3D model
model_path = "data/waj.obj"
try:
    scene = trimesh.load(model_path)

    # Check if the file is a scene or a single mesh
    if isinstance(scene, trimesh.Scene):
        if len(scene.geometry) == 0:
            raise ValueError("The 3D model contains no geometry.")
        mesh = list(scene.geometry.values())[0]  # Extract the first mesh
    elif isinstance(scene, trimesh.Trimesh):
        mesh = scene  # Single mesh loaded
    else:
        raise ValueError("Unsupported 3D model format.")

    # Rotation controls
    st.sidebar.subheader("Model Rotation Controls")
    rotation_x = st.sidebar.slider("Rotate X-axis (degrees)", -180, 180, 0)
    rotation_y = st.sidebar.slider("Rotate Y-axis (degrees)", -180, 180, 0)
    rotation_z = st.sidebar.slider("Rotate Z-axis (degrees)", -180, 180, 0)

    # Apply rotations to the mesh
    rotation_matrix_x = trimesh.transformations.rotation_matrix(
        np.radians(rotation_x), [1, 0, 0]
    )
    rotation_matrix_y = trimesh.transformations.rotation_matrix(
        np.radians(rotation_y), [0, 1, 0]
    )
    rotation_matrix_z = trimesh.transformations.rotation_matrix(
        np.radians(rotation_z), [0, 0, 1]
    )

    # Combine rotations
    rotation_matrix = trimesh.transformations.concatenate_matrices(
        rotation_matrix_x, rotation_matrix_y, rotation_matrix_z
    )
    mesh.apply_transform(rotation_matrix)

    # Get rotated vertices and faces
    vertices = mesh.vertices
    faces = mesh.faces

    # Adjust shadow length based on solar altitude
    if solar_altitude > 0:
        shadow_length = 10 / np.tan(np.radians(solar_altitude))  # Scale for visualization
        
        # Calculate shadow direction
        shadow_direction = solar_azimuth + 180 if solar_azimuth < 180 else solar_azimuth - 180
        shadow_dx = shadow_length * np.sin(np.radians(shadow_direction))
        shadow_dy = shadow_length * np.cos(np.radians(shadow_direction))

        # Create shadow vertices
        shadow_vertices = vertices.copy()
        shadow_vertices[:, 0] += shadow_dx
        shadow_vertices[:, 1] += shadow_dy
        shadow_vertices[:, 2] = 0  # Project onto the ground

        # Visualize the model and shadow using Plotly
        fig = go.Figure()

        # Add the 3D model
        fig.add_trace(go.Mesh3d(
            x=vertices[:, 0],
            y=vertices[:, 1],
            z=vertices[:, 2],
            i=faces[:, 0],
            j=faces[:, 1],
            k=faces[:, 2],
            color='blue',
            opacity=0.5,
            name="Building"
        ))

        # Add the shadow
        fig.add_trace(go.Mesh3d(
            x=shadow_vertices[:, 0],
            y=shadow_vertices[:, 1],
            z=shadow_vertices[:, 2],
            i=faces[:, 0],
            j=faces[:, 1],
            k=faces[:, 2],
            color='gray',
            opacity=0.3,
            name="Shadow"
        ))

        # Set layout for 3D plot
        fig.update_layout(
            scene=dict(
                xaxis_title="X (meters)",
                yaxis_title="Y (meters)",
                zaxis_title="Z (meters)",
            ),
            title="3D Shading Simulation with Custom Model and Rotation"
        )
        st.plotly_chart(fig)
    else:
        st.warning("The sun is below the horizon. No shadow is visible.")

except Exception as e:
    st.error(f"Error loading 3D model: {e}")

# Footer
st.write("---")
st.caption("Developed by Hawkar Abdulhaq")
