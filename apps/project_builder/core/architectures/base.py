class BaseBuilder:
    def __init__(self, root_path, output_dir, main_file, options, log_callback):
        self.root_path = root_path
        self.output_dir = output_dir
        self.main_file = main_file
        self.options = options
        self.log = log_callback

    def build(self) -> bool:
        raise NotImplementedError("Build method must be implemented by subclasses.")