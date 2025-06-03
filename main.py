import os
import argparse
import uproot
from tools.processing import *
from tools.histogram_generator import HistogramGenerator

ROOT.gROOT.SetBatch(True)

def main():
    parser = argparse.ArgumentParser(description="Generate ROOT file with plots from multiple scripts.")
    parser.add_argument("-f", "--file", required=True, help="Path to the input ntuple ROOT file.")
    parser.add_argument("--skip-histograms", action="store_true", 
                       help="Skip histogram generation and only create canvases from existing ROOT file")
    parser.add_argument("-o", "--output", default="output.root",
                       help="Output ROOT file path (default: output.root)")
    parser.add_argument("-m", "--memory_size", default=100,
                        help="Total memory used per chunk of data (mB).")

    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.file):
        print(f"Error: Input ntuple file '{args.file}' does not exist.")
        return

    # If we're only creating canvases, check if output file exists
    if args.skip_histograms:
        if not os.path.exists(args.output):
            print(f"Error: Cannot skip histogram generation - output file '{args.output}' does not exist.")
            return
        print("Skipping histogram generation, proceeding to create canvases...")
        create_canvases(args.output)
        return

    # Process for generating both histograms and canvases
    try:
        # Open input ROOT file
        events = uproot.open(f"{args.file}:tree/llpgtree")
        
        # Define directories to skip
        skip_dirs = {"__pycache__", "template", "test", "tools", "plots"}
        
        # Process histograms
        with uproot.recreate(args.output) as rfile:
            master_plots_dir = "MasterPlots"
            
            # Get valid subdirectories
            subdirs = [d for d in os.listdir(master_plots_dir) 
                      if os.path.isdir(os.path.join(master_plots_dir, d)) 
                      and d not in skip_dirs]
            
            # Process each subdirectory
            for subdir in subdirs:
                subdir_path = os.path.join(master_plots_dir, subdir)
                print(f"\nProcessing folder: {subdir_path}")
                save_histograms(rfile, subdir_path, subdir, events)
        
        # Create canvases after histograms are saved
        print("\nGenerating canvases from histograms...")
        create_canvases(args.output)
        
        print(f"\nProcessing complete. Output saved to: {args.output}")
        
    except Exception as e:
        print(f"Error during processing: {e}")

if __name__ == "__main__":
    main()
