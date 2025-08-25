import os
import importlib
import ROOT
from pathlib import Path

def path_to_module(dir_path: str) -> str:
    """Convert a directory path to a Python module notation (e.g., 'a/b/c' → 'a.b.c')."""
    return Path(dir_path).as_posix().replace("/", ".")

def save_histograms(output_file, subdirectory_path, subdirectory_name, events, root_dir_prefix=None):
    """
    Save histograms to a ROOT file based on configuration and scripts.
    
    Args:
        output_file: ROOT file object accessed through uproot to save histograms
        subdirectory_path: Path to the directory containing config and scripts
        subdirectory_name: Name of the subdirectory for module imports
        events: Event data to process (accessed through uproot)
        root_dir_prefix: Optional prefix for ROOT file directory structure (e.g., 'data', 'signal', 'background')
    """

    def read_config(config_path):
        """Read and filter non-empty lines from config file."""
        if not os.path.exists(config_path):
            print(f"Warning: No config.txt found in {subdirectory_path}. Skipping.")
            return []

        with open(config_path, "r") as config_file:
            if not config_path.startswith('#'):
                return [line.strip() for line in config_file if line.strip()]

    def get_script_folder(script_name):
        """Convert script name to CamelCase folder name."""
        return "".join(word.capitalize() for word in script_name.split("_"))

    def process_script(script_name, folder_path, root_path):
        """Process individual script and save its histograms."""

        # Use original subdirectory_name for module imports (not the ROOT path)
        module_path = path_to_module(f"{subdirectory_path}/{script_name}")

        prefix = "MasterPlots."
        if module_path.startswith(prefix):
            module_path = module_path[len(prefix):]
        
        module = importlib.import_module(module_path)
        
        if not hasattr(module, "create_histograms"):
            print(f"Warning: {script_name} has no create_histograms function.")
            return

        histograms = module.create_histograms(events, root_dir_prefix)
        print(f"\tExecuted {script_name} in {subdirectory_name}. "
              f"Collected {len(histograms)} histograms.")

        # Save histograms to ROOT file
        for name, hist in histograms.items():
            output_file[f"{root_path}/histograms/{name}"] = hist

    # Main execution
    config_path = os.path.join(subdirectory_path, "config.txt")

    scripts = read_config(config_path)
    if not scripts:
        return

    # Determine the root directory name in the ROOT file
    if root_dir_prefix:
        root_dir_name = f"{root_dir_prefix}/{subdirectory_name}"
    else:
        root_dir_name = subdirectory_name
    
    output_file.mkdir(root_dir_name)

    for script_name in scripts:
        try:
            script_folder = get_script_folder(script_name)
            
            if not script_folder.startswith('#'):
                root_folder_path = f"{root_dir_name}/{script_folder}" 
                full_folder_path = f"{subdirectory_path}/{script_folder}"
                output_file.mkdir(root_folder_path)
                process_script(script_name, full_folder_path, root_folder_path)
                print(root_folder_path)
        except Exception as e:
            print(f"Error executing {script_name}: {e}")

def create_canvases(histogram_file, canvas_file, subdirectory_path):
    """
    Create canvases from histograms in a ROOT file structure.
    
    Args:
        histogram_file: Path to ROOT file containing histograms
        canvas_file: Path to output ROOT file for canvases
    """
    def process_histograms(hist_folder):
        """Helper function to collect histograms from a folder."""
        return {
            hist_key.GetName(): hist_folder.Get(hist_key.GetName())
            for hist_key in hist_folder.GetListOfKeys()
        }

    def ensure_canvas_folder(root_file, path):
        """Helper function to create canvas folder if it doesn't exist."""
        if not root_file.GetDirectory(path):
            root_file.mkdir(path)
        return path

    def write_canvases(root_file, path, canvases):
        """Helper function to write canvases to file."""
        root_file.cd(path)
        for name, canvas in canvases.items():
            canvas.Write(name)

    def get_original_subfolder_name(path_parts):
        """Extract original subfolder name from path, handling prefixed directories."""
        # If path has a prefix (data/VertexVariables), return the last part
        # If no prefix (VertexVariables), return as-is
        return path_parts[-1] if len(path_parts) > 1 else path_parts[0]

    # Open the histogram ROOT file for reading and canvas file for writing
    hist_file = ROOT.TFile.Open(histogram_file, "READ")
    canvas_root_file = ROOT.TFile.Open(canvas_file, "RECREATE")

    try:
        def process_directory(directory, path_parts):
            """Recursively process directories to handle both flat and prefixed structures."""
            directory_name = directory.GetName()
            current_path = path_parts + [directory_name]

            # Check if this directory contains script folders (has subdirectories with histograms)
            has_script_folders = False
            for key in directory.GetListOfKeys():
                obj = directory.Get(key.GetName())
                if obj.InheritsFrom("TDirectory"):
                    subdir = obj
                    if subdir.GetDirectory("histograms"):
                        has_script_folders = True
                        break
            
            if has_script_folders:
                # This is a subfolder containing scripts (like VertexVariables)
                original_subfolder_name = get_original_subfolder_name(current_path)

                print(original_subfolder_name)
                
                for key in directory.GetListOfKeys():
                    obj = directory.Get(key.GetName())
                    if not obj.InheritsFrom("TDirectory"):
                        continue
                        
                    script_folder = obj
                    script_folder_name = script_folder.GetName()
                    hist_folder = script_folder.Get("histograms")

                    if not hist_folder:
                        continue
                    
                    # Convert CamelCase back to snake_case for module import
                    script_name = "_".join(word.lower() for word in 
                                         [script_folder_name[i:i+1] + script_folder_name[i+1:].rstrip('ABCDEFGHIJKLMNOPQRSTUVWXYZ') 
                                          for i in range(0, len(script_folder_name), 1) 
                                          if script_folder_name[i].isupper()] if word)
                    
                    # Find the actual script file
                    script_files = [f for f in os.listdir(f"{subdirectory_path}/{original_subfolder_name}") 
                                   if f.endswith(".py") and 
                                   "".join(word.capitalize() for word in f[:-3].split("_")) == script_folder_name]
                    
                    if not script_files:
                        continue

                    module_path = path_to_module(subdirectory_path)
                    prefix = "MasterPlots."
                    if module_path.startswith(prefix):
                        module_path = module_path[len(prefix):]
                    
                    script_file = script_files[0]
                    module_name = f"{module_path}.{original_subfolder_name}.{script_file[:-3]}"

                    try:
                        module = importlib.import_module(module_name)
                        if not hasattr(module, "create_canvases"):
                            print(f"Warning: {script_file} has no create_canvases function.")
                            continue

                        label = current_path[1] if current_path[1] in {'signal', 'background', 'data'} else None

                        histograms = process_histograms(hist_folder)
                        canvases = module.create_canvases(histograms, label)
                        print(f"\tGenerated {len(canvases)} canvases for {script_file[:-3]}.")

                        canvas_folder_path = "/".join(current_path + [script_folder_name, "canvases"])
                        canvas_folder_path = canvas_folder_path.split("/", 1)[1]
                        
                        ensure_canvas_folder(canvas_root_file, canvas_folder_path)
                        write_canvases(canvas_root_file, canvas_folder_path, canvases)

                    except Exception as e:
                        print(f"Error processing module {module_name}: {e}")
            else:
                # This directory might contain other directories, recurse
                for key in directory.GetListOfKeys():
                    obj = directory.Get(key.GetName())
                    if obj.InheritsFrom("TDirectory"):
                        process_directory(obj, current_path)

        # Start processing from root directory
        process_directory(hist_file, [])
        
    finally:
        hist_file.Close()
        canvas_root_file.Close()
