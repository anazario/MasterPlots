# canvas_creator.py
import os
import importlib
import ROOT
from .utils import path_to_module, camel_to_snake

def process_histograms(hist_folder):
    return {
        hist_key.GetName(): hist_folder.Get(hist_key.GetName())
        for hist_key in hist_folder.GetListOfKeys()
    }

def ensure_folder(root_file, path):
    if not root_file.GetDirectory(path):
        root_file.mkdir(path)
    return path

def write_canvases(root_file, path, canvases):
    root_file.cd(path)
    for name, canvas in canvases.items():
        canvas.Write(name)

def get_original_subfolder_name(path_parts):
    return path_parts[-1] if len(path_parts) > 1 else path_parts[0]

def find_script_file(subdir_path, folder_name):
    for f in os.listdir(subdir_path):
        if f.endswith(".py") and "".join(word.capitalize() for word in f[:-3].split("_")) == folder_name:
            return f
    return None

def create_canvases(histogram_file, canvas_file, subdirectory_path):
    hist_file = ROOT.TFile.Open(histogram_file, "READ")
    canvas_root_file = ROOT.TFile.Open(canvas_file, "RECREATE")

    def process_directory(directory, path_parts):
        current_path = path_parts + [directory.GetName()]

        for key in directory.GetListOfKeys():
            obj = directory.Get(key.GetName())
            if obj.InheritsFrom("TDirectory") and obj.GetDirectory("histograms"):
                original_folder = get_original_subfolder_name(current_path)
                script_folder = obj
                hist_folder = script_folder.Get("histograms")
                script_name = camel_to_snake(script_folder.GetName())
                script_file = find_script_file(f"{subdirectory_path}/{original_folder}", script_folder.GetName())

                if not script_file:
                    continue

                module_path = path_to_module(subdirectory_path)
                if module_path.startswith("MasterPlots."):
                    module_path = module_path[len("MasterPlots."):]                
                module_name = f"{module_path}.{original_folder}.{script_file[:-3]}"

                try:
                    module = importlib.import_module(module_name)
                    if not hasattr(module, "create_canvases"):
                        print(f"Warning: {script_file} has no create_canvases function.")
                        continue

                    label = current_path[1] if current_path[1] in {"signal", "background", "data"} else None
                    histograms = process_histograms(hist_folder)
                    canvases = module.create_canvases(histograms, f"{label}/{current_path[2]}")
                    canvas_folder_path = "/".join(current_path + [script_folder.GetName(), "canvases"]).split("/", 1)[1]
                    ensure_folder(canvas_root_file, canvas_folder_path)
                    write_canvases(canvas_root_file, canvas_folder_path, canvases)
                    #print(f"Processing {label}/{current_path[2]}")
                    #print(f"\tGenerated {len(canvases)} canvases for {script_file[:-3]}.")

                except Exception as e:
                    print(f"Error processing module {module_name}: {e}")
            elif obj.InheritsFrom("TDirectory"):
                process_directory(obj, current_path)

    try:
        process_directory(hist_file, [])
    finally:
        hist_file.Close()
        canvas_root_file.Close()
