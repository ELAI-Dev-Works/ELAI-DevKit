class BaseBuilder:
    def __init__(self, fs, out_fs, main_file, options, log_callback):
        self.fs = fs
        self.out_fs = out_fs
        self.root_path = fs.root
        self.output_dir = out_fs.root
        self.main_file = main_file
        self.options = options
        self.log = log_callback

    def build(self) -> bool:
        raise NotImplementedError("Build method must be implemented by subclasses.")