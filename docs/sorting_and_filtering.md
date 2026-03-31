# Sorting and Filtering Atlases

## Overview

brainrender-napari provides convenient tools to find the atlas you need from the growing collection of BrainGlobe atlases. Both the **Atlas Viewer** and **Atlas Manager** widgets support **column sorting** and **species filtering**.

## Sorting

Click any column header in the atlas table to sort alphabetically. Click again to reverse the sort order. This works in both:

- **Atlas Viewer**: Sort your locally downloaded atlases
- **Atlas Manager**: Sort all available atlases (including those not yet downloaded)

## Species Filtering

### Atlas Manager

The Atlas Manager includes a filter bar with three controls:

1. **Query field**: Type to search across atlas names and metadata
2. **Column selector**: Choose which column to search in, or "Any" for all columns
3. **Species dropdown**: Select a species to show only atlases for that species

The species dropdown automatically populates with all unique species found in the atlas collection:
- **Mouse** (Mus musculus)
- **Rat** (Rattus norvegicus)
- **Zebrafish** (Danio rerio)
- **Human** (Homo sapiens)
- And more as new atlases are added

Select **"All Species"** to remove the species filter and show all atlases.

### Atlas Viewer

The Atlas Viewer also includes a species filter dropdown above the atlas table. This filters your locally downloaded atlases by species.

## How Species is Determined

For **downloaded atlases**, the species is read from the atlas metadata file (`metadata.json`), which contains the scientific name (e.g., "Mus musculus"). This is mapped to a common name (e.g., "Mouse").

For **atlases not yet downloaded**, the species is inferred from the atlas name. For example, `allen_mouse_100um` is identified as a "Mouse" atlas.

## Tips

- Sorting and filtering can be combined: first filter by species, then click a column header to sort the filtered results
- The species filter resets when you type a new search query
- Use the "All Species" option to quickly clear the species filter
