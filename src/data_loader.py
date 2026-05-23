import pandas as pd
from pathlib import Path

current_dir = Path(__file__).parent
data_path = current_dir / ".." / "data" / "raw"


def load_data_raw(file_name):
    file_path = data_path / file_name
    return pd.read_json(file_path)

