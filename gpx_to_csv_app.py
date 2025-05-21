import streamlit as st
import gpxpy
import gpxpy.gpx
import csv
import io
import os
import math

# --- Set Page Config ---
st.set_page_config(
    page_title="GPX to CSV",
    page_icon="🗂️",
    layout="centered"
)

# --- Helper Functions ---
THRESHOLD_FT = 13
THRESHOLD_M = THRESHOLD_FT * 0.3048
DEFAULT_FRAME_ID = -2147483648

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_bearing(lat1, lon1, lat2, lon2):
    dLon = math.radians(lon2 - lon1)
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    x = math.sin(dLon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(dLon))
    bearing = math.atan2(x, y)
    return (math.degrees(bearing) + 360) % 360

def get_direction(bearing):
    directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    index = int((bearing + 22.5) // 45) % 8
    return directions[index]

def convert_gpx_to_rows(uploaded_file):
    file_content = uploaded_file.read().decode("utf-8")
    gpx = gpxpy.parse(io.StringIO(file_content))

    rows = []
    trkpt_id = 0
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                rows.append({
                    'trkpt_id': trkpt_id,
                    'frame_latitude': point.latitude,
                    'frame_longitude': point.longitude,
                    'frame_time': point.time.isoformat() if point.time else ''
                })
                trkpt_id += 1
    return rows

def filter_rows(rows):
    filtered_rows = []

    first = rows[0]
    last_lat = float(first['frame_latitude'])
    last_lon = float(first['frame_longitude'])

    filtered_rows.append({
        **first,
        'frame_id': DEFAULT_FRAME_ID,
        'direction': '',
        'cardinal_direction': ''
    })

    for point in rows[1:]:
        lat = float(point['frame_latitude'])
        lon = float(point['frame_longitude'])

        distance = haversine(last_lat, last_lon, lat, lon)
        if distance >= THRESHOLD_M:
            bearing = calculate_bearing(last_lat, last_lon, lat, lon)
            direction = get_direction(bearing)
            cardinal = direction[0] if direction else ''
            filtered_rows.append({
                **point,
                'frame_id': DEFAULT_FRAME_ID,
                'direction': direction,
                'cardinal_direction': cardinal
            })
            last_lat, last_lon = lat, lon

    return filtered_rows

def write_csv(data, fieldnames):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)
    output.seek(0)
    return output.getvalue().encode("utf-8")

# --- Tabs ---
tab1, tab2, tab3 = st.tabs([
    "📤 GPX to CSV Converter",
    "🔄 CSV Filtration",
    "🧩 One-Step Convert & Filter"
])

# --- GPX to CSV Converter ---
with tab1:
    st.title("GPX to CSV Converter")
    uploaded_files = st.file_uploader("Upload GPX files", type="gpx", accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            try:
                rows = convert_gpx_to_rows(uploaded_file)
                fieldnames = ['trkpt_id', 'frame_latitude', 'frame_longitude', 'frame_time']
                csv_bytes = write_csv(rows, fieldnames)
                filename = os.path.splitext(uploaded_file.name)[0] + ".csv"
                st.success(f"✅ CSV file is ready: {filename}")
                st.download_button(
                    label=f"Download CSV for {uploaded_file.name}",
                    data=csv_bytes,
                    file_name=filename,
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"❌ Error processing `{uploaded_file.name}`: {str(e)}")

# --- CSV Filtration ---
with tab2:
    st.title("CSV Filtration")
    uploaded_csv = st.file_uploader("Upload CSV file", type="csv", key="csv_filter")

    if uploaded_csv:
        try:
            csv_data = uploaded_csv.read().decode('utf-8')
            csv_lines = csv_data.splitlines()
            reader = csv.DictReader(csv_lines)
            rows = list(reader)

            filtered = filter_rows(rows)
            fieldnames = ['trkpt_id', 'frame_latitude', 'frame_longitude', 'frame_time', 'frame_id', 'direction', 'cardinal_direction']
            csv_bytes = write_csv(filtered, fieldnames)
            filename = os.path.splitext(uploaded_csv.name)[0] + " Metadata.csv"

            st.success(f"✅ Filtered CSV is ready: {filename}")
            st.download_button(
                label="Download Processed CSV",
                data=csv_bytes,
                file_name=filename,
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"❌ Error processing CSV: {str(e)}")

# --- One-Step Convert & Filter ---
with tab3:
    st.title("One-Step GPX Convert & Filter")
    uploaded_files = st.file_uploader("Upload GPX files", type="gpx", accept_multiple_files=True, key="one_step")

    if uploaded_files:
        for uploaded_file in uploaded_files:
            try:
                # Step 1: Convert GPX to rows
                rows = convert_gpx_to_rows(uploaded_file)

                # Step 2: Filter and add metadata
                filtered = filter_rows(rows)

                # Step 3: Write to CSV
                fieldnames = ['trkpt_id', 'frame_latitude', 'frame_longitude', 'frame_time', 'frame_id', 'direction', 'cardinal_direction']
                csv_bytes = write_csv(filtered, fieldnames)

                # Output filename similar to CSV Filtration
                original_filename = os.path.splitext(uploaded_file.name)[0]
                output_filename = f"{original_filename} Metadata.csv"  # Same as CSV Filtration pattern

                st.success(f"✅ One-step CSV ready: {output_filename}")
                st.download_button(
                    label=f"Download Filtered CSV for {uploaded_file.name}",
                    data=csv_bytes,
                    file_name=output_filename,
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"❌ Error processing `{uploaded_file.name}`: {str(e)}")
