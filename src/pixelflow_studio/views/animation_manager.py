"""
Animation Manager for PixelFlow Studio.

This module provides smooth animations and transitions for various UI elements,
improving the visual feedback and user experience.
"""

from __future__ import annotations

from typing import Optional, Callable, Any
from PySide6.QtWidgets import QWidget, QGraphicsItem
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, QParallelAnimationGroup, QSequentialAnimationGroup
from PySide6.QtGui import QColor

from ..core.logging_config import get_logger

logger = get_logger("animation_manager")


class AnimationManager:
    """
    Centralized animation manager for smooth UI transitions.
    
    Features:
    - Node creation animations
    - Connection creation animations
    - Selection animations
    - Fade in/out effects
    - Scale animations
    - Color transitions
    """
    
    def __init__(self):
        self.active_animations: list[QPropertyAnimation] = []
        self.animation_groups: list[QParallelAnimationGroup] = []
        
        logger.info("Animation manager initialized")
    
    def animate_node_creation(self, node_widget: QWidget, duration: int = 300) -> None:
        """Animate node creation with fade-in and scale effects."""
        try:
            # Create animation group
            group = QParallelAnimationGroup()
            
            # Opacity animation
            opacity_anim = QPropertyAnimation(node_widget, b"windowOpacity")
            opacity_anim.setStartValue(0.0)
            opacity_anim.setEndValue(1.0)
            opacity_anim.setDuration(duration)
            opacity_anim.setEasingCurve(QEasingCurve.OutCubic)
            
            # Scale animation (if supported)
            if hasattr(node_widget, 'setTransform'):
                scale_anim = QPropertyAnimation(node_widget, b"transform")
                scale_anim.setStartValue(0.8)
                scale_anim.setEndValue(1.0)
                scale_anim.setDuration(duration)
                scale_anim.setEasingCurve(QEasingCurve.OutBack)
                group.addAnimation(scale_anim)
            
            group.addAnimation(opacity_anim)
            group.start()
            
            self.animation_groups.append(group)
            group.finished.connect(lambda: self._cleanup_animation(group))
            
            logger.debug(f"Node creation animation started for {node_widget}")
            
        except Exception as e:
            logger.error(f"Error animating node creation: {e}")
    
    def animate_connection_creation(self, connection_item: QGraphicsItem, duration: int = 200) -> None:
        """Animate connection creation with drawing effect."""
        try:
            # Create sequential animation group
            group = QSequentialAnimationGroup()
            
            # Opacity animation
            opacity_anim = QPropertyAnimation(connection_item, b"opacity")
            opacity_anim.setStartValue(0.0)
            opacity_anim.setEndValue(1.0)
            opacity_anim.setDuration(duration)
            opacity_anim.setEasingCurve(QEasingCurve.OutCubic)
            
            # Pulse effect
            pulse_anim = QPropertyAnimation(connection_item, b"scale")
            pulse_anim.setStartValue(1.0)
            pulse_anim.setEndValue(1.1)
            pulse_anim.setDuration(100)
            pulse_anim.setEasingCurve(QEasingCurve.OutQuad)
            
            # Return to normal scale
            return_anim = QPropertyAnimation(connection_item, b"scale")
            return_anim.setStartValue(1.1)
            return_anim.setEndValue(1.0)
            return_anim.setDuration(100)
            return_anim.setEasingCurve(QEasingCurve.InQuad)
            
            group.addAnimation(opacity_anim)
            group.addAnimation(pulse_anim)
            group.addAnimation(return_anim)
            group.start()
            
            self.animation_groups.append(group)
            group.finished.connect(lambda: self._cleanup_animation(group))
            
            logger.debug(f"Connection creation animation started")
            
        except Exception as e:
            logger.error(f"Error animating connection creation: {e}")
    
    def animate_selection(self, widget: QWidget, selected: bool = True, duration: int = 150) -> None:
        """Animate selection state change."""
        try:
            # Create animation group
            group = QParallelAnimationGroup()
            
            # Border color animation
            if hasattr(widget, 'setStyleSheet'):
                # Animate border color
                border_anim = QPropertyAnimation(widget, b"styleSheet")
                if selected:
                    border_anim.setStartValue("border: 1px solid #666;")
                    border_anim.setEndValue("border: 2px solid #4080FF;")
                else:
                    border_anim.setStartValue("border: 2px solid #4080FF;")
                    border_anim.setEndValue("border: 1px solid #666;")
                
                border_anim.setDuration(duration)
                border_anim.setEasingCurve(QEasingCurve.OutCubic)
                group.addAnimation(border_anim)
            
            # Scale animation
            if hasattr(widget, 'setTransform'):
                scale_anim = QPropertyAnimation(widget, b"transform")
                if selected:
                    scale_anim.setStartValue(1.0)
                    scale_anim.setEndValue(1.02)
                else:
                    scale_anim.setStartValue(1.02)
                    scale_anim.setEndValue(1.0)
                
                scale_anim.setDuration(duration)
                scale_anim.setEasingCurve(QEasingCurve.OutQuad)
                group.addAnimation(scale_anim)
            
            group.start()
            self.animation_groups.append(group)
            group.finished.connect(lambda: self._cleanup_animation(group))
            
            logger.debug(f"Selection animation started for {widget}")
            
        except Exception as e:
            logger.error(f"Error animating selection: {e}")
    
    def animate_fade_in(self, widget: QWidget, duration: int = 200) -> None:
        """Animate fade-in effect."""
        try:
            anim = QPropertyAnimation(widget, b"windowOpacity")
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setDuration(duration)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            
            anim.start()
            self.active_animations.append(anim)
            anim.finished.connect(lambda: self._cleanup_animation(anim))
            
            logger.debug(f"Fade-in animation started for {widget}")
            
        except Exception as e:
            logger.error(f"Error animating fade-in: {e}")
    
    def animate_fade_out(self, widget: QWidget, duration: int = 200, callback: Optional[Callable] = None) -> None:
        """Animate fade-out effect with optional callback."""
        try:
            anim = QPropertyAnimation(widget, b"windowOpacity")
            anim.setStartValue(1.0)
            anim.setEndValue(0.0)
            anim.setDuration(duration)
            anim.setEasingCurve(QEasingCurve.InCubic)
            
            if callback:
                anim.finished.connect(callback)
            
            anim.start()
            self.active_animations.append(anim)
            anim.finished.connect(lambda: self._cleanup_animation(anim))
            
            logger.debug(f"Fade-out animation started for {widget}")
            
        except Exception as e:
            logger.error(f"Error animating fade-out: {e}")
    
    def animate_color_transition(self, widget: QWidget, start_color: QColor, end_color: QColor, 
                               duration: int = 300) -> None:
        """Animate color transition."""
        try:
            anim = QPropertyAnimation(widget, b"styleSheet")
            anim.setStartValue(f"background-color: {start_color.name()};")
            anim.setEndValue(f"background-color: {end_color.name()};")
            anim.setDuration(duration)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            
            anim.start()
            self.active_animations.append(anim)
            anim.finished.connect(lambda: self._cleanup_animation(anim))
            
            logger.debug(f"Color transition animation started for {widget}")
            
        except Exception as e:
            logger.error(f"Error animating color transition: {e}")
    
    def animate_bounce(self, widget: QWidget, duration: int = 400) -> None:
        """Animate bounce effect."""
        try:
            # Create sequential animation group
            group = QSequentialAnimationGroup()
            
            # Scale up
            scale_up = QPropertyAnimation(widget, b"transform")
            scale_up.setStartValue(1.0)
            scale_up.setEndValue(1.1)
            scale_up.setDuration(duration // 2)
            scale_up.setEasingCurve(QEasingCurve.OutQuad)
            
            # Scale down
            scale_down = QPropertyAnimation(widget, b"transform")
            scale_down.setStartValue(1.1)
            scale_down.setEndValue(1.0)
            scale_down.setDuration(duration // 2)
            scale_down.setEasingCurve(QEasingCurve.InQuad)
            
            group.addAnimation(scale_up)
            group.addAnimation(scale_down)
            group.start()
            
            self.animation_groups.append(group)
            group.finished.connect(lambda: self._cleanup_animation(group))
            
            logger.debug(f"Bounce animation started for {widget}")
            
        except Exception as e:
            logger.error(f"Error animating bounce: {e}")
    
    def animate_slide_in(self, widget: QWidget, direction: str = "left", duration: int = 300) -> None:
        """Animate slide-in effect from specified direction."""
        try:
            # Get widget geometry
            geometry = widget.geometry()
            
            # Calculate start position based on direction
            if direction == "left":
                start_pos = geometry.x() - geometry.width()
                end_pos = geometry.x()
                anim = QPropertyAnimation(widget, b"geometry")
                anim.setStartValue(geometry.translated(-geometry.width(), 0))
                anim.setEndValue(geometry)
            elif direction == "right":
                start_pos = geometry.x() + geometry.width()
                end_pos = geometry.x()
                anim = QPropertyAnimation(widget, b"geometry")
                anim.setStartValue(geometry.translated(geometry.width(), 0))
                anim.setEndValue(geometry)
            elif direction == "top":
                anim = QPropertyAnimation(widget, b"geometry")
                anim.setStartValue(geometry.translated(0, -geometry.height()))
                anim.setEndValue(geometry)
            elif direction == "bottom":
                anim = QPropertyAnimation(widget, b"geometry")
                anim.setStartValue(geometry.translated(0, geometry.height()))
                anim.setEndValue(geometry)
            else:
                logger.warning(f"Unknown slide direction: {direction}")
                return
            
            anim.setDuration(duration)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            
            anim.start()
            self.active_animations.append(anim)
            anim.finished.connect(lambda: self._cleanup_animation(anim))
            
            logger.debug(f"Slide-in animation started for {widget} from {direction}")
            
        except Exception as e:
            logger.error(f"Error animating slide-in: {e}")
    
    def animate_progress(self, widget: QWidget, progress: float, duration: int = 500) -> None:
        """Animate progress bar or similar progress indicator."""
        try:
            if hasattr(widget, 'setValue'):
                # For QProgressBar
                anim = QPropertyAnimation(widget, b"value")
                current_value = widget.value()
                target_value = int(progress * 100)  # Assuming 0-100 range
                anim.setStartValue(current_value)
                anim.setEndValue(target_value)
                anim.setDuration(duration)
                anim.setEasingCurve(QEasingCurve.OutCubic)
                
                anim.start()
                self.active_animations.append(anim)
                anim.finished.connect(lambda: self._cleanup_animation(anim))
                
                logger.debug(f"Progress animation started for {widget}")
            
        except Exception as e:
            logger.error(f"Error animating progress: {e}")
    
    def animate_highlight(self, widget: QWidget, highlight_color: QColor = QColor(64, 128, 255), 
                         duration: int = 1000) -> None:
        """Animate highlight effect with color pulse."""
        try:
            # Create sequential animation group
            group = QSequentialAnimationGroup()
            
            # Fade to highlight color
            fade_to = QPropertyAnimation(widget, b"styleSheet")
            fade_to.setStartValue("background-color: transparent;")
            fade_to.setEndValue(f"background-color: {highlight_color.name()};")
            fade_to.setDuration(duration // 2)
            fade_to.setEasingCurve(QEasingCurve.OutCubic)
            
            # Fade back to transparent
            fade_back = QPropertyAnimation(widget, b"styleSheet")
            fade_back.setStartValue(f"background-color: {highlight_color.name()};")
            fade_back.setEndValue("background-color: transparent;")
            fade_back.setDuration(duration // 2)
            fade_back.setEasingCurve(QEasingCurve.InCubic)
            
            group.addAnimation(fade_to)
            group.addAnimation(fade_back)
            group.start()
            
            self.animation_groups.append(group)
            group.finished.connect(lambda: self._cleanup_animation(group))
            
            logger.debug(f"Highlight animation started for {widget}")
            
        except Exception as e:
            logger.error(f"Error animating highlight: {e}")
    
    def stop_all_animations(self) -> None:
        """Stop all active animations."""
        try:
            for anim in self.active_animations:
                anim.stop()
            
            for group in self.animation_groups:
                group.stop()
            
            self.active_animations.clear()
            self.animation_groups.clear()
            
            logger.info("All animations stopped")
            
        except Exception as e:
            logger.error(f"Error stopping animations: {e}")
    
    def _cleanup_animation(self, animation: QPropertyAnimation | QParallelAnimationGroup | QSequentialAnimationGroup) -> None:
        """Clean up finished animations."""
        try:
            if animation in self.active_animations:
                self.active_animations.remove(animation)
            elif animation in self.animation_groups:
                self.animation_groups.remove(animation)
            
            animation.deleteLater()
            
        except Exception as e:
            logger.error(f"Error cleaning up animation: {e}")


# Global animation manager instance
_animation_manager: Optional[AnimationManager] = None


def get_animation_manager() -> AnimationManager:
    """Get the global animation manager instance."""
    global _animation_manager
    if _animation_manager is None:
        _animation_manager = AnimationManager()
    return _animation_manager


def animate_node_creation(node_widget: QWidget, duration: int = 300) -> None:
    """Animate node creation."""
    manager = get_animation_manager()
    manager.animate_node_creation(node_widget, duration)


def animate_connection_creation(connection_item: QGraphicsItem, duration: int = 200) -> None:
    """Animate connection creation."""
    manager = get_animation_manager()
    manager.animate_connection_creation(connection_item, duration)


def animate_selection(widget: QWidget, selected: bool = True, duration: int = 150) -> None:
    """Animate selection state change."""
    manager = get_animation_manager()
    manager.animate_selection(widget, selected, duration)


def animate_fade_in(widget: QWidget, duration: int = 200) -> None:
    """Animate fade-in effect."""
    manager = get_animation_manager()
    manager.animate_fade_in(widget, duration)


def animate_fade_out(widget: QWidget, duration: int = 200, callback: Optional[Callable] = None) -> None:
    """Animate fade-out effect."""
    manager = get_animation_manager()
    manager.animate_fade_out(widget, duration, callback)


def animate_bounce(widget: QWidget, duration: int = 400) -> None:
    """Animate bounce effect."""
    manager = get_animation_manager()
    manager.animate_bounce(widget, duration)


def animate_highlight(widget: QWidget, highlight_color: QColor = QColor(64, 128, 255), 
                     duration: int = 1000) -> None:
    """Animate highlight effect."""
    manager = get_animation_manager()
    manager.animate_highlight(widget, highlight_color, duration) 