from brainglobe_atlasapi.list_atlases import get_all_atlases_lastversions


def format_atlas_name(name: str) -> str:
    """Format an atlas name nicely.
    Assumes input in the form of atlas_name_in_snake_case_RESOLUTIONum,
    e.g. allen_mouse_100um"""
    assert name in get_all_atlases_lastversions().keys(), "invalid atlas name!"
    formatted_name = name.split("_")
    formatted_name[0] = formatted_name[0].capitalize()
    formatted_name[-1] = f"({formatted_name[-1].split('um')[0]} \u03BCm)"
    return " ".join([formatted for formatted in formatted_name])
