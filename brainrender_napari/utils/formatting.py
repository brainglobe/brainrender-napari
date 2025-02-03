def format_atlas_name(name: str) -> str:
    """Format an atlas name nicely.
    Assumes input in the form of atlas_name_in_snake_case_RESOLUTIONum,
    e.g. allen_mouse_100um"""
    formatted_name = name.split("_")
    formatted_name[0] = formatted_name[0].capitalize()
    formatted_name[-1] = f"({formatted_name[-1].split('um')[0]} \u03bcm)"
    return " ".join([formatted for formatted in formatted_name])
