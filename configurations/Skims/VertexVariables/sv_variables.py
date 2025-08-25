import os
import itertools
import uproot
import boost_histogram as bh
import awkward as ak

from tools.plotting import *
from tools.histogram_generator import *

from template.vertex_config_templates import *

def create_histograms(events, file_type):

    label = "SV"
    sv_config = vertex_skims_histogram_config(label)
    category, sample = os.path.split(file_type)
    
    sv_hist_generator = HistogramGenerator(
        sv_config
    )

    return sv_hist_generator.create_histograms(events)

def create_canvases(histograms, file_type):

    category, sample = os.path.split(file_type)
    
    return default_canvases(histograms, "sv")
