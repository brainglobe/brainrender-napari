def format_atlas_name(name: str) -> str:
    """Format an atlas name nicely.
    Assumes input in the form of atlas_name_in_snake_case_RESOLUTIONum,
    e.g. allen_mouse_100um"""
    formatted_name: list[str] = name.split("_")
    formatted_name[0] = formatted_name[0].capitalize()
    formatted_name[-1] = f"({formatted_name[-1].split('um')[0]} \u03bcm)"
    return " ".join(formatted_name)


def format_bytes(num_bytes: float) -> str:
    """
    Format a byte count into a human-readable string with appropriate units.
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.2f} TB"
