# Neom Hackathon Metadata Extration code

## Download

To develop and modify the code, clone this repository.

## Files

- crawl_and_classify.ipynb          (Notebook)
- extract_all_metadata.py           (Python file)
- requirements.txt                  (Python dependencies)

## Installation

### 1. Create and activate a virtual environment

Linux/macOS:

```
python3 -m venv venv
source venv/bin/activate
```

Windows:

```
python -m venv venv
venv\Scripts\activate
```

### 2. Install dependencies

    pip install -r requirements.txt

## Run notebook to extract metadata and save csv
 - The notebook presents a step by step workflow. It is best used for understanding the metadata extraction workflow
 - Open notebook 'crawl_and_classify.ipynb'
 - Set paths and global variables 
 - Run all cells to extract metadata and visualize the outputs

 - The python file 'extract_all_metadata' is best used for production stage.
 - open the file, set the root path, and paths to output csv
 - Select the file to be processed, then run the notebook. 





