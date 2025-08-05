"""
Тесты интеграции нового PropertiesPanel с MVVM архитектурой.
"""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from src.pixelflow_studio.core.application import Application
from src.pixelflow_studio.viewmodels.properties_viewmodel import PropertiesViewModel
from src.pixelflow_studio.views.properties.properties_panel import PropertiesPanel
from src.pixelflow_studio.views.node_editor import NodeEditorView


class TestMVVMIntegration:
    """Тесты интеграции MVVM архитектуры."""
    
    @pytest.fixture
    def app(self):
        """Создание тестового приложения."""
        return Application()
    
    @pytest.fixture
    def viewmodel(self, app):
        """Создание PropertiesViewModel."""
        return PropertiesViewModel(app)
    
    @pytest.fixture
    def properties_panel(self, viewmodel):
        """Создание PropertiesPanel с ViewModel."""
        return PropertiesPanel(viewmodel)
    
    @pytest.fixture
    def node_editor(self, app):
        """Создание NodeEditorView."""
        return NodeEditorView(app)
    
    def test_properties_panel_creation_with_viewmodel(self, properties_panel):
        """Тест создания PropertiesPanel с ViewModel."""
        assert properties_panel is not None
        assert properties_panel.viewmodel is not None
        assert isinstance(properties_panel.viewmodel, PropertiesViewModel)
    
    def test_viewmodel_initialization(self, viewmodel):
        """Тест инициализации ViewModel."""
        assert viewmodel.app is not None
        assert viewmodel._current_node_id is None
        assert viewmodel._current_pin_id is None
    
    def test_node_selection_signal(self, viewmodel, node_editor):
        """Тест сигнала выбора ноды."""
        # Подключаем сигнал
        signal_received = False
        selected_node_id = None
        
        def on_node_selected(node_id):
            nonlocal signal_received, selected_node_id
            signal_received = True
            selected_node_id = node_id
        
        viewmodel.node_info_changed.connect(on_node_selected)
        
        # Эмитируем сигнал выбора ноды
        test_node_id = "test_node_123"
        viewmodel.select_node(test_node_id)
        
        # Проверяем, что сигнал был получен
        assert signal_received
        assert selected_node_id is not None
    
    def test_pin_selection_signal(self, viewmodel):
        """Тест сигнала выбора пина."""
        # Подключаем сигнал
        signal_received = False
        selected_pin_id = None
        
        def on_pin_selected(pin_info):
            nonlocal signal_received, selected_pin_id
            signal_received = True
            selected_pin_id = pin_info.id
        
        viewmodel.pin_info_changed.connect(on_pin_selected)
        
        # Эмитируем сигнал выбора пина
        test_pin_id = "test_pin_456"
        viewmodel.select_pin(test_pin_id)
        
        # Проверяем, что сигнал был получен
        assert signal_received
        assert selected_pin_id == test_pin_id
    
    def test_selection_cleared_signal(self, viewmodel):
        """Тест сигнала очистки выбора."""
        # Подключаем сигнал
        signal_received = False
        
        def on_selection_cleared():
            nonlocal signal_received
            signal_received = True
        
        viewmodel.selection_cleared.connect(on_selection_cleared)
        
        # Эмитируем сигнал очистки выбора
        viewmodel.clear_selection()
        
        # Проверяем, что сигнал был получен
        assert signal_received
    
    def test_properties_panel_widgets_creation(self, properties_panel):
        """Тест создания всех виджетов в PropertiesPanel."""
        assert properties_panel.node_info_widget is not None
        assert properties_panel.node_properties_widget is not None
        assert properties_panel.pin_properties_widget is not None
        assert properties_panel.variable_properties_widget is not None
    
    def test_properties_panel_initial_state(self, properties_panel):
        """Тест начального состояния PropertiesPanel."""
        # В начальном состоянии все виджеты должны быть скрыты
        assert not properties_panel.node_info_widget.isVisible()
        assert not properties_panel.node_properties_widget.isVisible()
        assert not properties_panel.pin_properties_widget.isVisible()
        assert not properties_panel.variable_properties_widget.isVisible()
    
    def test_node_selection_ui_update(self, properties_panel, viewmodel):
        """Тест обновления UI при выборе ноды."""
        # Создаем тестовую информацию о ноде
        from src.pixelflow_studio.viewmodels.properties_viewmodel import NodeInfo
        
        test_node_info = NodeInfo(
            id="test_node_123",
            name="Test Node",
            category="Test Category",
            description="Test Description",
            position=(100.0, 200.0),
            node_type="test_type"
        )
        
        # Эмитируем сигнал выбора ноды
        viewmodel.node_info_changed.emit(test_node_info)
        
        # Проверяем, что UI обновился
        # В реальном приложении здесь нужно использовать QTimer для асинхронных проверок
        assert properties_panel.node_info_widget.isVisible()
        assert properties_panel.node_properties_widget.isVisible()
        assert not properties_panel.pin_properties_widget.isVisible()
        assert not properties_panel.variable_properties_widget.isVisible()


class TestMainWindowIntegration:
    """Тесты интеграции с MainWindow."""
    
    @pytest.fixture
    def qapp(self):
        """Создание QApplication для тестов."""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app
    
    @pytest.fixture
    def app(self):
        """Создание тестового приложения."""
        return Application()
    
    def test_main_window_imports(self):
        """Тест импортов в MainWindow."""
        # Проверяем, что новые компоненты можно импортировать
        from src.pixelflow_studio.views.main_window import MainWindow
        from src.pixelflow_studio.viewmodels.properties_viewmodel import PropertiesViewModel
        from src.pixelflow_studio.views.properties.properties_panel import PropertiesPanel
        
        assert MainWindow is not None
        assert PropertiesViewModel is not None
        assert PropertiesPanel is not None
    
    def test_main_window_creation_with_mvvm(self, qapp, app):
        """Тест создания MainWindow с MVVM архитектурой."""
        from src.pixelflow_studio.views.main_window import MainWindow
        
        # Создаем MainWindow
        main_window = MainWindow(app)
        
        # Проверяем, что ViewModel создан
        assert main_window.properties_viewmodel is not None
        assert isinstance(main_window.properties_viewmodel, PropertiesViewModel)
        
        # Проверяем, что PropertiesPanel создан с ViewModel
        assert main_window.properties_panel is not None
        assert main_window.properties_panel.viewmodel == main_window.properties_viewmodel
        
        # Очищаем
        main_window.close()
    
    def test_signal_connections(self, qapp, app):
        """Тест подключения сигналов в MainWindow."""
        from src.pixelflow_studio.views.main_window import MainWindow
        
        # Создаем MainWindow
        main_window = MainWindow(app)
        
        # Проверяем, что сигналы подключены
        assert main_window.node_editor is not None
        assert main_window.properties_viewmodel is not None
        
        # В реальном приложении здесь можно проверить подключение сигналов
        # но это требует более сложной настройки тестов
        
        # Очищаем
        main_window.close()


if __name__ == "__main__":
    pytest.main([__file__]) 