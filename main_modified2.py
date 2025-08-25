import os
import argparse
import uproot
import ROOT

from tools.histogram_writer import save_histograms
from tools.canvas_creator import create_canvases
from tools.histogram_generator import HistogramGenerator

ROOT.gROOT.SetBatch(True)

def parse_input_files(input_arg, tree_suffix=":tree/llpgtree"):
    """Parse input argument and return list of file paths with tree suffix.
    
    Args:
        input_arg: Either a single ROOT file path or a text file containing file paths
        tree_suffix: Tree path suffix to append to each file
    
    Returns:
        list: List of file paths with tree suffix
    """
    # Check if input is a text file containing file paths
    if input_arg.endswith('.txt'):
        if not os.path.exists(input_arg):
            raise FileNotFoundError(f"File list '{input_arg}' does not exist.")

        with open(input_arg, 'r') as file:
            file_paths = [line.strip() + tree_suffix for line in file if line.strip()]

        if not file_paths:
            raise ValueError(f"No valid file paths found in '{input_arg}'")

        print(f"Loaded {len(file_paths)} files from {input_arg}")
        return file_paths

    # Single ROOT file - return as single-item list for consistency
    elif input_arg.endswith('.root'):
        if not os.path.exists(input_arg):
            raise FileNotFoundError(f"Input ROOT file '{input_arg}' does not exist.")

        return [input_arg + tree_suffix]

    else:
        raise ValueError(f"Input file must be either a .root file or .txt file list, got: {input_arg}")


def get_valid_subdirectories(master_plots_dir, skip_dirs=None):
    """Get list of valid subdirectories, excluding specified directories.
    
    Args:
        master_plots_dir: Path to the master plots directory
        skip_dirs: Set of directory names to skip
    
    Returns:
        list: List of valid subdirectory names
    """
    if skip_dirs is None:
        skip_dirs = {"__pycache__", "template", "test", "tools", "plots", ".git"}
    
    if not os.path.exists(master_plots_dir):
        raise FileNotFoundError(f"Master plots directory '{master_plots_dir}' does not exist.")
    
    subdirs = [d for d in os.listdir(master_plots_dir)
              if os.path.isdir(os.path.join(master_plots_dir, d))
              and d not in skip_dirs]
    
    if not subdirs:
        raise ValueError(f"No valid subdirectories found in '{master_plots_dir}'")
    
    return subdirs


def process_input_files(input_file, input_type, rfile, args):
    """Process input files for a given input type.
    
    Args:
        input_file: Path to input file or file list
        input_type: Type of input ('single', 'data', 'signal', or 'background')
        rfile: Open uproot file for writing
        args: Command line arguments
    """
    print(f"\n{'='*50}")
    if input_type == "single":
        print(f"Processing input file: {input_file}")
    else:
        print(f"Processing {input_type.upper()} files: {input_file}")
    print(f"{'='*50}")

    try:
        # Parse input files
        tree_suffix = f":{args.tree_path}"
        file_paths = parse_input_files(input_file, tree_suffix)

        # Get valid subdirectories
        subdirs = get_valid_subdirectories(args.plots_dir)

        # Process each subdirectory
        for subdir in subdirs:
            subdir_path = os.path.join(args.plots_dir, subdir)
            print(f"Processing folder: {subdir_path}" + 
                  (f" for {input_type}" if input_type != "single" else ""))

            # Determine ROOT directory prefix
            root_dir_prefix = None if input_type == "single" else input_type

            save_histograms(rfile, subdir_path, subdir, file_paths,
                            root_dir_prefix=root_dir_prefix)

    except Exception as e:
        print(f"Error processing {input_type} input: {e}")
        raise


def validate_arguments(args):
    """Validate command line arguments and determine processing mode.
    
    Args:
        args: Parsed command line arguments
    
    Returns:
        tuple: (processing_mode, valid_inputs) where processing_mode is 'single' or 'multi'
               and valid_inputs is a list of (input_type, file_path) tuples
    """
    if args.file:
        # Single-file mode
        if any([args.data, args.signal, args.background]):
            raise ValueError("Cannot use -f/--file with -d/--data, -s/--signal, or -b/--background. "
                           "Use either: -f for single input, OR -d/-s/-b for multi-input mode")
        
        return "single", [("single", args.file)]
    
    else:
        # Multi-input mode
        input_types = [
            ("data", args.data),
            ("signal", args.signal),
            ("background", args.background)
        ]
        
        valid_inputs = [(name, path) for name, path in input_types if path is not None]
        
        if not valid_inputs:
            raise ValueError("Must specify either:\n"
                           "  - Single input: -f/--file\n"
                           "  - Multi-input: at least one of -d/--data, -s/--signal, -b/--background")
        
        return "multi", valid_inputs


def generate_output_filenames(output_arg):
    """Generate histogram and canvas output filenames.
    
    Args:
        output_arg: Output basename from command line
    
    Returns:
        tuple: (histogram_file, canvas_file)
    """
    # Remove .root extension if provided
    if output_arg.endswith('.root'):
        output_basename = output_arg[:-5]
    else:
        output_basename = output_arg
    
    return f"{output_basename}_histograms.root", f"{output_basename}_canvases.root"


def main():
    parser = argparse.ArgumentParser(description="Generate ROOT file with plots from multiple input types.")

    # Single file input (for backward compatibility)
    parser.add_argument("-f", "--file",
                       help="Path to input ROOT file (.root) or text file containing list of ROOT files (.txt) - single input mode")

    # Three separate input arguments for different data types
    parser.add_argument("-d", "--data",
                       help="Path to data ROOT file (.root) or text file containing list of data ROOT files (.txt)")

    parser.add_argument("-s", "--signal",
                       help="Path to signal ROOT file (.root) or text file containing list of signal ROOT files (.txt)")

    parser.add_argument("-b", "--background",
                       help="Path to background ROOT file (.root) or text file containing list of background ROOT files (.txt)")

    parser.add_argument("--skip-histograms",
                       help="Skip histogram generation and create canvases from existing histogram ROOT file. Specify the histogram ROOT file path.")

    parser.add_argument("-o", "--output", default="output",
                       help="Output file basename (default: output). Will create output_histograms.root and output_canvases.root")

    parser.add_argument("-m", "--memory_size", default=100,
                        help="Total memory used per chunk of data (mB).")

    parser.add_argument("--tree-path", default="tree/llpgtree",
                       help="Tree path within ROOT files (default: tree/llpgtree)")

    parser.add_argument("--plots-dir", default="MasterPlots",
                       help="Directory containing plot configuration subdirectories (default: MasterPlots)")

    args = parser.parse_args()

    try:
        # Validate arguments and determine processing mode
        processing_mode, valid_inputs = validate_arguments(args)

        print(f"Running in {processing_mode}-input mode. "
              f"Will process: {[name for name, _ in valid_inputs]}")
        print(f"Using plots directory: {args.plots_dir}")

        # Generate output file names
        histogram_file, canvas_file = generate_output_filenames(args.output)

        # Handle skip-histograms mode
        if args.skip_histograms:
            if not args.skip_histograms.endswith('.root'):
                print(f"Error: --skip-histograms must specify a ROOT file, got: {args.skip_histograms}")
                return

            if not os.path.exists(args.skip_histograms):
                print(f"Error: Histogram file '{args.skip_histograms}' does not exist.")
                return

            print(f"Skipping histogram generation.")
            print(f"Reading histograms from: {args.skip_histograms}")
            print(f"Creating canvases in: {canvas_file}")
            create_canvases(args.skip_histograms, canvas_file, args.plots_dir)
            print(f"Canvas generation complete. Output saved to: {canvas_file}")
            return

        # Process for generating both histograms and canvases
        with uproot.recreate(histogram_file) as rfile:
            # Process each specified input type
            for input_type, input_file in valid_inputs:
                process_input_files(input_file, input_type, rfile, args)

        # Create canvases after all histograms are saved
        print(f"\n{'='*50}")
        print("Generating canvases from histograms...")
        print(f"{'='*50}")
        create_canvases(histogram_file, canvas_file, args.plots_dir)

        print(f"\nProcessing complete. Output saved to: {canvas_file}")
        print(f"Processed input types: {[name for name, _ in valid_inputs]}")

    except Exception as e:
        print(f"Error during processing: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
