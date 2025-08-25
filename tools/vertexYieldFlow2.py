import uproot
import ROOT
import numpy as np
import awkward as ak

ROOT.gROOT.SetBatch(True)

# --- Configuration for File Paths and Branches ---

TREE_NAME = "tree/llpgtree"

# Leptonic Decay Configuration
LEPTONIC_STAGE_BRANCHES = {
    'Seeding': 'Vertex_isSeed',
    'Merging': 'Vertex_isMerged',
    'Cleaning': 'Vertex_isCleaned',
    'Disambiguation': 'Vertex_isDisambiguated',
    'FinalCandidate': 'Vertex_isFinalCandidate',
    'LooseID': None # Handled with custom logic below
}
LEPTONIC_GOLD_BRANCH = 'Vertex_isGold'
LEPTON_ID_DEPENDENCY_BRANCHES = ['Vertex_isFinalCandidate', 'Vertex_passLooseMuonID', 'Vertex_passLooseElectronID']

# Hadronic Decay Configuration
HADRONIC_STAGE_BRANCHES = {
        'Seeding': 'Vertex_isSeed',
        'Merging': 'Vertex_isMerged',
        'Disambiguation': 'Vertex_isDisambiguated',
        'FinalCandidate': 'Vertex_isFinalCandidate',
        'LooseID': None
}
HADRONIC_DEPENDENCIES =  ['Vertex_mass', 'Vertex_nTracks']
HADRONIC_MATCH_RATIO_BRANCH = 'Vertex_matchRatio'
HADRONIC_MATCH_RATIO_THRESHOLD = 0.5

# File paths
LEPTONIC_FILES = {
    'signal_sip2d_geq1': {'path': 'root/SMS-GlGl_mGl-1p0_mN2-250_Zll_ct1-10_sip2DMuonEnhancedGeq1_splitByStage.root', 'is_signal': True, 'label': 'Signal (Sip2D > 1)'},
    'signal_sip2d_geq2': {'path': 'root/SMS-GlGl_mGl-1p0_mN2-250_Zll_ct1-10_sip2DMuonEnhancedGeq2_splitByStage.root', 'is_signal': True, 'label': 'Signal (Sip2D > 2)'},
    'signal_sip2d_geq4': {'path': 'root/SMS-GlGl_mGl-1p0_mN2-250_Zll_ct1-10_sip2DMuonEnhanced_spliByStage.root', 'is_signal': True, 'label': 'Signal (Sip2D > 4)'},
    'signal_muon': {'path': 'root/SMS-GlGl_mGl-1p0_mN2-250_Zll_ct1-10_MuonEnhanced_spliByStage.root', 'is_signal': True, 'label': 'Signal (PV Association)'},
    'background_sip2d_geq1': {'path': 'root/WJets_Sip2DMuonEnhancedGeq1_splitByStage.root', 'is_signal': False, 'label': 'Background (Sip2D > 1)'},
    'background_sip2d_geq2': {'path': 'root/WJets_Sip2DMuonEnhancedGeq2_splitByStage.root', 'is_signal': False, 'label': 'Background (Sip2D > 2)'},
    'background_sip2d_geq4': {'path': 'root/WJets_Sip2DMuonEnhanced_splitByStage.root', 'is_signal': False, 'label': 'Background (Sip2D > 4)'},
    'background_muon': {'path': 'root/WJets_MuonEnhanced_splitByStage.root', 'is_signal': False, 'label': 'Background (PV Association)'},
}

HADRONIC_FILES = {
        'signal_had_1': {'path': 'root/SMS-GlGl_mGl-1500_mN2-500_mN1-100_Zff_N2ctau-ct10_splitByStage.root', 'is_signal': True, 'label': 'Signal (PV Association)'},
        'signal_had_2': {'path': 'root/SMS-GlGl_mGl-1500_mN2-500_mN1-100_Zff_N2ctau-ct10_Sip2DGeq4_splitByStage.root', 'is_signal': True, 'label': 'Signal (Sip2D > 4)'},
        'signal_had_3': {'path': 'root/SMS-GlGl_mGl-1500_mN2-500_mN1-100_Zff_N2ctau-ct10_Sip2DGeq2_splitByStage.root', 'is_signal': True, 'label': 'Signal (Sip2D > 2)'},
        'background_had_1': {'path': 'root/WJets_MuonEnhancedHad_splitByStage.root', 'is_signal': False, 'label': 'Background (PV Association)'},
        'background_had_2': {'path': 'root/WJets_Sip2DMuonEnhancedHad_splitByStage.root', 'is_signal': False, 'label': 'Background (Sip2D > 4)'},
        'background_had_3': {'path': 'root/WJets_Sip2DMuonEnhancedHadGeq2_splitByStage.root', 'is_signal': False, 'label': 'Background (Sip2D > 2)'}
}

# Colors and markers
COLORS = [
    ROOT.kBlue, ROOT.kRed, ROOT.kGreen+2, ROOT.kMagenta+2, ROOT.kOrange+7,
    ROOT.kCyan+2, ROOT.kViolet+5, ROOT.kAzure+5, ROOT.kPink+1, ROOT.kSpring+8
]
MARKERS = [
    20, 21, 22, 23, 29, # Solid circles, squares, triangles, diamonds, stars
    34, 25, 26, 27, 28  # Cross, open square, open circle, open triangle, open diamond
]
LINE_STYLES_SIGNAL = [1] * len(COLORS) # All solid for signal
LINE_STYLES_BACKGROUND = [2] * len(COLORS) # All dashed for background

def CMSmark(plot_title: str = "") -> None:
        latex = ROOT.TLatex()
        latex.SetTextFont(42)
        latex.SetNDC()
        latex.SetTextSize(0.035)
        latex.SetTextFont(42)
        latex.DrawLatex(0.51, 0.91, plot_title)
        latex.SetTextSize(0.04)
        latex.SetTextFont(42)
        latex.DrawLatex(0.12, 0.915, "#bf{CMS} #it{Preliminary}")

# --- Data Extraction Function ---

def get_yields(file_path, decay_type, is_signal):
    """
    Extracts yields for each stage from a ROOT file based on decay_type.
    Args:
        file_path (str): Path to the ROOT file.
        decay_type (str): 'leptonic' or 'hadronic'.
        is_signal (bool): True if it's a signal file, False otherwise.
    Returns:
        dict: A dictionary where keys are stage names and values are their yields.
    """
    
    # Determine which stages and branches to use based on decay_type
    if decay_type == 'leptonic':
        current_stage_branches_dict = LEPTONIC_STAGE_BRANCHES
        signal_cut_branch = LEPTONIC_GOLD_BRANCH
        additional_branches = LEPTON_ID_DEPENDENCY_BRANCHES # Corrected variable name
    elif decay_type == 'hadronic':
        current_stage_branches_dict = HADRONIC_STAGE_BRANCHES
        signal_cut_branch = HADRONIC_MATCH_RATIO_BRANCH
        additional_branches = HADRONIC_DEPENDENCIES # Not needed for hadronic
    else:
        raise ValueError(f"Invalid decay_type: {decay_type}. Must be 'leptonic' or 'hadronic'.")

    yields_data = {stage: 0 for stage in current_stage_branches_dict.keys()}
    branches_to_load = []

    # Collect all branches needed for the current decay_type and signal status
    for branch_name in current_stage_branches_dict.values():
        if branch_name: # Add all explicit stage branches
            branches_to_load.append(branch_name)
    
    branches_to_load.extend(additional_branches) # Add additional dependencies
    
    if is_signal:
        branches_to_load.append(signal_cut_branch) # Add the signal definition branch

    branches_to_load = list(set(branches_to_load)) # Remove duplicates

    try:
        with uproot.open(file_path) as file_obj:
            tree = file_obj[TREE_NAME]
            data = tree.arrays(branches_to_load, library="ak") # Load data as awkward array

            for stage_name, branch_name in current_stage_branches_dict.items():
                # Handle custom LeptonID stage for leptonic decays
                if stage_name == 'LooseID' and decay_type == 'leptonic':
                        final_candidate_data = ak.to_numpy(ak.flatten(data['Vertex_isFinalCandidate'])).astype(bool)
                        pass_loose_muon_id = ak.to_numpy(ak.flatten(data['Vertex_passLooseMuonID'])).astype(bool)
                        pass_loose_electron_id = ak.to_numpy(ak.flatten(data['Vertex_passLooseElectronID'])).astype(bool)
                        
                        lepton_id_condition = pass_loose_muon_id | pass_loose_electron_id
                        current_stage_mask = final_candidate_data & lepton_id_condition
                        
                        if is_signal: # Apply leptonic gold cut
                                gold_data = ak.to_numpy(ak.flatten(data[LEPTONIC_GOLD_BRANCH])).astype(bool)
                                final_mask_for_yield = current_stage_mask & gold_data
                        else: # Background file
                                final_mask_for_yield = current_stage_mask
                    
                        yields_data[stage_name] = np.sum(final_mask_for_yield)

                elif stage_name == 'LooseID' and decay_type == 'hadronic':
                        final_candidate_data = ak.to_numpy(ak.flatten(data['Vertex_isFinalCandidate'])).astype(bool)
                        data["massOverNTracks"] = data["Vertex_mass"]/data["Vertex_nTracks"]
                        pass_mass_nTracks_ratio_mask = data["massOverNTracks"] > 1
                        pass_mass_nTracks_ratio_cut = ak.to_numpy(ak.flatten(pass_mass_nTracks_ratio_mask)).astype(bool)
                        
                        current_stage_mask = final_candidate_data & pass_mass_nTracks_ratio_cut
                        
                        if is_signal:
                                match_ratio_data = ak.to_numpy(ak.flatten(data[HADRONIC_MATCH_RATIO_BRANCH]))
                                match_ratio_cut_mask = (match_ratio_data > HADRONIC_MATCH_RATIO_THRESHOLD)
                                final_mask_for_yield = current_stage_mask & match_ratio_cut_mask
                        else:
                                final_mask_for_yield = current_stage_mask

                        yields_data[stage_name] = np.sum(final_mask_for_yield)
                        
                # Handle all other standard stages (Seeding, Merging, Disambiguation, FinalCandidate, Cleaning)
                elif branch_name: # Ensure it's not a None placeholder
                    stage_data_ak = data[branch_name]
                    flat_stage_data = ak.to_numpy(ak.flatten(stage_data_ak)).astype(bool)

                    if is_signal:
                        if decay_type == 'leptonic':
                            gold_data = ak.to_numpy(ak.flatten(data[LEPTONIC_GOLD_BRANCH])).astype(bool)
                            final_filtered_data = flat_stage_data[gold_data]
                        elif decay_type == 'hadronic':
                            match_ratio_data = ak.to_numpy(ak.flatten(data[HADRONIC_MATCH_RATIO_BRANCH]))
                            match_ratio_cut_mask = (match_ratio_data > HADRONIC_MATCH_RATIO_THRESHOLD)
                                                    
                            # Ensure both arrays are of the same length before applying mask
                            if len(flat_stage_data) != len(match_ratio_cut_mask):
                                print(f"Warning: Length mismatch in {file_path} for stage {stage_name} (data: {len(flat_stage_data)},\
                                match_ratio_cut: {len(match_ratio_cut_mask)}). Proceeding, but verify if this is expected.")
                                # A more robust handling might involve filtering events before flattening,
                                # or ensuring a one-to-one vertex correspondence.
                                # For now, numpy will attempt broadcasting or raise error if shapes are truly incompatible.
                            final_filtered_data = flat_stage_data[match_ratio_cut_mask]
                        else: # Should not happen due to initial validation
                            final_filtered_data = flat_stage_data
                    else: # Background file (no signal-specific cut)
                        final_filtered_data = flat_stage_data

                    yields_data[stage_name] = np.sum(final_filtered_data)
                # If branch_name is None (e.g., LeptonID in hadronic), it's skipped by this 'elif'
            
    except Exception as e:
        print(f"Error processing file {file_path} (Decay Type: {decay_type}): {e}")
        # On error, return a dictionary with zeros for all relevant stages
        for stage in current_stage_branches_dict.keys():
            yields_data[stage] = 0
    return yields_data

# --- Plotting Utility Function ---

def plot_yields_on_canvas(canvas, plot_data, stage_names, title):
    """
    Draws yield graphs on a given PyROOT TCanvas.
    Args:
        canvas (ROOT.TCanvas): The canvas to draw on.
        plot_data (list of dict): List of dictionaries, each containing 'yields', 'label', 'color_idx', 'marker_idx'.
        stage_names (list): Ordered list of stage names for X-axis labels.
        title (str): Title for the plot.
    """
    canvas.cd() # Make sure this canvas is the active one
    canvas.Clear() # Clear any previous content if reusing canvas
    canvas.SetLogy(1) # Logarithmic Y-axis
    canvas.SetGridx(1) # Enable X grid
    canvas.SetGridy(1) # Enable Y grid
    canvas.SetTicks(1, 1)

    minY = 60
    n_stages = len(stage_names)
    canvas.h_dummy = ROOT.TH1F(f"h_dummy_{canvas.GetName()}", title, n_stages, 0.5, n_stages + 0.5)
    canvas.h_dummy.SetMinimum(minY) # Minimum for log scale
    canvas.h_dummy.GetXaxis().SetTitle("Algorithm Stage")
    canvas.h_dummy.GetYaxis().SetTitle("Total Vertex Yield")
    canvas.h_dummy.GetXaxis().CenterTitle(True)
    canvas.h_dummy.GetYaxis().CenterTitle(True)
    canvas.h_dummy.GetXaxis().SetTitleOffset(1.2)
    canvas.h_dummy.SetStats(0) # Remove stat box

    # Set X-axis bin labels
    for i, stage_name in enumerate(stage_names):
        canvas.h_dummy.GetXaxis().SetBinLabel(i + 1, stage_name)
    
    # Calculate dynamic Y-axis maximum
    all_yields_for_plot = []
    for entry in plot_data:
        all_yields_for_plot.extend(list(entry['yields'].values()))

    max_overall_yield = 1.0 
    positive_yields = [y for y in all_yields_for_plot if y > 0]
    if positive_yields:
        max_overall_yield = max(positive_yields)
    canvas.h_dummy.SetMaximum(max_overall_yield * 2)

    canvas.h_dummy.Draw("AXIS") # Draw only the axes

    graphs = []
    canvas.multigraph = ROOT.TMultiGraph()
    for i, entry in enumerate(plot_data):
        current_yields = list(entry['yields'].values())
        
        # Ensure yields list has values for all stages; fill with 0 if missing
        if len(current_yields) != n_stages:
            print(f"Warning: Yields for {entry['label']} do not match expected number of stages ({len(current_yields)} vs {n_stages}). Filling missing with 0.")
            current_yields_filled = current_yields + [0] * (n_stages - len(current_yields))
        else:
            current_yields_filled = current_yields

        x_coords = np.arange(1, n_stages + 1).astype(float)
        y_coords = np.array(current_yields_filled, dtype=float)

        graph = ROOT.TGraph(n_stages, x_coords, y_coords)
        graph.SetTitle(entry['label'])
        graph.SetMarkerColor(COLORS[entry['color_idx'] % len(COLORS)]) # Use modulo to cycle if more data lines than colors
        graph.SetLineColor(COLORS[entry['color_idx'] % len(COLORS)])
        graph.SetMarkerStyle(MARKERS[entry['marker_idx'] % len(MARKERS)]) # Use modulo to cycle
        graph.SetLineWidth(2)
        
        # Determine line style based on whether it's signal or background
        # You can add an 'is_signal' flag to plot_data entries for more robust check
        if 'signal' in entry['label'].lower():
            graph.SetLineStyle(LINE_STYLES_SIGNAL[entry['color_idx'] % len(LINE_STYLES_SIGNAL)])
        else:
            graph.SetLineStyle(LINE_STYLES_BACKGROUND[entry['color_idx'] % len(LINE_STYLES_BACKGROUND)])

        #graph.Draw("LP SAME")
        graphs.append(graph)
        canvas.multigraph.Add(graph)

    canvas.multigraph.Draw("lp")
    # Create a legend
    # Adjust legend position if it overlaps with plot elements
    canvas.legend = ROOT.TLegend(0.6, 0.7, 0.88, 0.88)
    canvas.legend.SetFillStyle(0)
    canvas.legend.SetBorderSize(0)
    #canvas.legend.SetNColumns(2)
    for graph in graphs:
        canvas.legend.AddEntry(graph, graph.GetTitle(), "lp")
    canvas.legend.Draw()

    for i, stage_name in enumerate(stage_names):
        if i == 0: continue
        x = i+0.5
        line = ROOT.TLine(x, minY, x, max_overall_yield * 2)
        line.SetLineStyle(3)  # Style 3 = dotted
        line.SetLineColor(ROOT.kGray+2)
        line.Draw()
        canvas._lines = getattr(canvas, '_lines', []) + [line]

    # Draw horizontal lines at each power of 10 (log scale)
    log_min = minY*10 
    log_max = max_overall_yield * 2
    
    # Determine powers of 10 in the plotting range
    log_min_exp = int(np.floor(np.log10(log_min)))
    log_max_exp = int(np.ceil(np.log10(log_max)))
    
    for exp in range(log_min_exp, log_max_exp):
        y = 10**exp
        line = ROOT.TLine(0.5, y, n_stages + 0.5, y)
        line.SetLineStyle(3)  # Dotted
        line.SetLineColor(ROOT.kGray+2)
        line.Draw()
        canvas._hlines = getattr(canvas, '_hlines', []) + [line]  # prevent GC
        
    CMSmark()
    canvas.Update()

# --- Main Execution ---

if __name__ == '__main__':
    # Initialize a ROOT file to save canvases
    output_root_file = ROOT.TFile("vertex_yield_comparison_plots.root", "RECREATE")

    # --- Process and Plot Leptonic Decays ---
    leptonic_plot_data = []
    color_idx_leptonic = 0
    marker_idx_leptonic = 0
    for key, info in LEPTONIC_FILES.items():
        yields = get_yields(info['path'], 'leptonic', info['is_signal'])
        leptonic_plot_data.append({
            'yields': yields,
            'label': info['label'],
            'color_idx': color_idx_leptonic,
            'marker_idx': marker_idx_leptonic
        })
        color_idx_leptonic += 1
        marker_idx_leptonic += 1

    # Create and draw on canvas for leptonic
    canvas_leptonic = ROOT.TCanvas("canvas_leptonic", "Leptonic Z-Decay Vertex Yields", 1000, 700)
    plot_yields_on_canvas(canvas_leptonic, leptonic_plot_data, list(LEPTONIC_STAGE_BRANCHES.keys()), "Leptonic Z-Decay Vertex Yields Across Algorithm Stages")
    canvas_leptonic.Write() # Save canvas to ROOT file

    # --- Process and Plot Hadronic Decays ---
    hadronic_plot_data = []
    # Using separate indices for hadronic to reuse initial colors/markers
    color_idx_hadronic = 0
    marker_idx_hadronic = 0
    for key, info in HADRONIC_FILES.items():
        yields = get_yields(info['path'], 'hadronic', info['is_signal'])
        hadronic_plot_data.append({
            'yields': yields,
            'label': info['label'],
            'color_idx': color_idx_hadronic,
            'marker_idx': marker_idx_hadronic
        })
        color_idx_hadronic += 1
        marker_idx_hadronic += 1

    # Create and draw on canvas for hadronic
    canvas_hadronic = ROOT.TCanvas("canvas_hadronic", "Hadronic Z-Decay Vertex Yields", 1000, 700)
    plot_yields_on_canvas(canvas_hadronic, hadronic_plot_data, list(HADRONIC_STAGE_BRANCHES.keys()), "Hadronic Z-Decay Vertex Yields Across Algorithm Stages")
    canvas_hadronic.Write() # Save canvas to ROOT file

    # Close the ROOT file
    output_root_file.Close()
    print("Plots saved to vertex_yield_comparison_plots.root")

