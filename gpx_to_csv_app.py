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

st.title("🗂️ GPX Processing Utility App")

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
tab1, tab2, tab3, tab4 = st.tabs([
    "📤 GPX to CSV Converter",
    "🔄 CSV Filtration",
    "🧩 One-Step Convert & Filter",
    "📸 Extract Frames & Embed GPS"
    
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
with tab4:
    st.title("Extract Frames & Embed GPS")

    video_file = st.file_uploader("Upload Video File (MP4)", type=["mp4"], key="video_file")
    metadata_file = st.file_uploader("Upload Metadata CSV", type=["csv"], key="metadata_file")

    if video_file and metadata_file:
        try:
            import tempfile
            import cv2
            import piexif
            from fractions import Fraction
            from datetime import datetime
            import pandas as pd

            st.info("Processing files...")

            # Save temp video file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
                tmp_video.write(video_file.read())
                tmp_video_path = tmp_video.name

            # Save temp CSV file
            csv_bytes = metadata_file.read()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_csv:
                tmp_csv.write(csv_bytes)
                tmp_csv_path = tmp_csv.name

            # Load CSV
            df = pd.read_csv(tmp_csv_path)
            video = cv2.VideoCapture(tmp_video_path)
            fps = video.get(cv2.CAP_PROP_FPS)

            # Get base name for output folder
            video_name = os.path.splitext(os.path.basename(video_file.name))[0]
            output_folder = os.path.join(os.getcwd(), f"{video_name}_frames")
            os.makedirs(output_folder, exist_ok=True)

            # Helper functions
            def decimal_to_dms(decimal):
                degrees = int(abs(decimal))
                minutes = int((abs(decimal) - degrees) * 60)
                seconds = (abs(decimal) - degrees - minutes / 60) * 3600
                return [(degrees, 1), (minutes, 1), (int(seconds * 100), 100)]

            def create_gps_exif(lat, lon):
                gps_ifd = {
                    piexif.GPSIFD.GPSLatitudeRef: 'N' if lat >= 0 else 'S',
                    piexif.GPSIFD.GPSLatitude: decimal_to_dms(lat),
                    piexif.GPSIFD.GPSLongitudeRef: 'E' if lon >= 0 else 'W',
                    piexif.GPSIFD.GPSLongitude: decimal_to_dms(lon),
                }
                exif_dict = {"GPS": gps_ifd}
                return piexif.dump(exif_dict)

            st.info("Starting frame extraction...")
            progress_bar = st.progress(0)
            total = len(df)

            for index, row in df.iterrows():
                try:
                    timestamp = datetime.fromisoformat(row['frame_time'])
                    start_time = datetime.fromisoformat(df['frame_time'].iloc[0])
                    time_diff = (timestamp - start_time).total_seconds()
                    frame_no = int(time_diff * fps)

                    video.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
                    success, frame = video.read()

                    if not success:
                        st.warning(f"⚠️ Skipped frame at {time_diff:.2f}s (index {index})")
                        continue

                    image_filename = f"{video_name}_{frame_no}.jpg"
                    image_path = os.path.join(output_folder, image_filename)

                    # Save image
                    cv2.imwrite(image_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 100])

                    # Embed GPS
                    lat = float(row['frame_latitude'])
                    lon = float(row['frame_longitude'])
                    exif_bytes = create_gps_exif(lat, lon)
                    piexif.insert(exif_bytes, image_path)

                except Exception as e:
                    st.error(f"❌ Error at index {index}: {str(e)}")

                progress_bar.progress((index + 1) / total)

            video.release()
            st.success(f"🎉 Done! Extracted frames saved to: `{output_folder}`")
            st.info("Download frames manually from your working directory.")

        except Exception as e:
            st.error(f"❌ Failed to process files: {str(e)}")
