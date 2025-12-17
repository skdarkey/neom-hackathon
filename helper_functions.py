import geopandas as gpd
import pandas as pd
import fiona 
from fiona.errors import DriverError
import os
from tqdm import tqdm
import matplotlib.pyplot as plt
from PIL import Image
import shapely
from shapely.geometry import shape
from shapely.errors import GeometryTypeError
from datetime import datetime
from PIL import Image, ExifTags
import logging
import warnings


# ---------------------------
#  Lists to be used in organising the metadata
SPECIES_TYPES = ["Corals", "Dugong", "Turtles", "Flying Fish", "Flora And Fauna", "Bird", "Cetaceans"]
ACTIVITY_TYPES = ["Restoration", "Survey", "Study", "Species Management", "Species_Recovery"]
IMAGES_EXTENSTIONS = ['.png', '.jpg','.cr2', 'gif', 'bmp', '.tif', 'webp', '.heic', '.jpeg', '.JPEG', '.JPG' ]
DATE_COLUMNS = ["Timestamp", "Date_", "StartDate", "EndDate"]
SHAPEFILES_EXTENSIONS = ['.shp', '.gpkg']
CSV_EXCEL_EXTENSIONS = ['.csv', '.xlsx', '.xls']
CRS = '32636' 

# function to find matching species and activity types
def find_match(values, parts):
    """This function finds matches 
        between two sets of strings. It is used 
        here to find species and activity types from 
        parts of the file name.
    I """
    for v in values:
        v_norm = v.lower().replace(" ", "_")
        if any(v_norm in p.replace(" ", "_") for p in parts):
            return v
    return None

# function to grab all images in the directory 
def get_files_to_list(root_dirs, files_endwith):
    """This function walks through directories and grabs all files such as images"""
    db_names = []
    db_paths = []

    for root_dir in root_dirs:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            for f in filenames:
                for i in files_endwith:
                    if f.endswith(f"{i}"):   #files_endwith
                        file_path = os.path.join(dirpath, f)
                        
                        # db_names.append(name)
                        db_paths.append(file_path)

    return db_paths

# 
def extract_image_metadata(
    image_paths,
    output_csv
):
    """
    Extracts metadata from image files using file system info,
    PIL image headers, EXIF (if present), and path-based inference.

    Parameters
    ----------
    image_paths : list[str]
        List of full paths to image files
    output_csv : str
        Path to save metadata CSV

    Returns
    -------
    pd.DataFrame
        Image metadata table
    """

    records = []

    # Reverse EXIF tag map once
    EXIF_TAGS = {v: k for k, v in ExifTags.TAGS.items()}

    for img_path in tqdm(image_paths):

        file_name = os.path.basename(img_path)
        name_no_ext, ext = os.path.splitext(file_name)

        meta = {
            "image_path": img_path,
            "file_name": file_name,
            "file_extension": ext.lower(),
            "status": "success",
            "error": None
        }

        try:
            # ---- File system metadata ----
            stat = os.stat(img_path)

            meta["file_size_mb"] = round(stat.st_size / (1024 ** 2), 3)
            meta["created_time"] = datetime.fromtimestamp(stat.st_ctime)
            meta["modified_time"] = datetime.fromtimestamp(stat.st_mtime)

            # ---- Path-based metadata ----
            path_parts = img_path.split(os.sep)
            path_parts_lower = [p.lower() for p in path_parts]

            meta["Species"] = find_match(SPECIES_TYPES, path_parts_lower)
            meta["activity"] = find_match(ACTIVITY_TYPES, path_parts_lower)

            # ---- Filename-derived metadata ----
            tokens = name_no_ext.replace("-", "_").split("_")
            meta["filename_tokens"] = ", ".join(tokens)

            # ---- Image header metadata ----
            with Image.open(img_path) as img:
                meta["image_format"] = img.format
                meta["color_mode"] = img.mode
                meta["width_px"], meta["height_px"] = img.size
                meta["aspect_ratio"] = round(img.size[0] / img.size[1], 4)

                # ---- EXIF metadata (best effort) ----
                exif_data = img._getexif()
                if exif_data:
                    exif = {
                        ExifTags.TAGS.get(tag, tag): value
                        for tag, value in exif_data.items()
                        if tag in ExifTags.TAGS
                    }

                    meta["has_exif"] = True
                    meta["camera_make"] = exif.get("Make")
                    meta["camera_model"] = exif.get("Model")
                    meta["datetime_original"] = exif.get("DateTimeOriginal")
                    meta["gps_info"] = "GPSInfo" in exif
                else:
                    meta["has_exif"] = False
                    meta["camera_make"] = None
                    meta["camera_model"] = None
                    meta["datetime_original"] = None
                    meta["gps_info"] = False

        except Exception as e:
            meta["status"] = "failed"
            meta["error"] = str(e)

        records.append(meta)

    # ---- Create DataFrame ----
    meta_df = pd.DataFrame(records)

    # ---- Save CSV ----
    meta_df.to_csv(output_csv, index=False, encoding="utf-8")

    # return meta_df

# functions to return geodatabase / files paths in list 
def get_geodbs_to_list(root_dirs, files_endwith='gdb'):
    """This function walks through directories and grabs all geodatabases"""
    db_names = []
    db_paths = []

    for root_dir in root_dirs:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            for f in dirnames:
                if f.endswith(f"{files_endwith}"):
                    file_path = os.path.join(dirpath, f)
                    
                    # Extract parts 
                    parts = os.path.normpath(file_path).split(os.sep)  
                    name = parts[-2]   

                    db_names.append(name)
                    db_paths.append(file_path)

    return db_names, db_paths

# find layers in gdb
def get_gdb_layers(gdb_paths):
    """
    Returns a dictionary mapping each geodatabase path
    to a list of its layer names.
    """
    layers_dict = {}
    rows = []

    for gdb_path in gdb_paths:
        try:
            layers = fiona.listlayers(gdb_path)
            layers_dict[gdb_path] = list(layers)

        except Exception as e:
            print(f"Skipping {gdb_path}: {e}")
            layers_dict[gdb_path] = []  # keep record of failed GDBs
            continue

    # return layers_dict
    for gdb_path, layers in layers_dict.items():
        if layers:
            for layer in layers:
                rows.append({
                    "geodatabase": gdb_path,
                    "layer": layer
                })
        else:
            rows.append({
                "geodatabase": gdb_path,
                "layer": None
            })

        # save a csv
    # df = pd.DataFrame(rows)
    # df.to_csv(f"{output_layers_csv_path}", index=False)
    
    # return layers
    return rows

# function to extract layers meta data
def extract_gdb_layer_metadata(
    layers_df,
    output_csv,
    crs=CRS
):
    """
    Reads geodatabase layers and extracts metadata safely.
    
    Parameters
    ----------
    layers_df : pd.DataFrame
        Must contain columns: ['geodatabase', 'layer']
    output_csv : str
        Path to save metadata CSV

    
    Returns
    -------
    pd.DataFrame
        Detailed metadata table
    """

    records = []

    # for idx, row in layers_df.iterrows():
    for idx, row in tqdm(layers_df.iterrows(), total=len(layers_df), desc="Processing layers"):
        gdb = row["geodatabase"]
        layer = row["layer"]

        meta = {
            "geodatabase": gdb,
            "layer": layer,
            "status": "success",
            "error": None
        }
   

        try:
            # ---- Read layer ----
            gdf = gpd.read_file(gdb, layer=layer)

            # # update to oriental bbox
            if gdf.crs is None:
                raise ValueError("Layer has no CRS defined")

            # Reproject if geographic (degrees)
            epsg = gdf.crs.to_epsg()
            if epsg == 4326:
                gdf = gdf.to_crs(crs)  # choose correct UTM zone

            # Clean invalid geometries 
            gdf["geometry"] = gdf.geometry.make_valid()

            # Dissolve all features
            geom = gdf.geometry.union_all()

            # Oriented bounding box
            obb = geom.minimum_rotated_rectangle
            obb_coords = list(obb.exterior.coords)[:4]

            # ---- Spatial metadata ----
            meta["crs"] = str(gdf.crs)
            meta["epsg"] = gdf.crs.to_epsg() if gdf.crs else None

            meta["geometry_types"] = ", ".join(sorted(gdf.geom_type.unique()))
            meta["bbox"] = list(gdf.total_bounds)
            meta["obb_bbox"] = obb_coords
            meta["geometry"] = gdf.geometry  # adding geometry 


            # ---- Feature-level metadata ----
            meta["feature_count"] = len(gdf)
            meta["has_geometry"] = "geometry" in gdf.columns

            # ----- Temporal meta data -----
            existing_date_cols = [col for col in DATE_COLUMNS if col in gdf.columns]

            meta["has_timestamp"] = len(existing_date_cols) > 0

            if meta["has_timestamp"]:
                for col in existing_date_cols:
                    gdf[col] = pd.to_datetime(gdf[col], errors="coerce")

                all_dates = pd.concat([gdf[col].dropna() for col in existing_date_cols])

                if not all_dates.empty:
                    meta["min_date"] = all_dates.min()
                    meta["max_date"] = all_dates.max()
                else:
                    meta["min_date"] = None
                    meta["max_date"] = None


            # ---- Attribute metadata ----
            meta["field_count"] = len(gdf.columns)
            meta["field_names"] = ", ".join(gdf.columns)

            meta["field_types"] = ", ".join(
                f"{col}:{dtype}"
                for col, dtype in gdf.dtypes.items()
            )
            # ---- Filtering metadata ----
            parts = layer.split('_')
            meta["first_word"] = f"{parts[0]}_{parts[1]}"

            gdb_parts = gdb.split(os.sep)
           
            # Normalize path parts once
            gdb_parts_lower = [p.lower() for p in gdb_parts]

            # ----- Species detection -----
            meta["Species"] = find_match(SPECIES_TYPES, gdb_parts_lower)
            meta["activity"] = find_match(ACTIVITY_TYPES, gdb_parts_lower)

            # ---- Derived metadata ----
            meta["memory_mb"] = round(
                gdf.memory_usage(deep=True).sum() / (1024 ** 2), 3
            )

            # ---- Z / M detection (best-effort) ----
            try:
                meta["has_z"] = gdf.geometry.has_z.any()
            except Exception:
                meta["has_z"] = None

        except (DriverError, PermissionError) as e:
            meta["status"] = "skipped"
            meta["error"] = str(e)

        except Exception as e:
            meta["status"] = "failed"
            meta["error"] = str(e)

        records.append(meta)

    # ---- Create DataFrame ----
    meta_df = pd.DataFrame(records)

    # ---- Save CSV ----
    meta_df.to_csv(output_csv, index=False, encoding="utf-8")

    # return meta_df

# function to extract shapefiles metadata
def extract_shapefile_metadata(
    shp_paths,
    output_csv,
    crs=CRS
):
    """
    Reads shapefiles and extracts metadata safely.

    Parameters
    ----------
    shp_paths : list[str]
        List of full paths to shapefiles
    output_csv : str
        Path to save metadata CSV

    Returns
    -------
    pd.DataFrame
        Detailed metadata table
    """

    records = []

    for shp in tqdm(shp_paths):

        layer_name = os.path.splitext(os.path.basename(shp))[0]

        meta = {
            "shapefile_path": shp,
            "layer_name": layer_name,
            "status": "success",
            "error": None
        }

        try:
            # ---- Read shapefile ----
            gdf = gpd.read_file(shp)

            if gdf.empty:
                raise ValueError("Shapefile contains no features")

            if gdf.crs is None:
                raise ValueError("Layer has no CRS defined")

            # ---- CRS handling ----
            epsg = gdf.crs.to_epsg()
            if epsg == 4326:
                gdf = gdf.to_crs(crs)  

            # ---- Geometry cleanup ----
            gdf["geometry"] = gdf.geometry.make_valid()

            geom = gdf.geometry.union_all()

            # ---- Oriented bounding box ----
            obb = geom.minimum_rotated_rectangle
            obb_coords = list(obb.exterior.coords)[:4]

            # ---- Spatial metadata ----
            meta["crs"] = str(gdf.crs)
            meta["epsg"] = gdf.crs.to_epsg()
            meta["geometry_types"] = ", ".join(sorted(gdf.geom_type.unique()))
            meta["bbox"] = list(gdf.total_bounds)
            meta["obb_bbox"] = obb_coords


            # ---- Feature-level metadata ----
            meta["feature_count"] = len(gdf)
            meta["has_geometry"] = "geometry" in gdf.columns

            # ---- Temporal metadata ----
            existing_date_cols = [col for col in DATE_COLUMNS if col in gdf.columns]
            meta["has_timestamp"] = len(existing_date_cols) > 0

            if meta["has_timestamp"]:
                for col in existing_date_cols:
                    gdf[col] = pd.to_datetime(gdf[col], errors="coerce")

                all_dates = pd.concat(
                    [gdf[col].dropna() for col in existing_date_cols],
                    ignore_index=True
                )

                if not all_dates.empty:
                    meta["min_date"] = all_dates.min()
                    meta["max_date"] = all_dates.max()
                else:
                    meta["min_date"] = None
                    meta["max_date"] = None
            else:
                meta["min_date"] = None
                meta["max_date"] = None

            # ---- Attribute metadata ----
            meta["field_count"] = len(gdf.columns)
            meta["field_names"] = ", ".join(gdf.columns)

            meta["field_types"] = ", ".join(
                f"{col}:{dtype}"
                for col, dtype in gdf.dtypes.items()
            )

            # ---- Path-based metadata ----
            shp_parts = shp.split(os.sep)
            shp_parts_lower = [p.lower() for p in shp_parts]

            meta["Species"] = find_match(SPECIES_TYPES, shp_parts_lower)
            meta["activity"] = find_match(ACTIVITY_TYPES, shp_parts_lower)

            # ---- Derived metadata ----
            meta["memory_mb"] = round(
                gdf.memory_usage(deep=True).sum() / (1024 ** 2), 3
            )

            # ---- Z / M detection ----
            try:
                meta["has_z"] = gdf.geometry.has_z.any()
            except Exception:
                meta["has_z"] = None

        except (DriverError, PermissionError) as e:
            meta["status"] = "skipped"
            meta["error"] = str(e)

        except Exception as e:
            meta["status"] = "failed"
            meta["error"] = str(e)

        records.append(meta)

    # ---- Create DataFrame ----
    meta_df = pd.DataFrame(records)

    # ---- Save CSV ----
    meta_df.to_csv(output_csv, index=False, encoding="utf-8")
    
    # return meta_df

# function to extract csv meta data 
def extract_table_metadata(
    table_paths,
    output_csv
):
    """
    Extracts metadata from CSV and Excel files (.csv, .xlsx, .xls).

    Parameters
    ----------
    table_paths : list[str]
        List of full paths to CSV / Excel files
    output_csv : str
        Path to save metadata CSV

    Returns
    -------
    pd.DataFrame
        Tabular metadata table
    """

    records = []

    for file_path in tqdm(table_paths):

        file_name = os.path.basename(file_path)
        name_no_ext, ext = os.path.splitext(file_name)

        ext = ext.lower()

        meta = {
            "file_path": file_path,
            "file_name": file_name,
            "file_extension": ext,
            "status": "success",
            "error": None
        }

        try:
            # ---- File system metadata ----
            stat = os.stat(file_path)

            meta["file_size_mb"] = round(stat.st_size / (1024 ** 2), 3)
            meta["created_time"] = datetime.fromtimestamp(stat.st_ctime)
            meta["modified_time"] = datetime.fromtimestamp(stat.st_mtime)

            # ---- Path-based inference ----
            path_parts = file_path.split(os.sep)
            path_parts_lower = [p.lower() for p in path_parts]

            meta["Species"] = find_match(SPECIES_TYPES, path_parts_lower)
            meta["activity"] = find_match(ACTIVITY_TYPES, path_parts_lower)

            # ---- Filename parsing ----
            tokens = name_no_ext.replace("-", "_").split("_")
            meta["filename_tokens"] = ", ".join(tokens)

            # ---- Table-level metadata ----
            meta["row_count"] = None
            meta["column_count"] = None
            meta["column_names"] = None
            meta["column_types"] = None
            meta["sheet_count"] = None
            meta["sheet_names"] = None
            meta["has_timestamp"] = False
            meta["min_date"] = None
            meta["max_date"] = None

            # ---- CSV handling ----
            if ext == ".csv":
                df = pd.read_csv(file_path, nrows=1000)

                meta["row_count"] = sum(1 for _ in open(file_path, encoding="utf-8", errors="ignore")) - 1
                meta["column_count"] = len(df.columns)
                meta["column_names"] = ", ".join(df.columns)
                meta["column_types"] = ", ".join(
                    f"{c}:{t}" for c, t in df.dtypes.items()
                )

            # ---- Excel handling ----
            elif ext in [".xlsx", ".xls"]:
                xls = pd.ExcelFile(file_path)

                meta["sheet_count"] = len(xls.sheet_names)
                meta["sheet_names"] = ", ".join(xls.sheet_names)

                df = xls.parse(xls.sheet_names[0], nrows=1000)

                meta["column_count"] = len(df.columns)
                meta["column_names"] = ", ".join(df.columns)
                meta["column_types"] = ", ".join(
                    f"{c}:{t}" for c, t in df.dtypes.items()
                )

                meta["row_count"] = None  # avoid loading full sheets

            else:
                raise ValueError(f"Unsupported file type: {ext}")

            # ---- Temporal column detection ----
            date_cols = [c for c in DATE_COLUMNS if c in df.columns]

            if date_cols:
                meta["has_timestamp"] = True

                for c in date_cols:
                    df[c] = pd.to_datetime(df[c], errors="coerce")

                all_dates = pd.concat([df[c].dropna() for c in date_cols])

                if not all_dates.empty:
                    meta["min_date"] = all_dates.min()
                    meta["max_date"] = all_dates.max()

        except PermissionError as e:
            meta["status"] = "skipped"
            meta["error"] = str(e)

        except Exception as e:
            meta["status"] = "failed"
            meta["error"] = str(e)

        records.append(meta)

    # ---- Create DataFrame ----
    meta_df = pd.DataFrame(records)

    # ---- Save CSV ----
    meta_df.to_csv(output_csv, index=False, encoding="utf-8")

    # return meta_df

# processing geo dbs
def process_geodatabases(ROOT_DIRS,OUTPUT_GDB_METADATA_CSV):
    # Get geo dbs to list
    _, gdb_paths = get_geodbs_to_list(root_dirs=ROOT_DIRS)
    
    # get layers
    layers = get_gdb_layers(gdb_paths)
    lyrs_df = pd.DataFrame(layers) 

    # extract meta data for each geo database layer and save csv
    extract_gdb_layer_metadata(
        lyrs_df,
        output_csv=OUTPUT_GDB_METADATA_CSV)

    print(f"geodatabases meta data printed successfully to {OUTPUT_GDB_METADATA_CSV}")

# processing shapefiles
def process_shapefiles(ROOT_DIRS, OUTPUT_SHP_METADATA_CSV):
# check all shape files and geopackages
    shp_paths = get_files_to_list(ROOT_DIRS, files_endwith=SHAPEFILES_EXTENSIONS)

    # get shp meta data to csv
    extract_shapefile_metadata(shp_paths, output_csv=OUTPUT_SHP_METADATA_CSV)

    print(f"shapefiles meta data printed successfully to {OUTPUT_SHP_METADATA_CSV}")

# processing non spatial tabular data
def process_csv_and_excel(ROOT_DIRS, OUTPUT_CSV_METADATA_CSV):
    # for CSV and EXCEL files
    csv_paths = get_files_to_list(ROOT_DIRS, files_endwith=CSV_EXCEL_EXTENSIONS)

    # get all csv and excel tables meta data
    extract_table_metadata(csv_paths, OUTPUT_CSV_METADATA_CSV)

    print(f"csv and excel files meta data printed successfully to {OUTPUT_CSV_METADATA_CSV}")

# processing images
def process_images(ROOT_DIRS, OUTPUT_IMGS_METADATA_CSV):
    ## for images
    img_paths = get_files_to_list(ROOT_DIRS, files_endwith=IMAGES_EXTENSTIONS) 
    extract_image_metadata(img_paths, OUTPUT_IMGS_METADATA_CSV)

    print(f"Image files meta data printed successfully to {OUTPUT_IMGS_METADATA_CSV}") 

