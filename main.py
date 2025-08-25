import os
import argparse
import glob
import uproot
import ROOT

from tools.histogram_writer import save_histograms
from tools.canvas_creator import create_canvases
from tools.histogram_generator import HistogramGenerator
from tools.input_utils import parse_input_files, get_valid_subdirectories

ROOT.gROOT.SetBatch(True)

def process_input_files(input_file, input_type, rfile, args):
    print(f"\n{'='*50}")
    print(f"Processing {input_type.upper()} input: {input_file}")
    print(f"{'='*50}")

    tree_suffix = f":{args.tree_path}"
    file_paths = parse_input_files(input_file, tree_suffix)
    subdirs = get_valid_subdirectories(args.plots_dir)

    for full_tree_path in file_paths:
        original_file = full_tree_path.split(":")[0]
        basename = os.path.basename(original_file).replace('.root', '')
        root_dir_prefix = os.path.join(input_type, basename) if input_type != "single" else None

        print(f"  --> Processing file: {original_file} (as {root_dir_prefix})")

        for subdir in subdirs:
            subdir_path = os.path.join(args.plots_dir, subdir)
            print(f"      \u21b3 Plot config: {subdir_path}")
            save_histograms(rfile, subdir_path, subdir, [full_tree_path],
                            root_dir_prefix=root_dir_prefix)

def validate_arguments(args):
    if args.file:
        if any([args.data, args.signal, args.background]):
            raise ValueError("Cannot use -f/--file with -d/--data, -s/--signal, or -b/--background.")
        return "single", [("single", args.file)]
    else:
        input_types = [
            ("data", args.data),
            ("signal", args.signal),
            ("background", args.background)
        ]
        valid_inputs = [(name, path) for name, path in input_types if path is not None]
        if not valid_inputs:
            raise ValueError("Must specify either a single input (-f) or one of -d/-s/-b.")
        return "multi", valid_inputs

def generate_output_filenames(output_arg):
    if output_arg.endswith('.root'):
        output_basename = output_arg[:-5]
    else:
        output_basename = output_arg
    return f"{output_basename}_histograms.root", f"{output_basename}_canvases.root"

def main():
    parser = argparse.ArgumentParser(description="Generate ROOT file with plots from multiple input types.")
    parser.add_argument("-f", "--file")
    parser.add_argument("-d", "--data")
    parser.add_argument("-s", "--signal")
    parser.add_argument("-b", "--background")
    parser.add_argument("--skip-histograms")
    parser.add_argument("-o", "--output", default="output")
    parser.add_argument("-m", "--memory_size", default=100)
    parser.add_argument("--tree-path", default="tree/llpgtree")
    parser.add_argument("--plots-dir", default="MasterPlots")
    parser.add_argument("--only-histograms", action="store_true",
                        help="Only generate histograms, skip canvas creation.")

    args = parser.parse_args()

    try:
        mode, inputs = validate_arguments(args)
        print(f"Running in {mode}-input mode.")
        histogram_file, canvas_file = generate_output_filenames(args.output)

        if args.skip_histograms:
            if not args.skip_histograms.endswith('.root') or not os.path.exists(args.skip_histograms):
                print(f"Invalid histogram file: {args.skip_histograms}")
                return
            print(f"Reading histograms from: {args.skip_histograms}")
            create_canvases(args.skip_histograms, canvas_file, args.plots_dir)
            print(f"Canvas generation complete. Output saved to: {canvas_file}")
            return

        with uproot.recreate(histogram_file) as rfile:
            for input_type, input_file in inputs:
                process_input_files(input_file, input_type, rfile, args)

        if args.only_histograms:
            print(f"\nOnly histogram generation requested. Skipping canvas creation.")
            print(f"Histograms saved to: {histogram_file}")
            return

        print(f"\n{'='*50}\nGenerating canvases from histograms...\n{'='*50}")
        create_canvases(histogram_file, canvas_file, args.plots_dir)
        print(f"\nProcessing complete. Output saved to: {canvas_file}")

    except Exception as e:
        print(f"Error during processing: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
