import pandas as pd
from pathlib import Path

current_dir = Path(__file__).parent
data_path_raw = current_dir / ".." / "data" / "raw"
data_path_cleaned = current_dir / ".." / "data" / "processed"

def load_data_raw(file_name):
    file_path = data_path_raw / file_name
    return pd.read_json(file_path)

def load_data_cleaned(file_name):
    file_path = data_path_cleaned / file_name
    return pd.read_csv(file_path)