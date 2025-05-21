import streamlit as st
import gpxpy
import csv
import io
import os

st.title("GPX to CSV Converter")

# File uploader: Allow multiple GPX files to be uploaded
uploaded_files = st.file_uploader("Upload GPX files", type="gpx", accept_multiple_files=True)

if uploaded_files:
    # Process each uploaded GPX file
    for uploaded_file in uploaded_files:
        # Read and parse each GPX file
        gpx = gpxpy.parse(uploaded_file)

        # Prepare output CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['trkpt_id', 'frame_latitude', 'frame_longitude', 'frame_time'])

        # Extract data
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

        # Generate a download link for each file
        csv_filename = os.path.splitext(uploaded_file.name)[0] + '.csv'
        st.success(f"CSV file is ready: {csv_filename}")
        st.download_button(
            label=f"Download CSV for {uploaded_file.name}",
            data=csv_bytes,
            file_name=csv_filename,
            mime='text/csv'
        )
