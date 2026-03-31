---
title: "brainrender-napari: Enhanced Atlas Discovery and Visualisation (GSoC 2026)"
author: "Mohd Mustafa"
date: "2026-03-31"
categories: ["GSoC", "brainrender-napari", "napari", "neuroinformatics"]
tags: ["atlas", "visualisation", "UI"]
---

*This post documents the completion of my Google Summer of Code (GSoC) 2026 project, developed under the mentorship of the BrainGlobe Initiative and [neuroinformatics.dev](https://neuroinformatics.dev/).*

## Introduction

As the BrainGlobe ecosystem continues to accelerate, so does the number of available neuroanatomical atlases. With dozens of atlases spanning multiple species — from mouse, to zebrafish, to human — **brainrender-napari** needed better tools for atlas discovery and more flexible visualisation options.

This post summarises the recent GSoC 2026 improvements to brainrender-napari that address user feedback and vastly improve the atlas exploration experience.

## What's New?

### 1. Sort Atlas Tables by Any Column

Both the **Atlas Viewer** (for browsing local atlases) and the **Atlas Manager** (for downloading/updating atlases) now support native column sorting. Simply click any column header to sort alphabetically, and click again to reverse the order.

This makes it trivially easy to find atlases by name, version, or any other attribute.

**Technical Highlights**: We introduced a `QSortFilterProxyModel` to the Atlas Viewer (the Atlas Manager already had one for text filtering) and enabled Qt's built-in sorting on both views. This follows Qt's Model/View architecture cleanly, with no changes needed to the underlying data model arrays.

### 2. Filter Atlases by Species

Finding the right atlas just got a lot easier. A new **species filter dropdown** is available in both the Atlas Manager and Atlas Viewer widgets.

Select "Mouse", "Zebrafish", "Human", or any other available species, and the table instantly filters to show only atlases for that species. Select "All Species" to reset the filter.

**How Species is Determined**: For downloaded atlases, the species is reliably read from the `metadata.json` file (e.g., "Mus musculus" maps to "Mouse"). For atlases not yet downloaded, we parse the species heuristically from the atlas name using the core BrainGlobe atlas naming convention (e.g., `allen_human_500um` is mapped to "Human"). 

### 3. Preset Annotation Colors

When you add an atlas to the napari viewer, annotations are now displayed with the **colours defined by the atlas maintainers**. Each brain region in a BrainGlobe atlas has an associated `rgb_triplet` in its structure metadata, and these colours are now injected by default.

This means you can immediately see meaningful colour boundaries between brain regions, without needing to manually configure colormaps.

A checkbox ("Use preset annotation colors", on by default) lets you toggle between the atlas-defined colours and napari's randomized label colormap.

**Technical Highlights**: We added a `build_colormap_from_structures()` utility that iterates over all structures in the atlas and builds a `{structure_id: RGBA}` dictionary. This is passed directly into napari's `DirectLabelColormap` class, mapping categorical IDs natively to semantic colours.

### 4. Custom Mesh Colors (Stretch Goal Completed)

Previously, brain region meshes always used the colour defined in the atlas metadata. Now, users can **choose any colour** for their 3D meshes.

Right-click on a structure in the 3D structure tree to open a context menu with two options:
- **"Add mesh (default color)"**: uses the atlas's preset colour.
- **"Add mesh with custom color..."**: opens a standard Qt colour picker.

This was highly requested via GitHub issues, heavily assisting researchers creating multi-layer, publication-quality figures where specific structures need arbitrary colour highlighting.

## Testing and Code Health

All new features include comprehensive `pytest` suites:
- **Unit tests** covering the species extraction heuristic, the `DirectLabelColormap` proxy builder, Qt widget drop-downs, and boundary cases.
- **Integration tests** verifying signal connections locally simulating user double-clicks (`pytest-qt`).

All 133 tests in the `brainrender-napari` test suite are fully operational and passing as part of this merge.

## Summary of PR Contributions

| Feature | Resolves Issue | Core Architectural Impact |
|---------|-------|----------------|
| Table sorting | — | Handled cleanly via `QSortFilterProxyModel`. |
| Species filter | [#22](https://github.com/brainglobe/brainrender-napari/issues/22) | Cross-compatible with `brainglobe-atlasapi` naming schemas. |
| Preset annotation colors | [#218](https://github.com/brainglobe/brainrender-napari/issues/218) | Bridges atlas `rgb_triplet` directly into Napari's label engine. |
| Custom mesh colors | [#46](https://github.com/brainglobe/brainrender-napari/issues/46) | Uses standalone PyQt signals (`add_structure_with_color_requested`) to avoid breaking downstream backwards compatibility. |

## Get Involved

I had a wonderful time working closely with the BrainGlobe maintainers. `brainrender-napari` is an open-source project and strongly welcomes contributions! 

Check out the [GitHub repository](https://github.com/brainglobe/brainrender-napari) to get started, and feel free to open issues or submit pull requests.

---

*(Google Summer of Code 2026 Project Report)*
