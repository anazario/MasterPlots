#from tools.base_module import BaseModule
from tools.histogram_generator import *
from tools.histogram_dictionary import get_variables
from tools.plotting import *
from template.vertex_four_vector_variables import *
        
def vertex_histogram_config(label: str) -> CollectionConfig:

    vertex_config = CollectionConfig(
    prefix=label,
    variables=get_variables(["pt", "eta", "mass", "nTracks", "cosTheta",
                                    "normalizedChi2", "dxy",  "dxyError", "pOverE",
                                    "pOverECosTheta", "sigDxy"]),
    category_masks=["isGold", "isSilver", "isBronze"],
    alternate_masks=["isUnique"],
    derived_variables={
        "pOverE": lambda arrays: (
            arrays[f"{label}_p"] / np.sqrt(arrays[f"{label}_p"]**2 + arrays[f"{label}_mass"]**2)
        ),
        "pOverECosTheta": lambda arrays: (
            arrays[f"{label}_p"] / np.sqrt(arrays[f"{label}_p"]**2 + arrays[f"{label}_mass"]**2) *
            arrays[f"{label}_cosTheta"]
        ),
        "sigDxy": lambda arrays: (
            arrays[f"{label}_dxy"]/arrays[f"{label}_dxyError"]
        ),
    },
    skip_pairs=[
        ("p", "pt"),
        ("pOverE", "pOverECosTheta"),
    ],
    skip_variables=["p", "dxyError"],
    global_filter=lambda arrays: ((arrays[f"{label}_mass"] > 10) & \
                                  (arrays[f"{label}_pOverE"] > 0.6) & \
                                  (arrays[f"{label}_cosTheta"] > 0.75) & \
                                  (arrays[f"{label}_normalizedChi2"] < 5))
    )

    return vertex_config

def candidate_leptonic_histogram_config(label: str) -> CollectionConfig:
    vertex_config = CollectionConfig(
        prefix=label,
        variables=get_variables(["x", "y", "z", "pt", "eta", "mass", "cosTheta", "nTotal",
                                 "dxy", "dxyError", "pOverE", "decayAngle"]),
        category_masks=[],
        alternate_masks=[],
        derived_variables={
            "pOverE": lambda arrays: (
                arrays[f"{label}_p"] / np.sqrt(arrays[f"{label}_p"]**2 + arrays[f"{label}_mass"]**2)
            ),
            "sigDxy": lambda arrays: (
                arrays[f"{label}_dxy"]/arrays[f"{label}_dxyError"]
            ),
        },
        skip_pairs=[
            ("p", "pt"),
            ("x", "dxy"),
            ("y", "dxy")
        ],
        skip_variables=[],
        dependencies=["passLooseMuonID", "passLooseElectronID", "p", "nTracks"],
        global_filter=lambda arrays: ((arrays[f"{label}_nTracks"] == 2) &
                                      #(arrays[f"{label}_matchRatio"] > 0.5) &
                                      ((arrays[f"{label}_passLooseMuonID"]) | (arrays[f"{label}_passLooseElectronID"])))
    )
    return vertex_config

def candidate_hadronic_histogram_config(label: str) -> CollectionConfig:
    vertex_config = CollectionConfig(
        prefix=label,
        variables=get_variables(["x", "y", "z", "pt", "eta", "mass", "nTracks", "cosTheta", "nTotal",
                                 "dxy", "dxyError", "pOverE", "decayAngle"]),
        category_masks=["failLooseID", "all"],#["passLooseID", "failLooseID", "all"],
        alternate_masks=["cosThetaPlus"],# "cosThetaMinus"],
        derived_variables={
            "pOverE": lambda arrays: (
                arrays[f"{label}_p"] / np.sqrt(arrays[f"{label}_p"]**2 + arrays[f"{label}_mass"]**2)
            ),
            "sigDxy": lambda arrays: (
                arrays[f"{label}_dxy"]/arrays[f"{label}_dxyError"]
            ),
            "massOverNTracks": lambda arrays: (
                arrays[f"{label}_mass"] / arrays[f"{label}_nTracks"]
            ),
            "passLooseID": lambda arrays: (
                (arrays[f"{label}_massOverNTracks"] > 1.2)# & (arrays[f"{label}_cosTheta"] < 0.995)
            ),
            "failLooseID": lambda arrays: (
		(arrays[f"{label}_massOverNTracks"] < 0.8) & (arrays[f"{label}_dxy"] > 1.9) #& (arrays[f"{label}_cosTheta"] > 0.995)
	    ),
            "cosThetaPlus": lambda arrays: (
                (arrays[f"{label}_cosTheta"] > 0.995)
            ),
             "cosThetaMinus": lambda arrays: (
                (arrays[f"{label}_cosTheta"] < 0.995)
	    ),
            "all": lambda arrays: (
                (arrays[f"{label}_passLooseID"]) | ~(arrays[f"{label}_passLooseID"])
            )
            
        },
        skip_pairs=[
            ("p", "pt"),
            ("x", "dxy"),
            ("y", "dxy")
        ],
        skip_variables=["passLooseID", "failLooseID", "all", "cosThetaPlus", "cosThetaMinus"],
        dependencies=["p"],
        global_filter=lambda arrays: ((arrays[f"{label}_nTracks"] >= 3))# &
                                      #(arrays[f"{label}_matchRatio"] > 0.5))

    )
    return vertex_config

def vertex_track_histogram_config(label: str) -> CollectionConfig:

    vertex_track_config = CollectionConfig(
        prefix=label,
        variables=get_variables(["p", "mass", "nTracks", "cosTheta", "normalizedChi2", "trackCosTheta", "trackCompatibility"]),# "trackCosThetaAtCM"]),
        category_masks=[
            MaskConfig(name="isGold", mapping_index="vertexIndex"),
            MaskConfig(name="isSilver", mapping_index="vertexIndex"),
            MaskConfig(name="isBronze", mapping_index="vertexIndex"),
        ],
        alternate_masks=["isUnique"],
        derived_variables={
            "pOverE": lambda arrays: (
                arrays[f"{label}_p"] / np.sqrt(arrays[f"{label}_p"]**2 + arrays[f"{label}_mass"]**2)
            ),
        },
        global_filter=lambda arrays: (
            (arrays[f"{label}_mass"] > 10) & \
            (arrays[f"{label}_pOverE"] > 0.6) & \
            (arrays[f"{label}_cosTheta"] > 0.75) & \
            (arrays[f"{label}_normalizedChi2"] < 5)
        ),
        skip_variables=["p", "mass", "nTracks", "pOverE", "cosTheta", "normalizedChi2"],
    )

    return vertex_track_config

def default_canvases(histograms, label):

    canvases = {}
    for name, hist in histograms.items():
        canvas_name = f"{label}_{name}"
        if "_vs_" in name:  # Convention for 2D histograms
            hist2D = histograms[name]

            # Split the name to extract x and y variables
            y_part, x_part = name.split("_vs_")
            yname = y_part.split("_")[-1]  # Extract the variable preceding "_vs_"
            xname = x_part.split("_")[0]  # Extract the variable following "_vs_"
            
            # Generate the canvas
            canvas = Plot.plot_histogram(hist2D, canvas_name, xname, yname)
            canvases[f"{canvas_name}"] = canvas

        else:
            canvas = Plot.plot_histogram1D(hist, canvas_name, name)
            canvases[f"{canvas_name}"] = canvas

    return canvases

def default_canvases_with_categories(histograms, categories, alternates, label):
    canvases = {}
    variables = {key.split("_")[-1] for key in histograms.keys() if "_" in key}

    for variable in variables:
        for alternate in alternates:
            hist_group = [
                histograms[f"{category}_{alternate}_{variable}"]
                for category in categories
                if f"{category}_{alternate}_{variable}" in histograms
            ]

            if hist_group: 
                labels = [category.capitalize() for category in categories
                          if f"{category}_{alternate}_{variable}" in histograms]
                name = f"{alternate}_{variable}_overlay"
                xlabel = variable
                canvas = Plot.plot_histograms(hist_group, labels, f"{label}_"+name, xlabel)
                canvases[f"{name}"] = canvas


    for name, hist in histograms.items():
        if "_vs_" in name: 
            hist2D = histograms[name]

            y_part, x_part = name.split("_vs_")
            yname = y_part.split("_")[-1]
            xname = x_part.split("_")[0] 

            canvas = Plot.plot_histogram(hist2D, f"{label}_"+name, xname, yname)
            canvases[f"{name}"] = canvas

    return canvases

def vertex_skims_histogram_config(label: str) -> CollectionConfig:

    vertex_config = CollectionConfig(
    prefix=label,
    variables=get_variables(["cosTheta", "decayAngle", "dxy", "dxySig", "mass", "massOverNtracks",
                             "nTracks", "pOverE"]),
    category_masks=["short", "medium", "long"],
    #alternate_masks=[],
    alternate_masks=["leptonic", "hadronic"],
    dependencies=["nElectron", "nHadronic", "nLeptonic", "nMuon"],
    derived_variables={
        "short": lambda arrays: (
            arrays[f"{label}_dxy"] < 6
        ),
        "medium": lambda arrays: (
            (arrays[f"{label}_dxy"] > 6) & (arrays[f"{label}_dxy"] < 15)
        ),
        "long": lambda arrays: (
            arrays[f"{label}_dxy"] > 15
        ),
        "leptonic": lambda arrays: (
            arrays[f"{label}_nTracks"] == 2
        ),
        "hadronic": lambda arrays: (
            arrays[f"{label}_nTracks"] > 4 
        ),
        "massOverNtracks": lambda arrays: (
            arrays[f"{label}_mass"]/arrays[f"{label}_nTracks"]
        ),
    },
    skip_pairs=[],
    skip_variables=["short", "medium", "long", "leptonic", "hadronic"],
    )

    return vertex_config



    
