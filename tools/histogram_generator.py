import numpy as np
import uproot
import awkward as ak
import boost_histogram as bh
import itertools
from dataclasses import dataclass, replace
from typing import Any, Dict, List, Set, Optional, Tuple, Callable, Union
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
    dependencies: Optional[List[str]] = None
    
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

    def add_dependencies(self, *additional_dependencies: str) -> 'CollectionConfig':
        """Add an additional condition to the global filter."""
        new_config = self.copy()
        if new_config.dependencies is None:
            new_config.dependencies = additional_dependencies
        else:
            original_dependencies = new_config.dependencies
            new_config.dependencies.extend(additional_dependencies)
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

        if self.config.dependencies:
            for branch in self.config.dependencies:
                branches.add(f"{self.config.prefix}_{branch}")
                
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

        if len(self.category_masks) == 0:
            return masks
        
        # Create individual category masks
        for mask_config in self.category_masks:
            key = mask_config.name.replace("is", "").lower()
            mask = arrays[f"{self.config.prefix}_{mask_config.name}"]
            mapping_index = mask_config.mapping_index
            masks[key] = (mask, mapping_index)

        """
        # Create background mask (not belonging to any category)
        background_mask = ak.ones_like(arrays[f"{self.config.prefix}_{self.category_masks[0].name}"])

        for mask_config in self.category_masks:
            background_mask = background_mask & (~arrays[f"{self.config.prefix}_{mask_config.name}"])
        masks["background"] = (background_mask, None)
        """
        return masks

    def _create_alternate_masks(self, arrays: Dict) -> Dict:

        masks = {}
	
        if len(self.config.alternate_masks) == 0:
            return masks

        """Create alternate masks if specified."""
        if not self.config.alternate_masks:
            return {"any": ak.ones_like(arrays[f"{self.config.prefix}_{self.category_masks[0].name}"])}
            
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

    def _prepare_arrays(self, arrays):
        """Prepare arrays by computing derived and functional variables."""
        arrays = self._compute_derived_variables(arrays)
        arrays = self._compute_functional_variables(arrays)
        return arrays

    def _prepare_masks(self, arrays) -> Dict[str, Any]:
        """Create and prepare all masks needed for histogram creation."""
        category_masks = self._create_category_masks(arrays)
        alternate_masks = self._create_alternate_masks(arrays)
        
        # Apply global filter if specified
        # Find a reference array to create the global filter shape
        if self.category_masks:
            # Use the first category mask as reference if available
            reference_array = arrays[f"{self.config.prefix}_{self.category_masks[0].name}"]
        elif self.variables:
            # Fall back to the first variable if no category masks
            reference_array = arrays[f"{self.config.prefix}_{self.variables[0]}"]
        else:
            # Last resort: use any available array
            reference_key = next(iter(arrays.keys()))
            reference_array = arrays[reference_key]
            
        global_filter = ak.ones_like(reference_array, dtype=bool)
        if self.config.global_filter is not None:
            global_filter = self.config.global_filter(arrays)
            
        return {
            'category_masks': category_masks,
            'alternate_masks': alternate_masks,
            'global_filter': global_filter
        }
    
    def _create_batch_histograms(self, arrays, masks) -> Dict[str, bh.Histogram]:
        """Create all histograms for the current batch of arrays."""
        batch_histograms = {}
        
        # Handle empty masks with sensible defaults
        category_masks = masks['category_masks']
        alternate_masks = masks['alternate_masks']
        
        # If no categories defined, create a default "all" category with no mask
        if not category_masks:
            default_mask = ak.ones_like(masks['global_filter'], dtype=bool)
            default_mapping_index = 0  # or whatever default mapping makes sense
            category_masks = {'all': (default_mask, default_mapping_index)}
            
        # If no alternates defined, create a default with no alternate mask
        if not alternate_masks:
            alternate_masks = {None: None}

        for category_name, (category_mask, mapping_index) in category_masks.items():
            for alt_name, alt_mask in alternate_masks.items():
                # Create 1D histograms
                self._create_1d_histograms(
                    arrays, batch_histograms, category_name, alt_name,
                    category_mask, alt_mask, masks['global_filter'], mapping_index
                )
                
                # Create 2D histograms
                self._create_2d_histograms(
                    arrays, batch_histograms, category_name, alt_name,
                    category_mask, alt_mask, masks['global_filter'], mapping_index
                )
                
        return batch_histograms

    def _create_nTotal_histogram(self, arrays, histograms, category_name, alt_name,
                                 category_mask, alt_mask, global_filter, mapping_index):
        """Creates and fills the 'nTotal' histogram for object counts per event."""

        if not self.variables:  # Do nothing if no variables are defined for the collection
            return

        # Use the first variable as a representative for applying masks
        representative_variable = self.variables[0] #

        # Create the combined mask using the representative variable's context
        nTotal_combined_mask = self._create_combined_mask(
            arrays, category_mask, alt_mask, global_filter, representative_variable, mapping_index
        ) #

        # Get the data for the representative variable to count selected objects from
        representative_branch_name = f"{self.config.prefix}_{representative_variable}" #

        if representative_branch_name not in arrays.fields:
            return

        objects_for_counting = arrays[representative_branch_name] #
        selected_objects_per_event = objects_for_counting[nTotal_combined_mask] #
        counts_per_event = ak.num(selected_objects_per_event) #

        # self._get_histogram_key needs to be defined in your class
        nTotal_key = self._get_histogram_key(category_name, alt_name, "nTotal") #

        hist_config = self._get_histogram_config("nTotal")
        nTotal_axis = bh.axis.Integer(
            start=hist_config.start,
            stop=hist_config.stop,
        )

        histograms[nTotal_key] = bh.Histogram(nTotal_axis) #
        histograms[nTotal_key].fill(counts_per_event) #

    def _create_1d_histograms(self, arrays, histograms, category_name, alt_name,
                              category_mask, alt_mask, global_filter, mapping_index):
        """Create 1D histograms for all variables in the current category/alternate combination."""
        for variable in self.variables:
            if(variable == "nTotal"):
                continue

            var_key = self._get_histogram_key(category_name, alt_name, variable)

            combined_mask = self._create_combined_mask(
                arrays, category_mask, alt_mask, global_filter, variable, mapping_index
            )

            hist_config = self._get_histogram_config(variable)
            axis = bh.axis.Regular(
                bins=hist_config.bins,
                start=hist_config.start,
                stop=hist_config.stop,
            )

            histograms[var_key] = bh.Histogram(axis)
            histograms[var_key].fill(
                ak.flatten(arrays[f"{self.config.prefix}_{variable}"][combined_mask])
            )

        if("nTotal" in self.variables):
            self._create_nTotal_histogram(
                arrays, histograms, category_name, alt_name,
                category_mask, alt_mask, global_filter, mapping_index
            )

    def _create_2d_histograms(self, arrays, histograms, category_name, alt_name,
                             category_mask, alt_mask, global_filter, mapping_index):
        """Create 2D histograms for all variable combinations in the current category/alternate combination."""
        for var_x, var_y in itertools.combinations(self.variables, 2):
            if not self._should_create_2d_histogram(var_x, var_y):
                continue

            if "nTotal" in (var_x, var_y):
                continue;

            var_key_2d = self._get_2d_histogram_key(category_name, alt_name, var_x, var_y)

            combined_mask = self._create_combined_mask(
                arrays, category_mask, alt_mask, global_filter, var_x, mapping_index
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

            histograms[var_key_2d] = bh.Histogram(x_axis, y_axis)
            histograms[var_key_2d].fill(
                ak.flatten(arrays[f"{self.config.prefix}_{var_x}"][combined_mask]),
                ak.flatten(arrays[f"{self.config.prefix}_{var_y}"][combined_mask])
            )
    
    def _get_histogram_key(self, category_name, alt_name, variable):
        """Generate the key for a 1D histogram."""
        # Handle default case where category is "all" and no alternate
        if category_name == 'all' and alt_name is None:
            return variable
        
        if alt_name is not None:
            return f"{category_name}_{alt_name}_{variable}"
        return f"{category_name}_{variable}"
    
    def _get_2d_histogram_key(self, category_name, alt_name, var_x, var_y):
        """Generate the key for a 2D histogram."""
        # Handle default case where category is "all" and no alternate
        if category_name == 'all' and alt_name is None:
            return f"{var_y}_vs_{var_x}"
        
        if alt_name is not None:
            return f"{category_name}_{alt_name}_{var_y}_vs_{var_x}"
        return f"{category_name}_{var_y}_vs_{var_x}"
    

    def _create_combined_mask(self, arrays, category_mask, alt_mask, global_filter, variable, mapping_index):
        """Create a combined mask by applying mask mapping and combining all masks."""
        
        def safe_map(mask):
            if mask is None:
                return ak.Array([True] * len(arrays[f"{self.config.prefix}_{variable}"]))
            return self._apply_mask_mapping(arrays, mask, variable, mapping_index)

        mapped_category_mask = safe_map(category_mask)
        mapped_alt_mask = safe_map(alt_mask)
        mapped_global_filter = safe_map(global_filter)

        return ak.fill_none(
            mapped_category_mask & mapped_alt_mask & mapped_global_filter,
            False
        )

    
    def _merge_histograms(self, existing_histograms, new_histograms):
        """Merge new histograms with existing ones, adding values where keys overlap."""
        for name, hist in new_histograms.items():
            if name in existing_histograms:
                existing_histograms[name] += hist
            else:
                existing_histograms[name] = hist
                
        return existing_histograms
    
    def create_histograms(self, input_data) -> Dict[str, bh.Histogram]:
        """Create histograms for all combinations of categories and variables.
           Args:
              input_data: Either a list of file paths (strings) or an events object with iterate method
        """
        histograms = {}

        # Determine if input is file paths or events object
        if isinstance(input_data, list) and all(isinstance(item, str) for item in input_data):

            # Input is a list of file paths
            iterator = uproot.iterate(
                input_data,
                filter_name=self._get_branch_names(),
                step_size=f"{self.memory_size} mB"
            )
        else:
            # Input is an events object
            iterator = input_data.iterate(
                filter_name=self._get_branch_names(),
                step_size=f"{self.memory_size} mB"
            )

        for arrays in iterator:
            arrays = self._prepare_arrays(arrays)
            masks = self._prepare_masks(arrays)
            batch_histograms = self._create_batch_histograms(arrays, masks)
            histograms = self._merge_histograms(histograms, batch_histograms)
        
        return histograms
