# histogram_writer.py
import importlib
import os
from .utils import path_to_module, read_config, get_script_folder

def import_analysis_module(base_path, script_name):
    module_path = path_to_module(f"{base_path}/{script_name}")
    prefix = "MasterPlots."
    if module_path.startswith(prefix):
        module_path = module_path[len(prefix):]
    return importlib.import_module(module_path)

def process_script(script_name, events, root_dir_prefix, output_file, script_dir, root_path):
    try:
        module = import_analysis_module(script_dir, script_name)
        if not hasattr(module, "create_histograms"):
            print(f"Warning: {script_name} lacks a create_histograms function.")
            return
        histograms = module.create_histograms(events, root_dir_prefix)
        for name, hist in histograms.items():
            output_file[f"{root_path}/histograms/{name}"] = hist
        #print(f"Processing {root_dir_prefix}")
        #print(f"\tExecuted {script_name}. Saved {len(histograms)} histograms.")
        return len(histograms)
    
    except Exception as e:
        print(f"Error executing {script_name}: {e}")

def save_histograms(output_file, subdirectory_path, subdirectory_name, events, root_dir_prefix=None):
    config_path = os.path.join(subdirectory_path, "config.txt")
    scripts = read_config(config_path)
    if not scripts:
        return

    root_dir_name = f"{root_dir_prefix}/{subdirectory_name}" if root_dir_prefix else subdirectory_name
    output_file.mkdir(root_dir_name)

    hist_count = 0
    
    for script_name in scripts:
        script_folder = get_script_folder(script_name)
        root_folder_path = f"{root_dir_name}/{script_folder}"
        full_folder_path = f"{subdirectory_path}/{script_folder}"
        output_file.mkdir(root_folder_path)
        hist_count += process_script(script_name, events, root_dir_prefix, output_file, subdirectory_path, root_folder_path)
    return hist_count
