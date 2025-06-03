import numpy as np
import awkward as ak
import boost_histogram as bh
import itertools
from dataclasses import dataclass, replace
from typing import Dict, List, Set, Optional, Tuple, Callable, Union
from tools.histogram_dictionary import VARIABLES, HistogramConfig
from tools.functional_variable import FunctionalVariable

@dataclass
class MaskConfig:
    name: str  # e.g., "isGold"
    is_derived: bool = False  # Flag to indicate if this is a derived mask
    mapping_index: Optional[str] = None  # Branch name for index mapping (e.g., "vertexIndex")

@dataclass
class CollectionConfig:
    prefix: str
    variables: Dict[str, HistogramConfig]
    category_masks: List[Union[str, MaskConfig]]
    alternate_masks: Optional[List[str]] = None
    derived_variables: Optional[Dict[str, callable]] = None
    skip_pairs: Optional[List[Tuple[str, str]]] = None
    global_filter: Optional[Callable[[Dict], ak.Array]] = None
    skip_variables: Optional[List[str]] = None
    functional_variables: Optional[Dict[str, FunctionalVariable]] = None
    
    def copy(self) -> 'CollectionConfig':
        """Create a deep copy of the configuration."""
        return replace(self)

    def print_config(self) -> None:
        """Print all configuration fields for verification."""
        print("\nCurrent Configuration:")
        print("-" * 50)
        print(f"Prefix: {self.prefix}")
        print("\nVariables:")
        for var, config in self.variables.items():
            print(f"  {var}: bins={config.bins}, range=[{config.start}, {config.stop}]")
        print("\nCategory Masks:")
        for mask in self.category_masks:
            if isinstance(mask, str):
                print(f"  {mask}")
            else:
                print(f"  {mask.name} (mapping_index: {mask.mapping_index})")
        print("\nAlternate Masks:")
        print(f"  {self.alternate_masks if self.alternate_masks else 'None'}")
        print("\nDerived Variables:")
        if self.derived_variables:
            for var in self.derived_variables:
                print(f"  {var}")
        else:
            print("  None")
        print("\nSkip Pairs:")
        print(f"  {self.skip_pairs if self.skip_pairs else 'None'}")
        print("\nSkip Variables:")
        print(f"  {self.skip_variables if self.skip_variables else 'None'}")
        print("\nGlobal Filter:")
        print(f"  {'Present' if self.global_filter else 'None'}")
        print("-" * 50)

    def add_functional_variables(self, functions: Dict[str, FunctionalVariable]) -> 'CollectionConfig':
        """
        Adds functional variables to the configuration.
        
        Args:
        functions: A dictionary mapping variable names to FunctionalVariable instances.

        Returns:
        A new CollectionConfig instance with the added functional variables.
        """
        # Create a copy of the current configuration
        new_config = self.copy()

        # Initialize functional_variables if it's None
        if new_config.functional_variables is None:
            new_config.functional_variables = {}

            # Add each functional variable
            for var, func_var in functions.items():
                if var in VARIABLES:
                    new_config.functional_variables[var] = func_var
                    new_config.add_variables(var)  # Assuming this method adds the variable to the config
                else:
                    raise KeyError(f"Variable {var} not found in VARIABLES")
                
        return new_config
    
    def add_variables(self, *var_names: str, **custom_configs: HistogramConfig) -> 'CollectionConfig':
        """
        Add variables to the configuration.
        
        Args:
            *var_names: Names of variables to add from VARIABLES
            **custom_configs: Custom HistogramConfig for specific variables
        """
        new_config = self.copy()
        
        # Add from standard dictionary
        for var in var_names:
            if var in VARIABLES:
                new_config.variables[var] = VARIABLES[var]
            else:
                raise KeyError(f"Variable {var} not found in VARIABLES")
        
        # Add custom configurations
        new_config.variables.update(custom_configs)
        return new_config

    def remove_variables(self, *var_names: str) -> 'CollectionConfig':
        """Remove specified variables from all relevant fields."""
        new_config = self.copy()
        
        # Remove from variables
        for var in var_names:
            new_config.variables.pop(var, None)
        
        # Remove from derived variables
        if new_config.derived_variables:
            for var in var_names:
                new_config.derived_variables.pop(var, None)
        
        # Remove from skip pairs
        if new_config.skip_pairs:
            new_config.skip_pairs = [
                pair for pair in new_config.skip_pairs 
                if pair[0] not in var_names and pair[1] not in var_names
            ]
        
        # Remove from skip variables
        if new_config.skip_variables:
            new_config.skip_variables = [
                var for var in new_config.skip_variables 
                if var not in var_names
            ]
            
        return new_config

    def add_global_filter(self, additional_filter: Callable[[Dict], ak.Array]) -> 'CollectionConfig':
        """Add an additional condition to the global filter."""
        new_config = self.copy()
        if new_config.global_filter is None:
            new_config.global_filter = additional_filter
        else:
            original_filter = new_config.global_filter
            new_config.global_filter = lambda arrays: original_filter(arrays) & additional_filter(arrays)
        return new_config

    def replace_global_filter(self, new_filter: Callable[[Dict], ak.Array]) -> 'CollectionConfig':
        """Replace the global filter entirely."""
        new_config = self.copy()
        new_config.global_filter = new_filter
        return new_config

    def clear_global_filter(self) -> 'CollectionConfig':
        """Remove the global filter entirely."""
        new_config = self.copy()
        new_config.global_filter = None
        return new_config
    
    def add_category_masks(self, *masks: Union[str, MaskConfig]) -> 'CollectionConfig':
        """Add additional category masks."""
        new_config = self.copy()
        new_config.category_masks.extend(masks)
        return new_config

    def replace_category_masks(self, masks: List[Union[str, MaskConfig]]) -> 'CollectionConfig':
        """Replace all category masks."""
        new_config = self.copy()
        new_config.category_masks = masks
        return new_config

    def add_alternate_masks(self, *masks: str) -> 'CollectionConfig':
        """Add additional alternate masks."""
        new_config = self.copy()
        if new_config.alternate_masks is None:
            new_config.alternate_masks = list(masks)
        else:
            new_config.alternate_masks.extend(masks)
        return new_config

    def replace_alternate_masks(self, masks: List[str]) -> 'CollectionConfig':
        """Replace all alternate masks."""
        new_config = self.copy()
        new_config.alternate_masks = masks
        return new_config

    def add_skip_pairs(self, *pairs: Tuple[str, str]) -> 'CollectionConfig':
        """Add variable pairs to skip."""
        new_config = self.copy()
        if new_config.skip_pairs is None:
            new_config.skip_pairs = list(pairs)
        else:
            new_config.skip_pairs.extend(pairs)
        return new_config

    def add_skip_variables(self, *variables: str) -> 'CollectionConfig':
        """Add variables to skip."""
        new_config = self.copy()
        if new_config.skip_variables is None:
            new_config.skip_variables = list(variables)
        else:
            new_config.skip_variables.extend(variables)
        return new_config
    
class HistogramGenerator:
    def __init__(self, collection_config: CollectionConfig, memory_size=100):
        self.config = collection_config
        self.memory_size = memory_size

        # Convert string masks to MaskConfig objects
        self.category_masks = []
        for mask in self.config.category_masks:
            if isinstance(mask, str):
                self.category_masks.append(MaskConfig(name=mask))
            else:
                self.category_masks.append(mask)
        
        # Include both regular and derived variables in the variables list
        self.variables = list(collection_config.variables.keys())
        if self.config.derived_variables:
            self.variables.extend(list(self.config.derived_variables.keys()))
            
        # Remove skipped variables from the plotting list
        if self.config.skip_variables:
            self.variables = [var for var in self.variables if var not in self.config.skip_variables]
        
        # Create set of variable pairs to skip
        self.skip_pairs = set()
        if self.config.skip_pairs:
            for var1, var2 in self.config.skip_pairs:
                self.skip_pairs.add((var1, var2))
                self.skip_pairs.add((var2, var1))

    def _get_branch_names(self) -> Set[str]:
        """Generate full branch names needed for histogram creation."""
        branches = set()
        
        # Add main variable branches
        for var in self.config.variables.keys():
            branches.add(f"{self.config.prefix}_{var}")
            
        # Add category branches and mapping indices
        for mask_config in self.category_masks:
            branches.add(f"{self.config.prefix}_{mask_config.name}")
            if mask_config.mapping_index:
                branches.add(f"{self.config.prefix}_{mask_config.mapping_index}")
            
        # Add alternate branches
        if self.config.alternate_masks:
            for branch in self.config.alternate_masks:
                branches.add(f"{self.config.prefix}_{branch}")

        # Add functional variable dependencies
        if self.config.functional_variables:
            for name, func_var in self.config.functional_variables.items():
                for branch in func_var.get_dependencies():
                    if branch in branches:
                        continue
                    else:
                        branches.add(branch)
                
        return branches

    def _compute_derived_variables(self, arrays: Dict) -> Dict:
        """Compute any derived variables specified in the config."""
        if not self.config.derived_variables:
            return arrays
            
        arrays_copy = arrays  # Make a copy to avoid modifying the original
        for var_name, compute_func in self.config.derived_variables.items():
            branch_name = f"{self.config.prefix}_{var_name}"
            arrays_copy[branch_name] = compute_func(arrays_copy)
        return arrays_copy

    def _compute_functional_variables(self, arrays:Dict) -> Dict:
        if not self.config.functional_variables:
            return arrays

        arrays_copy = arrays 
        for var_name, func_var in self.config.functional_variables.items():
            branch_name = f"{self.config.prefix}_{var_name}"
            arrays_copy[branch_name] = func_var.evaluate(arrays, f"{self.config.prefix}")

        return arrays_copy

    def _get_histogram_config(self, variable: str) -> HistogramConfig:
        """Get histogram configuration for a variable, using default if not specified."""
        return self.config.variables.get(variable, HistogramConfig())

    def _create_category_masks(self, arrays: Dict) -> Dict[str, Tuple[ak.Array, Optional[str]]]:
        """Create masks for different categories, returning both mask and any needed mapping index."""
        masks = {}
        
        # Create individual category masks
        for mask_config in self.category_masks:
            key = mask_config.name.replace("is", "").lower()
            mask = arrays[f"{self.config.prefix}_{mask_config.name}"]
            mapping_index = mask_config.mapping_index
            masks[key] = (mask, mapping_index)
            
        # Create background mask (not belonging to any category)
        background_mask = ak.ones_like(arrays[f"{self.config.prefix}_{self.category_masks[0].name}"])
        for mask_config in self.category_masks:
            background_mask = background_mask & (~arrays[f"{self.config.prefix}_{mask_config.name}"])
        masks["background"] = (background_mask, None)
        
        return masks

    def _create_alternate_masks(self, arrays: Dict) -> Dict:
        """Create alternate masks if specified."""
        if not self.config.alternate_masks:
            return {"any": ak.ones_like(arrays[f"{self.config.prefix}_{self.category_masks[0].name}"])}
            
        masks = {}
        for branch in self.config.alternate_masks:
            key = branch.replace("is", "").lower()
            masks[key] = arrays[f"{self.config.prefix}_{branch}"]
            masks[f"non_{key}"] = ~arrays[f"{self.config.prefix}_{branch}"]
        masks["any"] = ak.ones_like(arrays[f"{self.config.prefix}_{self.category_masks[0].name}"])
        
        return masks

    def _should_create_2d_histogram(self, var1: str, var2: str) -> bool:
        """Check if we should create a 2D histogram for this variable pair."""
        # Skip if variables are the same
        if var1 == var2:
            return False
            
        # Skip if pair is in skip_pairs
        if (var1, var2) in self.skip_pairs:
            return False
            
        return True

    def _apply_mask_mapping(self, arrays: Dict, mask: ak.Array, variable: str, mapping_index: Optional[str]) -> ak.Array:
        """Apply mask mapping if needed for track-level variables."""
        if mapping_index and self.config.variables.get(variable, HistogramConfig()).mapping_required:
            vertex_index = arrays[f"{self.config.prefix}_{mapping_index}"]
            return mask[vertex_index]
        return mask

    def create_histograms(self, events) -> Dict[str, bh.Histogram]:
        """Create histograms for all combinations of categories and variables."""

        histograms = {}
        
        for arrays in events.iterate(filter_name=self._get_branch_names(), step_size=f"{self.memory_size} mB"):
            arrays = self._compute_derived_variables(arrays)
            arrays = self._compute_functional_variables(arrays)
        
            # Create masks
            category_masks = self._create_category_masks(arrays)
            alternate_masks = self._create_alternate_masks(arrays)

            # Apply global filter if specified
            global_filter = ak.ones_like(arrays[f"{self.config.prefix}_{self.category_masks[0].name}"])
            if self.config.global_filter is not None:
                global_filter = self.config.global_filter(arrays)
        
            temp_histograms = {}

            # Create 1D and 2D histograms for all combinations
            for category_name, (category_mask, mapping_index) in category_masks.items():
                for alt_name, alt_mask in alternate_masks.items():
                    # 1D histograms
                    for variable in self.variables:
                        
                        var_key = f"{category_name}_{variable}"
                        if(alt_mask is not None):
                            var_key = f"{category_name}_{alt_name}_{variable}"
                            
                        hist_config = self._get_histogram_config(variable)
                        
                        # Apply appropriate mask mapping for this variable
                        mapped_category_mask = self._apply_mask_mapping(
                            arrays, category_mask, variable, mapping_index
                        )
                        
                        mapped_alt_mask = self._apply_mask_mapping(
                            arrays, alt_mask, variable, mapping_index
                        )
                        
                        mapped_global_filter = self._apply_mask_mapping(
                            arrays, global_filter, variable, mapping_index
                        )
                        
                        # Combine masks
                        combined_mask = ak.fill_none(
                            mapped_category_mask & mapped_alt_mask & mapped_global_filter, 
                            False
                        )
                        
                        axis = bh.axis.Regular(
                            bins=hist_config.bins,
                            start=hist_config.start,
                            stop=hist_config.stop,
                        )
                        
                        temp_histograms[var_key] = bh.Histogram(axis)
                        temp_histograms[var_key].fill(
                            ak.flatten(arrays[f"{self.config.prefix}_{variable}"][combined_mask])
                        )
                        
                    # 2D histograms
                    for var_x, var_y in itertools.combinations(self.variables, 2):
                        if not self._should_create_2d_histogram(var_x, var_y):
                            continue
                        
                        var_key_2d = f"{category_name}_{var_y}_vs_{var_x}"
                        if(alt_mask is not None):
                            var_key_2d = f"{category_name}_{alt_name}_{var_y}_vs_{var_x}"
                            
                        # Apply appropriate mask mapping for both variables
                        mapped_category_mask = self._apply_mask_mapping(
                            arrays, category_mask, var_x, mapping_index
                        )
                        mapped_alt_mask = self._apply_mask_mapping(
                            arrays, alt_mask, var_x, mapping_index
                        )
                        mapped_global_filter = self._apply_mask_mapping(
                            arrays, global_filter, var_x, mapping_index
                        )
                        
                        combined_mask = ak.fill_none(
                            mapped_category_mask & mapped_alt_mask & mapped_global_filter, 
                            False
                        )
                        
                        x_config = self._get_histogram_config(var_x)
                        y_config = self._get_histogram_config(var_y)
                        
                        x_axis = bh.axis.Regular(
                            bins=x_config.bins,
                            start=x_config.start,
                            stop=x_config.stop,
                        )
                        y_axis = bh.axis.Regular(
                            bins=y_config.bins,
                            start=y_config.start,
                            stop=y_config.stop,
                        )
                        
                        temp_histograms[var_key_2d] = bh.Histogram(x_axis, y_axis)
                        temp_histograms[var_key_2d].fill(
                            ak.flatten(arrays[f"{self.config.prefix}_{var_x}"][combined_mask]),
                            ak.flatten(arrays[f"{self.config.prefix}_{var_y}"][combined_mask])
                        )

            for name, hist in temp_histograms.items():
                if name in histograms.keys():
                    histograms[name] += temp_histograms[name]
                else:
                    histograms[name] = hist
        
        return histograms
