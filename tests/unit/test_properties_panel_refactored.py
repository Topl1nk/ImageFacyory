"""
Tests for the refactored Properties Panel components.
"""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from src.pixelflow_studio.viewmodels.properties_viewmodel import PropertiesViewModel, NodeInfo, PinInfo
from src.pixelflow_studio.views.properties.properties_panel import PropertiesPanel
from src.pixelflow_studio.core.application import Application


class TestPropertiesPanelRefactored:
    """Test the refactored Properties Panel."""
    
    @pytest.fixture
    def app(self):
        """Create test application."""
        return Application()
    
    @pytest.fixture
    def viewmodel(self, app):
        """Create PropertiesViewModel."""
        return PropertiesViewModel(app)
    
    @pytest.fixture
    def properties_panel(self, viewmodel):
        """Create PropertiesPanel."""
        return PropertiesPanel(viewmodel)
    
    def test_properties_panel_creation(self, properties_panel):
        """Test that PropertiesPanel can be created."""
        assert properties_panel is not None
        assert properties_panel.viewmodel is not None
        assert properties_panel.node_info_widget is not None
        assert properties_panel.node_properties_widget is not None
        assert properties_panel.pin_properties_widget is not None
        assert properties_panel.variable_properties_widget is not None
    
    def test_node_selection(self, properties_panel, viewmodel):
        """Test node selection functionality."""
        # Create test node info
        node_info = NodeInfo(
            id="test_node_1",
            name="Test Node",
            category="Generator",
            description="A test node",
            position=(100.0, 200.0),
            node_type="SolidColorNode"
        )
        
        # Select node
        viewmodel.select_node(node_info.id)
        
        # Check that appropriate widgets are shown
        assert properties_panel.node_info_widget.isVisible()
        assert properties_panel.node_properties_widget.isVisible()
        assert not properties_panel.pin_properties_widget.isVisible()
        assert not properties_panel.variable_properties_widget.isVisible()
        assert properties_panel.delete_btn.isVisible()
    
    def test_pin_selection(self, properties_panel, viewmodel):
        """Test pin selection functionality."""
        # Create test pin info
        pin_info = PinInfo(
            id="test_pin_1",
            name="Test Pin",
            pin_type="FLOAT",
            direction="Input",
            value=1.5,
            connections_count=0
        )
        
        # Select pin
        viewmodel.select_pin("test_node_1", pin_info.id)
        
        # Check that appropriate widgets are shown
        assert not properties_panel.node_info_widget.isVisible()
        assert not properties_panel.node_properties_widget.isVisible()
        assert properties_panel.pin_properties_widget.isVisible()
        assert not properties_panel.variable_properties_widget.isVisible()
        assert not properties_panel.delete_btn.isVisible()
    
    def test_selection_cleared(self, properties_panel, viewmodel):
        """Test clearing selection."""
        # First select a node
        node_info = NodeInfo(
            id="test_node_1",
            name="Test Node",
            category="Generator",
            description="A test node",
            position=(100.0, 200.0),
            node_type="SolidColorNode"
        )
        viewmodel.select_node(node_info.id)
        
        # Clear selection
        viewmodel.select_node("")
        
        # Check that all widgets are hidden
        assert not properties_panel.node_info_widget.isVisible()
        assert not properties_panel.node_properties_widget.isVisible()
        assert not properties_panel.pin_properties_widget.isVisible()
        assert not properties_panel.variable_properties_widget.isVisible()
        assert not properties_panel.delete_btn.isVisible()
    
    def test_variable_properties(self, properties_panel):
        """Test variable properties display."""
        # Create test variable data
        variable_data = {
            'id': 'test_var_1',
            'name': 'Test Variable',
            'type': 'Float',
            'value': 3.14,
            'description': 'A test variable'
        }
        
        # Show variable properties
        properties_panel.show_variable_properties(variable_data)
        
        # Check that appropriate widgets are shown
        assert not properties_panel.node_info_widget.isVisible()
        assert not properties_panel.node_properties_widget.isVisible()
        assert not properties_panel.pin_properties_widget.isVisible()
        assert properties_panel.variable_properties_widget.isVisible()
        assert not properties_panel.delete_btn.isVisible()
    
    def test_delete_button_functionality(self, properties_panel, viewmodel):
        """Test delete button functionality."""
        # Select a node
        node_info = NodeInfo(
            id="test_node_1",
            name="Test Node",
            category="Generator",
            description="A test node",
            position=(100.0, 200.0),
            node_type="SolidColorNode"
        )
        viewmodel.select_node(node_info.id)
        
        # Check that delete button is visible
        assert properties_panel.delete_btn.isVisible()
        
        # Test delete functionality (this would require mocking the confirmation dialog)
        # For now, just check that the method exists
        assert hasattr(properties_panel, 'delete_current_node')
        assert callable(properties_panel.delete_current_node)


class TestNodeInfoWidget:
    """Test NodeInfoWidget component."""
    
    @pytest.fixture
    def app(self):
        """Create test application."""
        return Application()
    
    @pytest.fixture
    def viewmodel(self, app):
        """Create PropertiesViewModel."""
        return PropertiesViewModel(app)
    
    @pytest.fixture
    def node_info_widget(self, viewmodel):
        """Create NodeInfoWidget."""
        from src.pixelflow_studio.views.properties.node_info_widget import NodeInfoWidget
        return NodeInfoWidget(viewmodel)
    
    def test_node_info_widget_creation(self, node_info_widget):
        """Test that NodeInfoWidget can be created."""
        assert node_info_widget is not None
        assert node_info_widget.viewmodel is not None
        assert node_info_widget.group_box is not None
        assert node_info_widget.form_layout is not None
    
    def test_node_info_display(self, node_info_widget):
        """Test node info display."""
        # Create test node info
        node_info = NodeInfo(
            id="test_node_1",
            name="Test Node",
            category="Generator",
            description="A test node description",
            position=(100.0, 200.0),
            node_type="SolidColorNode"
        )
        
        # Update widget with node info
        node_info_widget.on_node_info_changed(node_info)
        
        # Check that widget is visible
        assert node_info_widget.isVisible()
        
        # Check that title is set correctly
        assert node_info_widget.group_box.title() == "Node Information"


class TestNodePropertiesWidget:
    """Test NodePropertiesWidget component."""
    
    @pytest.fixture
    def app(self):
        """Create test application."""
        return Application()
    
    @pytest.fixture
    def viewmodel(self, app):
        """Create PropertiesViewModel."""
        return PropertiesViewModel(app)
    
    @pytest.fixture
    def node_properties_widget(self, viewmodel):
        """Create NodePropertiesWidget."""
        from src.pixelflow_studio.views.properties.node_properties_widget import NodePropertiesWidget
        return NodePropertiesWidget(viewmodel)
    
    def test_node_properties_widget_creation(self, node_properties_widget):
        """Test that NodePropertiesWidget can be created."""
        assert node_properties_widget is not None
        assert node_properties_widget.viewmodel is not None
        assert node_properties_widget.group_box is not None
        assert node_properties_widget.form_layout is not None
    
    def test_pin_editor_creation(self, node_properties_widget):
        """Test pin editor creation."""
        # Test that the method exists
        assert hasattr(node_properties_widget, 'create_pin_editor')
        assert callable(node_properties_widget.create_pin_editor) 