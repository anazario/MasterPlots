import os
import glob

def parse_input_files(input_arg, tree_suffix=":tree/llpgtree"):
    """Parse input: wildcard, .txt list, or .root file."""
    if '*' in input_arg:
        matched_files = glob.glob(input_arg)
        if not matched_files:
            raise ValueError(f"No files matched pattern: {input_arg}")
        return [f + tree_suffix for f in matched_files]

    elif input_arg.endswith('.txt'):
        if not os.path.exists(input_arg):
            raise FileNotFoundError(f"File list '{input_arg}' does not exist.")
        with open(input_arg, 'r') as f:
            return [line.strip() + tree_suffix for line in f if line.strip()]

    elif input_arg.endswith('.root'):
        if not os.path.exists(input_arg):
            raise FileNotFoundError(f"Input file '{input_arg}' does not exist.")
        return [input_arg + tree_suffix]

    else:
        raise ValueError(f"Unsupported input type: {input_arg}")


def get_valid_subdirectories(master_plots_dir, skip_dirs=None):
    if skip_dirs is None:
        skip_dirs = {"__pycache__", "template", "test", "tools", "plots", ".git"}
    
    if not os.path.exists(master_plots_dir):
        raise FileNotFoundError(f"Master plots directory '{master_plots_dir}' does not exist.")
    
    subdirs = [
        d for d in os.listdir(master_plots_dir)
        if os.path.isdir(os.path.join(master_plots_dir, d)) and d not in skip_dirs
    ]

    if not subdirs:
        raise ValueError(f"No valid subdirectories found in '{master_plots_dir}'")

    return subdirs
