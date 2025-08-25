import awkward as ak
import vector
import uproot
import numpy as np

def calculate_pair_vertex_track_four_vectors(branches, label="VertexCand"):

    # Register awkward with vector
    vector.register_awkward()

    pair_vertex_mask = branches[f"{label}_nTracks"] == 2

    # Since the vertices are ordered by multiplicity find the last index that has a pair vertex
    pair_vertex_indices = ak.fill_none(
        ak.mask(
            ak.local_index(branches[f"{label}_nTracks"]), pair_vertex_mask), -1
    )

    # Build a new list the contains the largest pair vertex index
    last_index_position = pair_vertex_indices[ak.argmax(pair_vertex_indices, axis=1, keepdims=True)]

    # Scale the indices by 2 to account for the two tracks
    scaled_indices = 2 * ak.flatten(last_index_position) + 1

    # Select the vertex indices assigned per track that match the range of the scaled indices
    track_to_pair_vertex_indices = ak.local_index(branches[f"{label}_vertexIndex"]) <= scaled_indices[:, None]

    # Reserve 2 times the size of vertices in each event for each track pair to conserve vertex dimensions
    tracks_length_buffer_size = ak.num(pair_vertex_mask)*2
    tracks_length_buffer_mask = ak.local_index(track_to_pair_vertex_indices) < tracks_length_buffer_size

    # Get the pair vertex index mappings between tracks and vertices and the tracks and the general track collection
    pair_vertex_track_to_vertex_indices = ak.mask(branches[f"{label}_vertexIndex"], track_to_pair_vertex_indices)[tracks_length_buffer_mask]
    pair_vertex_track_to_track_indices = ak.mask(branches[f"{label}_trackIndex"], track_to_pair_vertex_indices)[tracks_length_buffer_mask]

    # Create the track four-vectors
    tracks = ak.zip(
        {"px": branches["Track_px"][pair_vertex_track_to_track_indices],
         "py": branches["Track_py"][pair_vertex_track_to_track_indices],
         "pz": branches["Track_pz"][pair_vertex_track_to_track_indices],
         "mass": ak.zeros_like(branches["Track_px"][pair_vertex_track_to_track_indices])},
        with_name="Momentum4D",
    )

    # Split tracks into two sets containing the complementary partners and add their four-vectors together
    tracks_first = tracks[:, ::2]
    tracks_second = tracks[:, 1::2]

    return tracks_first, tracks_second

"""
def calculate_pair_vertex_track_four_vectors(events, label="VertexCand"):
    
    # Register awkward with vector
    vector.register_awkward()

    # Get track and vertex branches and set up mask to select two track vertices
    track_branches = events.arrays(filter_name="Track_p[xyz]")
    vertex_branches = events.arrays([f"{label}_vertexIndex", f"{label}_trackIndex", f"{label}_nTracks"])
    pair_vertex_mask = vertex_branches[f"{label}_nTracks"] == 2

    # Since the vertices are ordered by multiplicity find the last index that has a pair vertex
    pair_vertex_indices = ak.fill_none(
        ak.mask(
            ak.local_index(vertex_branches[f"{label}_nTracks"]), pair_vertex_mask), -1
    )

    # Build a new list the contains the largest pair vertex index
    #last_index_position = pair_vertex_indices[:, -1:]
    last_index_position = pair_vertex_indices[ak.argmax(pair_vertex_indices, axis=1, keepdims=True)]

    # Scale the indices by 2 to account for the two tracks
    scaled_indices = 2 * ak.flatten(last_index_position) + 1
    
    # Select the vertex indices assigned per track that match the range of the scaled indices
    track_to_pair_vertex_indices = ak.local_index(vertex_branches[f"{label}_vertexIndex"]) <= scaled_indices[:, None]

    # Reserve 2 times the size of vertices in each event for each track pair to conserve vertex dimensions
    tracks_length_buffer_size = ak.num(pair_vertex_mask)*2
    tracks_length_buffer_mask = ak.local_index(track_to_pair_vertex_indices) < tracks_length_buffer_size
    
    # Get the pair vertex index mappings between tracks and vertices and the tracks and the general track collection
    pair_vertex_track_to_vertex_indices = ak.mask(vertex_branches[f"{label}_vertexIndex"], track_to_pair_vertex_indices)[tracks_length_buffer_mask]
    pair_vertex_track_to_track_indices = ak.mask(vertex_branches[f"{label}_trackIndex"], track_to_pair_vertex_indices)[tracks_length_buffer_mask]

    # Create the track four-vectors
    tracks = ak.zip(
        {"px": track_branches.Track_px[pair_vertex_track_to_track_indices],
         "py": track_branches.Track_py[pair_vertex_track_to_track_indices],
         "pz": track_branches.Track_pz[pair_vertex_track_to_track_indices],
         "mass": ak.zeros_like(track_branches.Track_px[pair_vertex_track_to_track_indices])},
        with_name="Momentum4D",
    )

    # Split tracks into two sets containing the complementary partners and add their four-vectors together
    tracks_first = tracks[:, ::2]
    tracks_second = tracks[:, 1::2]
    
    return tracks_first, tracks_second
""" 
def calculate_pair_vertex_four_vectors(branches, label="VertexCand"):

    tracks_first, tracks_second = calculate_pair_vertex_track_four_vectors(branches, label)
    pair_vertices = tracks_first + tracks_second

    return pair_vertices

def calculate_pair_vertex_decay_angles(events, label="VertexCand"):

    tracks_first, tracks_second = calculate_pair_vertex_track_four_vectors(events, label)
    pair_vertices = tracks_first + tracks_second
    
    # Boost first set of tracks to their pair vertex CM frame and calculate the decay angles
    beta_cm_boost = pair_vertices.to_beta3()
    boosted_tracks_first = tracks_first.boostCM_of_p4(pair_vertices)
    beta_boosted_tracks = boosted_tracks_first.to_beta3()

    decay_angles = beta_boosted_tracks.dot(pair_vertices.to_beta3())/(beta_cm_boost.mag*beta_boosted_tracks.mag) 
    
    return decay_angles

def calculate_pair_vertex_beta_cm_magnitude(events, label="VertexCand"):

    pair_vertices = calculate_pair_vertex_four_vectors(events, label)
    pair_vertex_cm_beta_vector = pair_vertices.to_beta3()
    return pair_vertex_cm_beta_vector.mag

"""
def calculate_boosted_cosine_angle(events, label="VertexCand"):

    # Register awkward with vector
    vector.register_awkward()

    # Get track and vertex branches and set up mask to select two track vertices
    track_branches = events.arrays(filter_name="Track_p[xyz]")
    vertex_branches = events.arrays([f"{label}_vertexIndex",
                                     f"{label}_trackIndex",
                                     f"{label}_nTracks",
                                     f"{label}_px",
                                     f"{label}_py",
                                     f"{label}_pz",
                                     f"{label}_mass"])


    track_to_vertex_indices = vertex_branches[f"{label}_vertexIndex"]
    
    track_projected_vertices = ak.zip(
        {"px": vertex_branches[f"{label}_px"][track_to_vertex_indices],
         "py": vertex_branches[f"{label}_py"][track_to_vertex_indices],
         "pz": vertex_branches[f"{label}_pz"][track_to_vertex_indices],
         "mass": vertex_branches[f"{label}_mass"][track_to_vertex_indices]},
        with_name="Momentum4D",
    )

    track_to_track_indices = vertex_branches[f"{label}_trackIndex"]
    
    tracks = ak.zip(
        {"px": track_branches.Track_px[track_to_track_indices],
         "py": track_branches.Track_py[track_to_track_indices],
         "pz": track_branches.Track_pz[track_to_track_indices],
         "mass": ak.zeros_like(track_branches.Track_px[track_to_track_indices])},
        with_name="Momentum4D",
    )

    boosted_tracks = tracks.boostCM_of_beta3(track_projected_vertices.to_beta3())
    
    angles = boosted_tracks.dot(track_projected_vertices.to_beta3())/(track_projected_vertices.to_beta3().mag*boosted_tracks.mag)

    return angles
"""

def calculate_boosted_cosine_angle(branches, label="VertexCand"):

    # Register awkward with vector
    vector.register_awkward()

    track_to_vertex_indices = branches[f"{label}_vertexIndex"]

    track_projected_vertices = ak.zip(
        {"px": branches[f"{label}_px"][track_to_vertex_indices],
         "py": branches[f"{label}_py"][track_to_vertex_indices],
         "pz": branches[f"{label}_pz"][track_to_vertex_indices],
         "mass": branches[f"{label}_mass"][track_to_vertex_indices]},
        with_name="Momentum4D",
    )

    track_to_track_indices = branches[f"{label}_trackIndex"]

    tracks = ak.zip(
        {"px": branches.Track_px[track_to_track_indices],
         "py": branches.Track_py[track_to_track_indices],
         "pz": branches.Track_pz[track_to_track_indices],
         "mass": ak.zeros_like(branches.Track_px[track_to_track_indices])},
        with_name="Momentum4D",
    )

    boosted_tracks = tracks.boostCM_of_beta3(track_projected_vertices.to_beta3())

    angles = boosted_tracks.dot(track_projected_vertices.to_beta3())/(track_projected_vertices.to_beta3().mag*boosted_tracks.mag)

    return angles
