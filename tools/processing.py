import os
import importlib
import ROOT

def save_histograms(output_file, subdirectory_path, subdirectory_name, events):
    """
    Save histograms to a ROOT file based on configuration and scripts.
    
    Args:
        output_file: ROOT file object accessed through uproot to save histograms
        subdirectory_path: Path to the directory containing config and scripts
        subdirectory_name: Name of the subdirectory in ROOT file
        events: Event data to process (accessed through uproot)
    """
    def read_config(config_path):
        """Read and filter non-empty lines from config file."""
        if not os.path.exists(config_path):
            print(f"Warning: No config.txt found in {subdirectory_path}. Skipping.")
            return []
            
        with open(config_path, "r") as config_file:
            return [line.strip() for line in config_file if line.strip()]

    def get_script_folder(script_name):
        """Convert script name to CamelCase folder name."""
        return "".join(word.capitalize() for word in script_name.split("_"))

    def process_script(script_name, folder_path):
        """Process individual script and save its histograms."""
        module_path = f"{subdirectory_name}.{script_name}"
        module = importlib.import_module(module_path)
        
        if not hasattr(module, "create_histograms"):
            print(f"Warning: {script_name} has no create_histograms function.")
            return

        histograms = module.create_histograms(events)
        print(f"\tExecuted {script_name} in {subdirectory_name}. "
              f"Collected {len(histograms)} histograms.")
        
        # Save histograms to ROOT file
        for name, hist in histograms.items():
            output_file[f"{folder_path}/histograms/{name}"] = hist

    # Main execution
    config_path = os.path.join(subdirectory_path, "config.txt")
    scripts = read_config(config_path)
    if not scripts:
        return

    output_file.mkdir(subdirectory_name)
    
    for script_name in scripts:
        try:
            script_folder = get_script_folder(script_name)
            full_folder_path = f"{subdirectory_name}/{script_folder}"
            output_file.mkdir(full_folder_path)
            
            process_script(script_name, full_folder_path)
            
        except Exception as e:
            print(f"Error executing {script_name}: {e}")

def create_canvases(output_file):
    """
    Create canvases from histograms in a ROOT file structure.
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

    # Open the ROOT file in update mode
    root_file = ROOT.TFile.Open(output_file, "UPDATE")
    
    try:
        for key in root_file.GetListOfKeys():
            subfolder = root_file.Get(key.GetName())
            subfolder_name = subfolder.GetName()
            
            for script_name in os.listdir(f"MasterPlots/{subfolder_name}"):
                if not script_name.endswith(".py"):
                    continue

                script_folder = "".join(word.capitalize() 
                                      for word in script_name[:-3].split("_"))
                hist_folder = subfolder.Get(f"{script_folder}/histograms")
                
                if not hist_folder:
                    continue

                module_name = f"{subfolder_name}.{script_name[:-3]}"

                try:
                    module = importlib.import_module(module_name)
                    if not hasattr(module, "create_canvases"):
                        print(f"Warning: {script_name} has no create_canvases function.")
                        continue

                    histograms = process_histograms(hist_folder)
                    canvases = module.create_canvases(histograms)
                    print(f"\tGenerated {len(canvases)} canvases for {script_name[:-3]}.")

                    canvas_folder_path = f"{subfolder_name}/{script_folder}/canvases"
                    ensure_canvas_folder(root_file, canvas_folder_path)
                    write_canvases(root_file, canvas_folder_path, canvases)

                except Exception as e:
                    print(f"Error processing module {module_name}: {e}")
    finally:
        root_file.Close()
