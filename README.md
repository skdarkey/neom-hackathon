# Neom Hackathon Metadata Extration code
- Contributor: Selorm Komla Darkey (skdarkey@gmail.com)

## Download

To develop and modify the code, clone this repository.

## Files

- crawl_and_classify.ipynb          (Notebook)
- extract_all_metadata.py           (Python file)
- neom_metadata_extractor_v2.py     (Python file)
- helper function                   (python file)
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

## Extract Metadata in 3 different ways
**Extractor Graphical User Interface**
 - In your terminal, run the streamlit app using the `streamlit run`. Like this `streamlit run .\neom_metadata_extractor_v2.py`
 - This will run the app in your browser
 - Copy and paste your paths to scan and output directory path.
 - Select the file types to process.
 - Click `Run Metadata Extraction`.

 **Step By Step Notebook Extraction** 
 - The notebook presents a step by step workflow. It is best used for understanding the metadata extraction workflow
 - Open notebook `crawl_and_classify.ipynb`
 - Set paths and global variables 
 - Run all cells to extract metadata and visualize the outputs

**Single Python file**
 - The python file `extract_all_metadata.py` is best used if you want to improve the current approach.
 - open the file, set the root path, and paths to output csv
 - Select the file to be processed, then run the file in your terminal `python .\extract_all_metadata.py`. 

### Graphical User Interface
![Metadata UI](codes/images/metadata_ui.png)




