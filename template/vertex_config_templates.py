#from tools.base_module import BaseModule
from tools.histogram_generator import *
from tools.histogram_dictionary import get_variables
from template.vertex_four_vector_variables import *
        
def vertex_histogram_config(label: str) -> CollectionConfig:

    vertex_config = CollectionConfig(
    prefix=label,
    variables=get_variables(["p", "pt", "eta", "mass", "nTracks", "cosTheta",
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

