"""
СИСТЕМА ЗАПИСИ И ПРОВЕРКИ ДЕМО
Философия: "Законы пишутся на крови, но мы пишем их ДО пролития крови"

Эта система записывает каждое действие пользователя как "демо" (как в играх),
затем может воспроизвести это демо и проверить, что все работает правильно.
Позволяет предсказывать и предотвращать проблемы ДО их появления.
"""

import json
import time
import threading
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from enum import Enum
from uuid import uuid4

from loguru import logger
from PySide6.QtCore import QObject, Signal, QPoint, QPointF
from PySide6.QtGui import QMouseEvent, QKeyEvent, QWheelEvent

from .types import Position, NodeID, PinID, ConnectionID


class ActionType(Enum):
    """Типы действий в системе"""
    MOUSE_CLICK = "mouse_click"
    MOUSE_MOVE = "mouse_move"
    MOUSE_WHEEL = "mouse_wheel"
    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"
    NODE_CREATE = "node_create"
    NODE_DELETE = "node_delete"
    NODE_MOVE = "node_move"
    CONNECTION_CREATE = "connection_create"
    CONNECTION_DELETE = "connection_delete"
    CONTEXT_MENU = "context_menu"
    UI_CHANGE = "ui_change"
    SYSTEM_STATE = "system_state"


class ExpectedOutcome(Enum):
    """Ожидаемые результаты действий"""
    SUCCESS = "success"
    FAILURE = "failure"
    NO_CHANGE = "no_change"
    SPECIFIC_STATE = "specific_state"


@dataclass
class DemoAction:
    """Одно действие в демо записи"""
    id: str
    timestamp: float
    action_type: ActionType
    data: Dict[str, Any]
    expected_outcome: ExpectedOutcome
    expected_state: Dict[str, Any]
    actual_outcome: Optional[ExpectedOutcome] = None
    actual_state: Optional[Dict[str, Any]] = None
    success: Optional[bool] = None
    error_message: Optional[str] = None


@dataclass
class SystemSnapshot:
    """Снимок состояния системы в определенный момент"""
    timestamp: float
    nodes_count: int
    connections_count: int
    scene_items_count: int
    selected_items: List[str]
    ui_state: Dict[str, Any]
    memory_usage: Optional[int] = None
    performance_metrics: Optional[Dict[str, float]] = None


class ProphiticRule:
    """Профетическое правило - закон, написанный ДО проблемы"""
    
    def __init__(self, name: str, description: str, check_function: Callable, 
                 severity: str = "warning", auto_fix: Optional[Callable] = None):
        self.name = name
        self.description = description
        self.check_function = check_function
        self.severity = severity  # "critical", "warning", "info"
        self.auto_fix = auto_fix
        self.violation_count = 0
        self.last_violation = None
    
    def check(self, demo_action: DemoAction, system_state: SystemSnapshot) -> bool:
        """Проверить правило"""
        try:
            violation = self.check_function(demo_action, system_state)
            if violation:
                self.violation_count += 1
                self.last_violation = time.time()
                logger.warning(f"🚨 Правило нарушено: {self.name} - {self.description}")
                
                if self.auto_fix:
                    logger.info(f"🔧 Попытка автоисправления: {self.name}")
                    self.auto_fix(demo_action, system_state)
                
                return False
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке правила {self.name}: {e}")
            return False


class DemoRecorder(QObject):
    """Записывает действия пользователя в демо файл"""
    
    action_recorded = Signal(DemoAction)
    
    def __init__(self):
        super().__init__()
        self.recording = False
        self.current_demo: List[DemoAction] = []
        self.start_time = 0
        self.demo_name = ""
        
    def start_recording(self, demo_name: str) -> None:
        """Начать запись демо"""
        self.demo_name = demo_name
        self.current_demo = []
        self.start_time = time.time()
        self.recording = True
        logger.info(f"🎬 Начата запись демо: {demo_name}")
    
    def stop_recording(self) -> List[DemoAction]:
        """Остановить запись и вернуть записанное демо"""
        self.recording = False
        logger.info(f"⏹️ Запись демо остановлена: {self.demo_name} ({len(self.current_demo)} действий)")
        return self.current_demo.copy()
    
    def record_action(self, action_type: ActionType, data: Dict[str, Any], 
                     expected_outcome: ExpectedOutcome = ExpectedOutcome.SUCCESS,
                     expected_state: Dict[str, Any] = None) -> None:
        """Записать действие"""
        if not self.recording:
            return
            
        action = DemoAction(
            id=str(uuid4()),
            timestamp=time.time() - self.start_time,
            action_type=action_type,
            data=data,
            expected_outcome=expected_outcome,
            expected_state=expected_state or {}
        )
        
        self.current_demo.append(action)
        self.action_recorded.emit(action)
        logger.debug(f"📝 Записано действие: {action_type.value}")


class DemoPlayer:
    """Воспроизводит записанное демо и проверяет результаты"""
    
    def __init__(self, application):
        self.app = application
        self.current_demo: List[DemoAction] = []
        self.playing = False
        self.current_action_index = 0
        
    def load_demo(self, demo_path: Path) -> bool:
        """Загрузить демо из файла"""
        try:
            with open(demo_path, 'r', encoding='utf-8') as f:
                demo_data = json.load(f)
                
            self.current_demo = []
            for action_data in demo_data.get('actions', []):
                action = DemoAction(
                    id=action_data['id'],
                    timestamp=action_data['timestamp'],
                    action_type=ActionType(action_data['action_type']),
                    data=action_data['data'],
                    expected_outcome=ExpectedOutcome(action_data['expected_outcome']),
                    expected_state=action_data['expected_state']
                )
                self.current_demo.append(action)
            
            logger.info(f"📂 Загружено демо: {demo_path} ({len(self.current_demo)} действий)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки демо {demo_path}: {e}")
            return False
    
    def play_demo(self, verify_each_step: bool = True) -> Dict[str, Any]:
        """Воспроизвести демо и проверить результаты"""
        if not self.current_demo:
            return {"success": False, "error": "Демо не загружено"}
        
        self.playing = True
        self.current_action_index = 0
        
        results = {
            "success": True,
            "total_actions": len(self.current_demo),
            "successful_actions": 0,
            "failed_actions": 0,
            "errors": [],
            "performance": {}
        }
        
        start_time = time.time()
        
        try:
            for i, action in enumerate(self.current_demo):
                if not self.playing:
                    break
                    
                self.current_action_index = i
                logger.info(f"🎮 Воспроизведение действия {i+1}/{len(self.current_demo)}: {action.action_type.value}")
                
                # Воспроизвести действие
                success = self._execute_action(action)
                
                if success:
                    results["successful_actions"] += 1
                    action.success = True
                else:
                    results["failed_actions"] += 1
                    action.success = False
                    results["errors"].append({
                        "action_index": i,
                        "action_type": action.action_type.value,
                        "error": action.error_message
                    })
                
                # Проверить состояние системы если требуется
                if verify_each_step:
                    self._verify_system_state(action)
                
                # Небольшая задержка для имитации человеческих действий
                time.sleep(0.1)
        
        except Exception as e:
            logger.error(f"❌ Критическая ошибка при воспроизведении демо: {e}")
            results["success"] = False
            results["errors"].append({"critical_error": str(e)})
        
        finally:
            self.playing = False
            results["performance"]["total_time"] = time.time() - start_time
            results["performance"]["actions_per_second"] = len(self.current_demo) / results["performance"]["total_time"]
        
        logger.info(f"🎯 Демо завершено: {results['successful_actions']}/{results['total_actions']} успешных действий")
        return results
    
    def _execute_action(self, action: DemoAction) -> bool:
        """Выполнить одно действие"""
        try:
            if action.action_type == ActionType.NODE_CREATE:
                return self._execute_node_create(action)
            elif action.action_type == ActionType.CONNECTION_CREATE:
                return self._execute_connection_create(action)
            elif action.action_type == ActionType.MOUSE_CLICK:
                return self._execute_mouse_click(action)
            elif action.action_type == ActionType.CONTEXT_MENU:
                return self._execute_context_menu(action)
            else:
                logger.warning(f"⚠️ Неизвестный тип действия: {action.action_type}")
                return False
                
        except Exception as e:
            action.error_message = str(e)
            logger.error(f"❌ Ошибка выполнения действия {action.action_type}: {e}")
            return False
    
    def _execute_node_create(self, action: DemoAction) -> bool:
        """Выполнить создание ноды"""
        try:
            class_name = action.data.get('class_name')
            position = action.data.get('position', {})
            pos = Position(position.get('x', 0), position.get('y', 0))
            
            # Подсчитаем ноды до
            nodes_before = len(self.app.graph.nodes)
            
            # Создаем ноду
            node = self.app.create_node(class_name)
            node.position = pos
            self.app.graph.add_node(node)
            
            # Проверяем результат
            nodes_after = len(self.app.graph.nodes)
            created_count = nodes_after - nodes_before
            
            action.actual_state = {
                "nodes_before": nodes_before,
                "nodes_after": nodes_after,
                "created_count": created_count
            }
            
            # Проверяем ожидания
            expected_count = action.expected_state.get('expected_nodes_created', 1)
            if created_count == expected_count:
                action.actual_outcome = ExpectedOutcome.SUCCESS
                return True
            else:
                action.actual_outcome = ExpectedOutcome.FAILURE
                action.error_message = f"Создано {created_count} нод, ожидалось {expected_count}"
                return False
                
        except Exception as e:
            action.error_message = str(e)
            return False
    
    def _execute_connection_create(self, action: DemoAction) -> bool:
        """Выполнить создание соединения"""
        try:
            # Получаем данные о соединении
            output_node_id = action.data.get('output_node_id')
            output_pin_name = action.data.get('output_pin_name')
            input_node_id = action.data.get('input_node_id')
            input_pin_name = action.data.get('input_pin_name')
            
            # Найти ноды
            output_node = None
            input_node = None
            
            for node in self.app.graph.nodes:
                if node.id == output_node_id:
                    output_node = node
                elif node.id == input_node_id:
                    input_node = node
            
            if not output_node or not input_node:
                action.error_message = "Ноды для соединения не найдены"
                return False
            
            # Найти пины
            output_pin = output_node.get_output_pin(output_pin_name)
            input_pin = input_node.get_input_pin(input_pin_name)
            
            if not output_pin or not input_pin:
                action.error_message = "Пины для соединения не найдены"
                return False
            
            # Создать соединение
            connections_before = len(self.app.graph.connections)
            connection = self.app.graph.connect_pins(output_pin, input_pin)
            connections_after = len(self.app.graph.connections)
            
            action.actual_state = {
                "connections_before": connections_before,
                "connections_after": connections_after,
                "connection_created": connection is not None
            }
            
            if connection:
                action.actual_outcome = ExpectedOutcome.SUCCESS
                return True
            else:
                action.actual_outcome = ExpectedOutcome.FAILURE
                action.error_message = "Соединение не было создано"
                return False
                
        except Exception as e:
            action.error_message = str(e)
            return False
    
    def _execute_mouse_click(self, action: DemoAction) -> bool:
        """Выполнить клик мыши"""
        # Для демо режима просто логируем действие
        pos = action.data.get('position', {})
        button = action.data.get('button', 'left')
        logger.debug(f"🖱️ Клик мыши: {button} кнопка в ({pos.get('x', 0)}, {pos.get('y', 0)})")
        return True
    
    def _execute_context_menu(self, action: DemoAction) -> bool:
        """Выполнить действие контекстного меню"""
        menu_action = action.data.get('menu_action')
        logger.debug(f"📋 Контекстное меню: {menu_action}")
        return True
    
    def _verify_system_state(self, action: DemoAction) -> None:
        """Проверить состояние системы после действия"""
        current_state = self._capture_system_state()
        
        # Сравнить с ожидаемым состоянием
        expected = action.expected_state
        for key, expected_value in expected.items():
            actual_value = current_state.get(key)
            if actual_value != expected_value:
                logger.warning(f"⚠️ Состояние не соответствует ожиданиям: {key} = {actual_value}, ожидалось {expected_value}")
    
    def _capture_system_state(self) -> Dict[str, Any]:
        """Захватить текущее состояние системы"""
        return {
            "nodes_count": len(self.app.graph.nodes),
            "connections_count": len(self.app.graph.connections),
            "timestamp": time.time()
        }


class PropheticRulesEngine:
    """Движок профетических правил - пишет законы ДО проблем"""
    
    def __init__(self):
        self.rules: List[ProphiticRule] = []
        self.violations_log: List[Dict[str, Any]] = []
        self._setup_default_rules()
    
    def _setup_default_rules(self) -> None:
        """Настроить правила по умолчанию"""
        
        # Правило: Дублирование нод
        def check_node_duplication(action: DemoAction, state: SystemSnapshot) -> bool:
            if action.action_type == ActionType.NODE_CREATE:
                actual_created = action.actual_state.get('created_count', 1) if action.actual_state else 1
                return actual_created > 1
            return False
        
        self.add_rule(ProphiticRule(
            name="no_node_duplication",
            description="Создание ноды не должно приводить к дублированию",
            check_function=check_node_duplication,
            severity="critical"
        ))
        
        # Правило: Производительность
        def check_performance(action: DemoAction, state: SystemSnapshot) -> bool:
            if state.performance_metrics:
                response_time = state.performance_metrics.get('response_time', 0)
                return response_time > 1.0  # Действие заняло больше 1 секунды
            return False
        
        self.add_rule(ProphiticRule(
            name="performance_threshold",
            description="Действия должны выполняться быстро (< 1 сек)",
            check_function=check_performance,
            severity="warning"
        ))
        
        # Правило: Утечки памяти
        def check_memory_leak(action: DemoAction, state: SystemSnapshot) -> bool:
            if state.memory_usage and hasattr(self, '_previous_memory'):
                memory_growth = state.memory_usage - self._previous_memory
                return memory_growth > 50 * 1024 * 1024  # Рост больше 50MB
            self._previous_memory = state.memory_usage or 0
            return False
        
        self.add_rule(ProphiticRule(
            name="memory_leak_prevention",
            description="Каждое действие не должно вызывать утечку памяти",
            check_function=check_memory_leak,
            severity="critical"
        ))
    
    def add_rule(self, rule: ProphiticRule) -> None:
        """Добавить новое правило"""
        self.rules.append(rule)
        logger.info(f"📜 Добавлено профетическое правило: {rule.name}")
    
    def check_all_rules(self, action: DemoAction, state: SystemSnapshot) -> Dict[str, Any]:
        """Проверить все правила"""
        results = {
            "total_rules": len(self.rules),
            "passed": 0,
            "failed": 0,
            "violations": []
        }
        
        for rule in self.rules:
            try:
                violation = rule.check(action, state)
                if violation:
                    results["failed"] += 1
                    violation_record = {
                        "rule": rule.name,
                        "severity": rule.severity,
                        "description": rule.description,
                        "timestamp": time.time(),
                        "action_type": action.action_type.value
                    }
                    results["violations"].append(violation_record)
                    self.violations_log.append(violation_record)
                else:
                    results["passed"] += 1
                    
            except Exception as e:
                logger.error(f"❌ Ошибка при проверке правила {rule.name}: {e}")
                results["failed"] += 1
        
        return results


class DemoSystem:
    """Главная система демо записи и проверки"""
    
    def __init__(self, application):
        self.app = application
        self.recorder = DemoRecorder()
        self.player = DemoPlayer(application)
        self.rules_engine = PropheticRulesEngine()
        self.demos_dir = Path("demos")
        self.demos_dir.mkdir(exist_ok=True)
    
    def start_recording(self, demo_name: str) -> None:
        """Начать запись нового демо"""
        self.recorder.start_recording(demo_name)
    
    def stop_recording_and_save(self) -> Path:
        """Остановить запись и сохранить демо"""
        actions = self.recorder.stop_recording()
        demo_path = self.save_demo(self.recorder.demo_name, actions)
        return demo_path
    
    def save_demo(self, name: str, actions: List[DemoAction]) -> Path:
        """Сохранить демо в файл"""
        demo_path = self.demos_dir / f"{name}.json"
        
        demo_data = {
            "name": name,
            "created_at": time.time(),
            "actions_count": len(actions),
            "actions": [asdict(action) for action in actions]
        }
        
        with open(demo_path, 'w', encoding='utf-8') as f:
            json.dump(demo_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Демо сохранено: {demo_path}")
        return demo_path
    
    def play_demo_and_verify(self, demo_path: Path) -> Dict[str, Any]:
        """Воспроизвести демо и проверить все правила"""
        if not self.player.load_demo(demo_path):
            return {"success": False, "error": "Не удалось загрузить демо"}
        
        # Воспроизвести демо
        play_results = self.player.play_demo(verify_each_step=True)
        
        # Проверить правила для каждого действия
        rules_results = []
        for action in self.player.current_demo:
            if action.actual_state:
                state = SystemSnapshot(
                    timestamp=action.timestamp,
                    nodes_count=action.actual_state.get('nodes_after', 0),
                    connections_count=action.actual_state.get('connections_after', 0),
                    scene_items_count=0,
                    selected_items=[],
                    ui_state={}
                )
                rule_check = self.rules_engine.check_all_rules(action, state)
                rules_results.append(rule_check)
        
        # Объединить результаты
        combined_results = {
            **play_results,
            "rules_check": rules_results,
            "total_violations": sum(r["failed"] for r in rules_results),
            "demo_path": str(demo_path)
        }
        
        return combined_results
    
    def record_action(self, action_type: ActionType, data: Dict[str, Any], 
                     expected_outcome: ExpectedOutcome = ExpectedOutcome.SUCCESS,
                     expected_state: Dict[str, Any] = None) -> None:
        """Записать действие (используется интеграцией с UI)"""
        self.recorder.record_action(action_type, data, expected_outcome, expected_state)


# Глобальный экземпляр системы демо
_demo_system = None


def get_demo_system(application=None):
    """Получить глобальный экземпляр системы демо"""
    global _demo_system
    if _demo_system is None and application:
        _demo_system = DemoSystem(application)
    return _demo_system