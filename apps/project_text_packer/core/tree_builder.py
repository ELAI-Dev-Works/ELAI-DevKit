import posixpath

class TreeBuilder:
    @staticmethod
    def build(fs, dir_path_rel, handler, prefix=""):
        tree =[]
        try:
            items_in_dir = sorted(fs.listdir(dir_path_rel))
        except PermissionError:
            return [prefix + "└── [Access Denied]"]
        except FileNotFoundError:
            return[]

        processed_items =[]
        for item in items_in_dir:
            item_rel = posixpath.join(dir_path_rel, item).strip('/')
            is_dir = fs.is_dir(item_rel)
            is_ignored_item = handler.is_ignored(item, is_dir=is_dir)
            processed_items.append({'name': item, 'is_dir': is_dir, 'is_ignored': is_ignored_item, 'rel': item_rel})

        for i, item_data in enumerate(processed_items):
            is_last = (i == len(processed_items) - 1)
            connector = "└── " if is_last else "├── "
            item_name = item_data['name']
            is_dir = item_data['is_dir']
            is_ignored = item_data['is_ignored']
            item_rel = item_data['rel']

            display_name = item_name
            if is_dir:
                display_name += "/"
            if is_ignored:
                display_name += " [...]"
            tree.append(prefix + connector + display_name)

            if is_dir and not is_ignored:
                extension = "    " if is_last else "│   "
                tree.extend(TreeBuilder.build(fs, item_rel, handler, prefix + extension))
        return tree