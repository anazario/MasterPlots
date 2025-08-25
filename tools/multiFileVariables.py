import uproot
import awkward as ak
import numpy as np

def get_variable_data_from_file(file_path, branch_name, mask_names):

    try:
        with uproot.open(file_path) as file_obj:
            branches = list(mask_names)
            branches.append(branch_name)

            tree = file_obj["tree/llpgtree"]
            data = tree.arrays(branch_name, library="ak")
