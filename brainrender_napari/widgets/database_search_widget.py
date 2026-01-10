"""Widget for searching and browsing neuron databases."""

from typing import Optional

from napari.qt import thread_worker
from napari.utils.notifications import show_error, show_info
from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from brainrender_napari.data_models.dataset_table_model import DatasetTableModel
from brainrender_napari.utils.morphapi_integration import get_database_searcher
from brainrender_napari.utils.download_datasets import register_dynamic_dataset


class DatabaseSearchWidget(QWidget):
    """Widget for searching neuron databases and displaying results."""

    search_results_updated = Signal(list)  # List of neuron metadata dicts
    neuron_selected = Signal(dict)  # Selected neuron metadata

    def __init__(self, parent: QWidget = None):
        """Initialize the database search widget."""
        super().__init__(parent)
        
        self.setLayout(QVBoxLayout())
        
        # Database selection
        db_group = QGroupBox("Select Database")
        db_group.setLayout(QHBoxLayout())
        
        db_label = QLabel("Database:")
        self.database_combo = QComboBox()
        self.database_combo.addItems([
            "Allen Brain Atlas",
            "Janelia MouseLight",
            "NeuroMorpho.org"
        ])
        self.database_combo.currentTextChanged.connect(self._on_database_changed)
        
        db_group.layout().addWidget(db_label)
        db_group.layout().addWidget(self.database_combo)
        db_group.layout().addStretch()
        
        self.layout().addWidget(db_group)
        
        # Search criteria
        search_group = QGroupBox("Search Criteria")
        search_group.setLayout(QVBoxLayout())
        
        # Allen-specific search
        self.allen_search_layout = QHBoxLayout()
        allen_structure_label = QLabel("Brain Structure (e.g., VISp, MOs):")
        self.allen_structure_input = QLineEdit()
        self.allen_structure_input.setPlaceholderText("VISp")
        self.allen_search_layout.addWidget(allen_structure_label)
        self.allen_search_layout.addWidget(self.allen_structure_input)
        search_group.layout().addLayout(self.allen_search_layout)
        
        # MouseLight-specific search
        self.mouselight_search_layout = QHBoxLayout()
        ml_region_label = QLabel("Soma Region (e.g., MOs):")
        self.mouselight_region_input = QLineEdit()
        self.mouselight_region_input.setPlaceholderText("MOs")
        self.mouselight_search_layout.addWidget(ml_region_label)
        self.mouselight_search_layout.addWidget(self.mouselight_region_input)
        search_group.layout().addLayout(self.mouselight_search_layout)
        
        # NeuroMorpho-specific search
        self.neuromorpho_search_layout = QVBoxLayout()
        nm_row1 = QHBoxLayout()
        nm_species_label = QLabel("Species:")
        self.neuromorpho_species_input = QLineEdit()
        self.neuromorpho_species_input.setText("mouse")
        self.neuromorpho_species_input.setPlaceholderText("mouse")
        nm_row1.addWidget(nm_species_label)
        nm_row1.addWidget(self.neuromorpho_species_input)
        
        nm_row2 = QHBoxLayout()
        nm_celltype_label = QLabel("Cell Type:")
        self.neuromorpho_celltype_input = QLineEdit()
        self.neuromorpho_celltype_input.setPlaceholderText("pyramidal")
        nm_row2.addWidget(nm_celltype_label)
        nm_row2.addWidget(self.neuromorpho_celltype_input)
        
        nm_row3 = QHBoxLayout()
        nm_region_label = QLabel("Brain Region:")
        self.neuromorpho_region_input = QLineEdit()
        self.neuromorpho_region_input.setPlaceholderText("neocortex")
        nm_row3.addWidget(nm_region_label)
        nm_row3.addWidget(self.neuromorpho_region_input)
        
        self.neuromorpho_search_layout.addLayout(nm_row1)
        self.neuromorpho_search_layout.addLayout(nm_row2)
        self.neuromorpho_search_layout.addLayout(nm_row3)
        search_group.layout().addLayout(self.neuromorpho_search_layout)
        
        # Search button
        self.search_button = QPushButton("Search Database")
        self.search_button.clicked.connect(self._on_search_clicked)
        search_group.layout().addWidget(self.search_button)
        
        self.layout().addWidget(search_group)
        
        # Results table
        results_group = QGroupBox("Search Results")
        results_group.setLayout(QVBoxLayout())
        
        self.results_table = QTableView()
        self.results_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.results_table.doubleClicked.connect(self._on_result_double_clicked)
        results_group.layout().addWidget(self.results_table)
        
        self.layout().addWidget(results_group)
        
        # Initialize UI state
        self._on_database_changed()
        self._current_results = []

    def _on_database_changed(self):
        """Update UI when database selection changes."""
        db_name = self.database_combo.currentText()
        
        # Hide all search input widgets
        for i in range(self.allen_search_layout.count()):
            widget = self.allen_search_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        
        for i in range(self.mouselight_search_layout.count()):
            widget = self.mouselight_search_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        
        for i in range(self.neuromorpho_search_layout.count()):
            item = self.neuromorpho_search_layout.itemAt(i)
            if item:
                layout = item.layout()
                if layout:
                    for j in range(layout.count()):
                        widget = layout.itemAt(j).widget()
                        if widget:
                            widget.setVisible(False)
        
        # Show relevant search layout
        if "Allen" in db_name:
            for i in range(self.allen_search_layout.count()):
                widget = self.allen_search_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(True)
        elif "MouseLight" in db_name:
            for i in range(self.mouselight_search_layout.count()):
                widget = self.mouselight_search_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(True)
        elif "NeuroMorpho" in db_name:
            for i in range(self.neuromorpho_search_layout.count()):
                item = self.neuromorpho_search_layout.itemAt(i)
                if item:
                    layout = item.layout()
                    if layout:
                        for j in range(layout.count()):
                            widget = layout.itemAt(j).widget()
                            if widget:
                                widget.setVisible(True)

    def _on_search_clicked(self):
        """Perform database search."""
        db_name = self.database_combo.currentText()
        self.search_button.setEnabled(False)
        self.search_button.setText("Searching...")
        
        try:
            searcher = get_database_searcher()
            
            if "Allen" in db_name:
                structure = self.allen_structure_input.text().strip() or None
                worker = self._search_allen_worker(searcher, structure)
            elif "MouseLight" in db_name:
                regions = [r.strip() for r in self.mouselight_region_input.text().split(",") if r.strip()]
                regions = regions if regions else None
                worker = self._search_mouselight_worker(searcher, regions)
            elif "NeuroMorpho" in db_name:
                species = self.neuromorpho_species_input.text().strip() or "mouse"
                cell_type = self.neuromorpho_celltype_input.text().strip() or None
                brain_region = self.neuromorpho_region_input.text().strip() or None
                worker = self._search_neuromorpho_worker(searcher, species, cell_type, brain_region)
            else:
                show_error(f"Unknown database: {db_name}")
                self.search_button.setEnabled(True)
                self.search_button.setText("Search Database")
                return
            
            worker.returned.connect(self._on_search_complete)
            worker.errored.connect(self._on_search_error)
            worker.start()
            
        except ImportError:
            show_error(
                "morphapi is not installed. Install with: pip install morphapi\n"
                "This is required for database searching functionality."
            )
            self.search_button.setEnabled(True)
            self.search_button.setText("Search Database")
        except Exception as e:
            show_error(f"Failed to start search: {str(e)}")
            self.search_button.setEnabled(True)
            self.search_button.setText("Search Database")

    @thread_worker
    def _search_allen_worker(self, searcher, structure: Optional[str]):
        """Worker thread for Allen database search."""
        return searcher.search_allen_neurons(structure_area=structure, limit=50)

    @thread_worker
    def _search_mouselight_worker(self, searcher, regions: Optional[list]):
        """Worker thread for MouseLight database search."""
        return searcher.search_mouselight_neurons(filter_regions=regions, limit=50)

    @thread_worker
    def _search_neuromorpho_worker(self, searcher, species: str, cell_type: Optional[str], brain_region: Optional[str]):
        """Worker thread for NeuroMorpho database search."""
        return searcher.search_neuromorpho_neurons(
            species=species, cell_type=cell_type, brain_region=brain_region, limit=50
        )

    def _on_search_complete(self, results: list):
        """Handle completed search."""
        self.search_button.setEnabled(True)
        self.search_button.setText("Search Database")
        
        if not results:
            show_info("No neurons found matching the search criteria.")
            self._current_results = []
            self.results_table.setModel(None)
            return
        
        self._current_results = results
        
        # Register all found neurons as available datasets
        for neuron in results:
            register_dynamic_dataset(neuron)
        
        # Create a table model to display results
        from brainrender_napari.data_models.search_results_model import SearchResultsModel
        model = SearchResultsModel(results)
        self.results_table.setModel(model)
        self.results_table.resizeColumnsToContents()
        
        show_info(f"Found {len(results)} neurons. Double-click to download.")
        self.search_results_updated.emit(results)

    def _on_search_error(self, error):
        """Handle search error."""
        self.search_button.setEnabled(True)
        self.search_button.setText("Search Database")
        show_error(f"Search failed: {str(error)}")

    def _on_result_double_clicked(self):
        """Handle double-click on search result."""
        selected_index = self.results_table.selectionModel().currentIndex()
        if not selected_index.isValid() or not self._current_results:
            return
        
        row = selected_index.row()
        if row < len(self._current_results):
            neuron = self._current_results[row]
            self.neuron_selected.emit(neuron)
