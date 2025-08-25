class BaseModule(ABC):
    # Default global memory size
    default_memory_size = 100  # Default: 100 mB

    def __init__(self, config=None, memory_size=None):
        """
        Base class for all modules.
        Args:
            events: Input events data.
            config: Optional configuration dictionary for the module.
            memory_size: Optional memory size in mega bytes (overrides default if provided).
        """
        self.config = config or {}
        self.histograms = {}
        self.canvases = {}

        # Use the provided memory_size or fall back to the global default
        self.memory_size = memory_size if memory_size is not None else BaseModule.default_memory_size

    @abstractmethod
    def create_histograms(self):
        """
        Abstract method for creating histograms.
        Must be implemented by derived classes.
        """
        pass

    @abstractmethod
    def create_canvases(self):
        """
        Abstract method for creating canvases from histograms.
        Must be implemented by derived classes.
        """
        pass

    def get_memory_size(self):
        """
        Retrieve the memory size for this instance.
        """
        return self.memory_size

    def get_config(self):
        return self.config
