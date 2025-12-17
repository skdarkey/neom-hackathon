import streamlit as st
from pathlib import Path
import extract_all_metadata
from PIL import Image, ExifTags
import os
from tqdm import tqdm
import pandas as pd
from datetime import datetime
import helper_functions


st.set_page_config(page_title="Neom Metadata Extractor v2", layout="centered")


# -----------------------------
# Helper: Folder Picker (Streamlit native)
# -----------------------------

def pick_folder(label="Select Folder", key=None):
    folder = st.text_input(label, value="", key=key, help="Enter folder path manually or paste it here")
    return folder

# -----------------------------
# Header
# -----------------------------
st.title("📁 Neom Metadata Extractor v2")
st.caption("Extracts metadata from geospatial, tabular, and image datasets")

st.markdown("""
This tool is designed for **non-technical users**.
Simply select folders, choose data types, and provide a single output name.
""")

st.divider()

# -----------------------------
# Root Directory Picker
# -----------------------------
st.subheader("1️⃣ Select Root Folder to Scan")
root_dir = pick_folder(label="Root folder to scan", key="root_dir_input")

# -----------------------------
# Document Types
# -----------------------------
st.subheader("2️⃣ Select Data Types to Process")
document_types = st.multiselect(
    "Choose one or more",
    options=[
        "GEODATABASES",
        "SHAPEFILES",
        "CSV AND EXCEL",
        "IMAGES",
    ],
)

# -----------------------------
# Output Folder Picker
# -----------------------------
st.subheader("3️⃣ Select Output Folder")
output_dir = pick_folder(label="Output folder", key="output_dir_input")

# -----------------------------
# Output File Base Name
# -----------------------------
st.subheader("4️⃣ Output File Name")
base_name = st.text_input(
    "Enter a base name for output files",
    value="metadata",
    help="This name will be used to generate multiple metadata CSV files",
)

st.markdown("**Generated files:**")
st.code(f"""
{base_name}_gdb_layer_metadata.csv
{base_name}_shp_layer_metadata.csv
{base_name}_csv_xlsx_tables_metadata.csv
{base_name}_images_layer_metadata.csv
""")

# -----------------------------
# Review Settings
# -----------------------------
st.subheader("5️⃣ Review & Run")
st.write("**Root folder:**", root_dir or "Not selected")
st.write("**Output folder:**", output_dir or "Not selected")
st.write("**Data types:**", ", ".join(document_types) if document_types else "None selected")

# -----------------------------
# Run Button
# -----------------------------
st.divider()
run = st.button("🚀 Run Metadata Extraction", use_container_width=True)

# --------------------
# Helper functions
# ----------------------------


# -----------------------------
# Execution Placeholder
# -----------------------------
if run:
    if not root_dir:
        st.error("Please provide a root folder")
    elif not output_dir:
        st.error("Please provide an output folder")
    elif not document_types:
        st.warning("Please select at least one data type")
    else:
        output_paths = {
            "GEODATABASES": Path(output_dir) / f"{base_name}_gdb_layer_metadata.csv",
            "SHAPEFILES": Path(output_dir) / f"{base_name}_shp_layer_metadata.csv",
            "CSV AND EXCEL": Path(output_dir) / f"{base_name}_csv_xlsx_tables_metadata.csv",
            "IMAGES": Path(output_dir) / f"{base_name}_images_layer_metadata.csv",
        }

        st.success("Metadata extraction started")

        with st.spinner("Extracting metadata..."):
            if "GEODATABASES" in document_types:
                helper_functions.process_geodatabases(
                    ROOT_DIRS=[root_dir],
                    OUTPUT_GDB_METADATA_CSV=output_paths["GEODATABASES"])
                
            if "SHAPEFILES" in document_types:
                helper_functions.process_shapefiles(
                    ROOT_DIRS=[root_dir],
                    OUTPUT_SHP_METADATA_CSV=output_paths["SHAPEFILES"]
                )

            if "CSV AND EXCEL" in document_types:
                helper_functions.process_csv_and_excel(
                    ROOT_DIRS=[root_dir],
                    OUTPUT_CSV_METADATA_CSV=output_paths["CSV AND EXCEL"]
                )

            if "IMAGES" in document_types:
                helper_functions.process_images(
                    ROOT_DIRS=[root_dir],
                    OUTPUT_IMGS_METADATA_CSV=output_paths["IMAGES"]
                )

        st.success("Metadata extraction completed ✅")
