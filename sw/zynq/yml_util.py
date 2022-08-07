
import yaml
from collections import OrderedDict


def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
    )
    return yaml.load(stream, OrderedLoader)


def get_num_in_range(config, name, parent, val_type, min_val, max_val):
    if name not in config:
        if parent:
            raise RuntimeError(f"{parent} {name} must be specified")
        else:
            raise RuntimeError(f"{name} must be specified")
    value = val_type(config[name])
    if value < min_val or value > max_val:
        if parent:
            raise RuntimeError(
                f"{parent} {name} must be in range: {min_val} to {max_val}"
            )
        else:
            raise RuntimeError(
                f"{name} must be in range: {min_val} to {max_val}"
            )
    return value


def get_one_of(config, name, parent, val_type, options):
    if name not in config:
        if parent:
            raise RuntimeError(f"{parent} {name} must be specified")
        else:
            raise RuntimeError(f"{name} must be specified")
    value = val_type(config[name])
    if value not in options:
        if parent:
            raise RuntimeError(
                f"{parent} {name} must be one of: "
                f'{ ", ".join(options)}'
            )
        else:
            raise RuntimeError(
                f"{name} must be one of: "
                f'{ ", ".join(options)}'
            )
    return value
