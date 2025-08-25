# utils.py
import os
from pathlib import Path

def path_to_module(dir_path: str) -> str:
    return Path(dir_path).as_posix().replace("/", ".")

def read_config(config_path):
    if not os.path.exists(config_path):
        print(f"Warning: No config.txt found at {config_path}. Skipping.")
        return []
    with open(config_path, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

def get_script_folder(script_name):
    return "".join(word.capitalize() for word in script_name.split("_"))

def camel_to_snake(name):
    import re
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
