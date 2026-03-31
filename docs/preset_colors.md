# Atlas Annotation Colors and Custom Mesh Colors

## Preset Annotation Colors

When visualising an atlas, annotations can be displayed with colours that are predefined in the atlas metadata. Each brain region in a BrainGlobe atlas has an associated `rgb_triplet` colour, chosen by the atlas maintainers to be visually meaningful.

### How to Use

1. Open the **Atlas Viewer** widget in napari
2. Ensure the **"Use preset annotation colors"** checkbox is checked (it is checked by default)
3. Double-click on an atlas to add it to the viewer

The annotation layer will now display each brain region with its metadata-defined colour, making it easy to distinguish different structures at a glance.

### Disabling Preset Colors

If you prefer napari's default label colormap:

1. Uncheck the **"Use preset annotation colors"** checkbox
2. Double-click on an atlas

The annotations will use napari's built-in label colormap instead.

### How It Works

When preset colors are enabled, brainrender-napari:

1. Reads the `rgb_triplet` from each structure in the atlas's `structures.json`
2. Maps each structure ID to its normalised RGBA colour
3. Sets the background (ID=0) to transparent
4. Passes this colour dictionary to napari's `add_labels()` function

## Custom Mesh Colors

By default, brain region meshes are displayed with the colour defined in the atlas metadata (the `rgb_triplet` of each structure). You can override this with any colour of your choosing.

### How to Use

1. Open the **Atlas Viewer** widget and select a downloaded atlas
2. In the **3D Atlas region meshes** section, find the structure you want to visualise
3. **Right-click** on the structure to open the context menu
4. Choose one of:
   - **"Add mesh (default color)"** — uses the atlas's preset colour
   - **"Add mesh with custom color..."** — opens a colour picker dialog

When you select "Add mesh with custom color...", a standard colour picker dialog appears. Choose your preferred colour and click OK. The mesh will be added to the viewer with your chosen colour.

### Tips

- You can add the same structure multiple times with different colours
- Custom colours are specified as RGB values (0–255)
- Meshes are only visible when the viewer is in 3D mode — toggle with the square/cube icon in the lower left of the napari window
