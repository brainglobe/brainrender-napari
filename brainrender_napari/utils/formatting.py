import math

def format_atlas_name(name: str) -> str:
    """Format an atlas name nicely.
    Assumes input in the form of atlas_name_in_snake_case_RESOLUTIONum,
    e.g. allen_mouse_100um"""
    formatted_name = name.split("_")
    formatted_name[0] = formatted_name[0].capitalize()
    formatted_name[-1] = f"({formatted_name[-1].split('um')[0]} \u03bcm)"
    return " ".join([formatted for formatted in formatted_name])


def format_bytes(num_bytes: float) -> str:
    """
    Format a byte count into a human-readable string with appropriate units.
    """
    units = ["B", "KB", "MB", "GB", "TB"]
    if num_bytes < 0:
        return f"{num_bytes:.2f} B"
    # ensuring the index doesn't exceed the units
    i = min(math.floor(math.log(num_bytes, 1024)), len(units) - 1)
    return f"{num_bytes / (1024 ** i):.2f} {units[i]}"