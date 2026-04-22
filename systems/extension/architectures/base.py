class BaseArchitecture:
    """
    Strategy interface for loading and initializing extensions.
    """
    def load(self, meta):
        """Loads the python modules required for the extension."""
        raise NotImplementedError

    def initialize(self, meta, context_or_window):
        """Creates the app instance and the GUI instance."""
        raise NotImplementedError