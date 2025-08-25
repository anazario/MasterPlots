MODULE_REGISTRY = {}

def register_module(name):
    """Decorator to register a BaseModule-derived class."""
    def decorator(cls):
        MODULE_REGISTRY[name] = cls
        return cls
    return decorator
