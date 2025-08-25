from typing import List, Callable, Dict, Any
import awkward as ak

class FunctionalVariable:
    def __init__(self, dependencies: List[str], func: Callable[[Dict[str, ak.Array]], ak.Array], **kwargs):
        """
        Args:
            dependencies: List of branch names required for the calculation.
            func: Function that takes a dictionary of arrays (keyed by branch names)
                  and returns the processed array.
        """
        self.dependencies = dependencies
        self.func = func
        self.kwargs = kwargs

    def get_dependencies(self):
        return self.dependencies
        
    def evaluate(self, data: Dict[str, ak.Array], label: str) -> ak.Array:
        """
        Evaluates the functional variable using the provided data.
        """
        return self.func(data, **self.kwargs)

        
