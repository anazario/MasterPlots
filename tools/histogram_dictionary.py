import awkward as ak
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable

@dataclass
class HistogramConfig:
    bins: int = 100
    start: float = 0
    stop: float = 1
    mapping_required: bool = False

# Central dictionary of all possible variable configurations
VARIABLES = {
    "p": HistogramConfig(bins=100, start=0, stop=200),
    "pt": HistogramConfig(bins=100, start=0, stop=200),
    "eta": HistogramConfig(bins=100, start=-4, stop=4),
    "mass": HistogramConfig(bins=100, start=0, stop=150),
    "nTracks": HistogramConfig(bins=20, start=0, stop=20),
    "cosTheta": HistogramConfig(bins=100, start=0.75, stop=1),
    "normalizedChi2": HistogramConfig(bins=100, start=0, stop=5),
    "dxy": HistogramConfig(bins=100, start=0, stop=50),
    "dxyError": HistogramConfig(bins=100, start=0, stop=5),
    "pOverE": HistogramConfig(bins=100, start=0, stop=1),
    "pOverECosTheta": HistogramConfig(bins=100, start=0, stop=1),
    "decayAngle": HistogramConfig(bins=100, start=-1, stop=1),
    "beta": HistogramConfig(bins=100, start=0, stop=1),
    "sigDxy": HistogramConfig(bins=100, start=0, stop=200),
    # Add any track-specific variables with vertex_to_track=True
    "trackCosTheta": HistogramConfig(bins=100, start=-1, stop=1, mapping_required=True),
    "trackCosThetaAtCM": HistogramConfig(bins=100, start=-1, stop=1, mapping_required=True),
    "trackCompatibility": HistogramConfig(bins=100, start=0, stop=5, mapping_required=True),
    "shiftDzAfterTrackRemoval": HistogramConfig(bins=100, start=0, stop=1, mapping_required=True),
    "shift3DAfterTrackRemoval":	HistogramConfig(bins=100, start=0, stop=1, mapping_required=True),
    # Track variables (not vertex specific)
    "ptRes": HistogramConfig(bins=100, start=0, stop=0.5),
}

def get_variables(variable_names: List[str]) -> Dict[str, HistogramConfig]:
    """
    Get a subset of vertex variable configurations based on provided names.
    
    Args:
        variable_names: List of variable names to include
        
    Returns:
        Dictionary of variable configurations for the requested variables
    
    Raises:
        KeyError: If a requested variable name isn't in VERTEX_VARIABLES
    """
    return {name: VARIABLES[name] for name in variable_names}

