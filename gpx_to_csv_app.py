import streamlit as st
import gpxpy
import csv
import io
import os
import math

# --- Create Tabs ---
tab1, tab2 = st.tabs(["📤 GPX to CSV Converter", "🔄 CSV Filteration"])

with tab1:
    st.title("GPX to CSV Converter")

    # File uploader for multiple GPX files
    uploaded_files = st.file_uploader("Upload GPX files", type="gpx", accept_multiple_files=True)

    if uploaded_files:
        # Process each uploaded GPX file
        for uploaded_file in uploaded_files:
            gpx = gpxpy.parse(uploaded_file)

            # Prepare output CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['trkpt_id', 'frame_latitude', 'frame_longitude', 'frame_time'])

            trkpt_id = 0
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        writer.writerow([
                            trkpt_id,
                            point.latitude,
                            point.longitude,
                            point.time.isoformat() if point.time else ''
                        ])
                        trkpt_id += 1

            # Convert output to downloadable bytes
            output.seek(0)
            csv_bytes = output.getvalue().encode('utf-8')

            # Generate a download link for the CSV file
            csv_filename = os.path.splitext(uploaded_file.name)[0] + '.csv'
            st.success(f"CSV file is ready: {csv_filename}")
            st.download_button(
                label=f"Download CSV for {uploaded_file.name}",
                data=csv_bytes,
                file_name=csv_filename,
                mime='text/csv'
            )

with tab2:
    st.title("CSV Filteration")

    # Instructions
    st.write("Upload a CSV file for processing with additional metadata.")

    uploaded_csv = st.file_uploader("Upload CSV file", type="csv")

    if uploaded_csv:
        # Read CSV content
        csv_data = uploaded_csv.read().decode('utf-8')
        csv_lines = csv_data.splitlines()
        reader = csv.DictReader(csv_lines)
        points = list(reader)

        # Parameters for filtering
        THRESHOLD_FT = 13
        THRESHOLD_M = THRESHOLD_FT * 0.3048
        DEFAULT_FRAME_ID = -2147483648

        # Haversine formula for distance calculation
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371000  # Earth radius in meters
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            d_phi = math.radians(lat2 - lat1)
            d_lambda = math.radians(lon2 - lon1)

            a = math.sin(d_phi / 2) ** 2 + \
                math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return R * c

        # Calculate bearing between two points
        def calculate_bearing(lat1, lon1, lat2, lon2):
            dLon = math.radians(lon2 - lon1)
            lat1 = math.radians(lat1)
            lat2 = math.radians(lat2)
            x = math.sin(dLon) * math.cos(lat2)
            y = math.cos(lat1)*math.sin(lat2) - (math.sin(lat1)*math.cos(lat2)*math.cos(dLon))
            bearing = math.atan2(x, y)
            return (math.degrees(bearing) + 360) % 360

        def get_direction(bearing):
            directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
            index = int((bearing + 22.5) // 45) % 8
            return directions[index]

        # Process the CSV to add metadata
        filtered_rows = []

        # Keep the first point
        first = points[0]
        last_lat = float(first['frame_latitude'])
        last_lon = float(first['frame_longitude'])

        filtered_rows.append({
            'trkpt_id': first['trkpt_id'],
            'frame_latitude': last_lat,
            'frame_longitude': last_lon,
            'frame_time': first['frame_time'],
            'frame_id': DEFAULT_FRAME_ID,
            'direction': '',
            'cardinal_direction': ''
        })

        # Iterate through the rest of the points
        for point in points[1:]:
            lat = float(point['frame_latitude'])
            lon = float(point['frame_longitude'])

            distance = haversine(last_lat, last_lon, lat, lon)

            if distance >= THRESHOLD_M:
                bearing = calculate_bearing(last_lat, last_lon, lat, lon)
                direction = get_direction(bearing)
                cardinal = direction[0] if direction else ''
                filtered_rows.append({
                    'trkpt_id': point['trkpt_id'],
                    'frame_latitude': lat,
                    'frame_longitude': lon,
                    'frame_time': point['frame_time'],
                    'frame_id': DEFAULT_FRAME_ID,
                    'direction': direction,
                    'cardinal_direction': cardinal
                })
                last_lat, last_lon = lat, lon

        # Convert filtered rows to CSV output
        output = io.StringIO()
        fieldnames = ['trkpt_id', 'frame_latitude', 'frame_longitude', 'frame_time', 'frame_id', 'direction', 'cardinal_direction']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered_rows)

        # Convert output to downloadable bytes
        output.seek(0)
        csv_bytes = output.getvalue().encode('utf-8')

        # Generate a download link for the processed CSV file
        output_filename = "Processed_Metadata.csv"
        st.success(f"Filtered CSV with metadata is ready: {output_filename}")
        st.download_button(
            label=f"Download Processed CSV",
            data=csv_bytes,
            file_name=output_filename,
            mime='text/csv'
        )
