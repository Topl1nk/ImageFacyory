"""
Validation system for PixelFlow Studio.

This module provides a comprehensive validation system for checking
data integrity and preventing errors throughout the application.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum

from .exceptions import ValidationError
from .constants import VALIDATION


class ValidationType(Enum):
    """Types of validation."""
    REQUIRED = "required"
    TYPE = "type"
    RANGE = "range"
    LENGTH = "length"
    PATTERN = "pattern"
    CUSTOM = "custom"


@dataclass
class ValidationRule:
    """A validation rule with its parameters."""
    validation_type: ValidationType
    message: str
    parameters: Dict[str, Any]
    
    def __post_init__(self):
        """Validate the rule itself."""
        if not isinstance(self.validation_type, ValidationType):
            raise ValueError("validation_type must be ValidationType")
        if not isinstance(self.message, str):
            raise ValueError("message must be string")
        if not isinstance(self.parameters, dict):
            raise ValueError("parameters must be dictionary")


class Validator:
    """Main validator class."""
    
    def __init__(self):
        """Initialize the validator."""
        self._rules: Dict[str, List[ValidationRule]] = {}
        self._custom_validators: Dict[str, Callable] = {}
    
    def add_rule(self, field_name: str, rule: ValidationRule) -> None:
        """
        Add a validation rule for a field.
        
        Args:
            field_name: Name of the field to validate
            rule: Validation rule to apply
        """
        if field_name not in self._rules:
            self._rules[field_name] = []
        self._rules[field_name].append(rule)
    
    def add_custom_validator(self, name: str, validator_func: Callable) -> None:
        """
        Add a custom validator function.
        
        Args:
            name: Name of the custom validator
            validator_func: Function that takes (value, parameters) and returns bool
        """
        self._custom_validators[name] = validator_func
    
    def validate(self, data: Dict[str, Any]) -> List[ValidationError]:
        """
        Validate a dictionary of data against all rules.
        
        Args:
            data: Dictionary of data to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        for field_name, rules in self._rules.items():
            value = data.get(field_name)
            
            for rule in rules:
                try:
                    if not self._validate_rule(value, rule):
                        errors.append(
                            ValidationError(field_name, value, rule.message)
                        )
                except Exception as e:
                    errors.append(
                        ValidationError(field_name, value, f"Validation failed: {e}")
                    )
        
        return errors
    
    def validate_field(self, field_name: str, value: Any) -> List[ValidationError]:
        """
        Validate a single field.
        
        Args:
            field_name: Name of the field
            value: Value to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        if field_name not in self._rules:
            return []
        
        errors = []
        for rule in self._rules[field_name]:
            try:
                if not self._validate_rule(value, rule):
                    errors.append(
                        ValidationError(field_name, value, rule.message)
                    )
            except Exception as e:
                errors.append(
                    ValidationError(field_name, value, f"Validation failed: {e}")
                )
        
        return errors
    
    def _validate_rule(self, value: Any, rule: ValidationRule) -> bool:
        """
        Validate a value against a specific rule.
        
        Args:
            value: Value to validate
            rule: Rule to apply
            
        Returns:
            True if valid, False otherwise
        """
        if rule.validation_type == ValidationType.REQUIRED:
            return self._validate_required(value, rule.parameters)
        elif rule.validation_type == ValidationType.TYPE:
            return self._validate_type(value, rule.parameters)
        elif rule.validation_type == ValidationType.RANGE:
            return self._validate_range(value, rule.parameters)
        elif rule.validation_type == ValidationType.LENGTH:
            return self._validate_length(value, rule.parameters)
        elif rule.validation_type == ValidationType.PATTERN:
            return self._validate_pattern(value, rule.parameters)
        elif rule.validation_type == ValidationType.CUSTOM:
            return self._validate_custom(value, rule.parameters)
        else:
            raise ValueError(f"Unknown validation type: {rule.validation_type}")
    
    def _validate_required(self, value: Any, params: Dict[str, Any]) -> bool:
        """Validate that a value is not None or empty."""
        if value is None:
            return False
        if isinstance(value, str) and not value.strip():
            return False
        if isinstance(value, (list, dict)) and not value:
            return False
        return True
    
    def _validate_type(self, value: Any, params: Dict[str, Any]) -> bool:
        """Validate that a value is of the expected type."""
        expected_type = params.get("type")
        if expected_type is None:
            return True
        
        if isinstance(expected_type, type):
            return isinstance(value, expected_type)
        elif isinstance(expected_type, (list, tuple)):
            return any(isinstance(value, t) for t in expected_type)
        else:
            return False
    
    def _validate_range(self, value: Any, params: Dict[str, Any]) -> bool:
        """Validate that a numeric value is within a range."""
        if not isinstance(value, (int, float)):
            return False
        
        min_val = params.get("min")
        max_val = params.get("max")
        
        if min_val is not None and value < min_val:
            return False
        if max_val is not None and value > max_val:
            return False
        
        return True
    
    def _validate_length(self, value: Any, params: Dict[str, Any]) -> bool:
        """Validate the length of a string, list, or dict."""
        if value is None:
            return False
        
        if isinstance(value, str):
            length = len(value)
        elif isinstance(value, (list, dict)):
            length = len(value)
        else:
            return False
        
        min_len = params.get("min")
        max_len = params.get("max")
        
        if min_len is not None and length < min_len:
            return False
        if max_len is not None and length > max_len:
            return False
        
        return True
    
    def _validate_pattern(self, value: Any, params: Dict[str, Any]) -> bool:
        """Validate a string against a regex pattern."""
        import re
        
        if not isinstance(value, str):
            return False
        
        pattern = params.get("pattern")
        if pattern is None:
            return True
        
        try:
            return bool(re.match(pattern, value))
        except re.error:
            return False
    
    def _validate_custom(self, value: Any, params: Dict[str, Any]) -> bool:
        """Validate using a custom validator function."""
        validator_name = params.get("validator")
        if validator_name is None:
            return True
        
        if validator_name not in self._custom_validators:
            return False
        
        try:
            return self._custom_validators[validator_name](value, params)
        except Exception:
            return False


# Global validator instance
validator = Validator()


# Common validation rules
def add_common_rules() -> None:
    """Add common validation rules to the global validator."""
    
    # Node name validation
    validator.add_rule("node_name", ValidationRule(
        ValidationType.REQUIRED,
        "Node name is required",
        {}
    ))
    validator.add_rule("node_name", ValidationRule(
        ValidationType.LENGTH,
        "Node name must be between 1 and 50 characters",
        {"min": 1, "max": 50}
    ))
    
    # Position validation
    validator.add_rule("position_x", ValidationRule(
        ValidationType.RANGE,
        "X position must be between -10000 and 10000",
        {"min": -10000, "max": 10000}
    ))
    validator.add_rule("position_y", ValidationRule(
        ValidationType.RANGE,
        "Y position must be between -10000 and 10000",
        {"min": -10000, "max": 10000}
    ))
    
    # Pin value validation
    validator.add_rule("pin_value", ValidationRule(
        ValidationType.TYPE,
        "Pin value must be a valid type",
        {"type": (int, float, str, bool, list, dict)}
    ))
    
    # File path validation
    validator.add_rule("file_path", ValidationRule(
        ValidationType.REQUIRED,
        "File path is required",
        {}
    ))
    validator.add_rule("file_path", ValidationRule(
        ValidationType.PATTERN,
        "File path must be a valid path",
        {"pattern": r"^[a-zA-Z]:\\.*|^/.*|^\./.*"}
    ))


# Initialize common rules
add_common_rules()


def validate_node_data(data: Dict[str, Any]) -> List[ValidationError]:
    """
    Validate node creation data.
    
    Args:
        data: Node data to validate
        
    Returns:
        List of validation errors
    """
    return validator.validate(data)


def validate_pin_value(value: Any, pin_type: str) -> List[ValidationError]:
    """
    Validate a pin value based on its type.
    
    Args:
        value: Value to validate
        pin_type: Type of the pin
        
    Returns:
        List of validation errors
    """
    if pin_type == "int":
        return validator.validate_field("pin_value", value)
    elif pin_type == "float":
        return validator.validate_field("pin_value", value)
    elif pin_type == "string":
        return validator.validate_field("pin_value", value)
    elif pin_type == "bool":
        return validator.validate_field("pin_value", value)
    else:
        return validator.validate_field("pin_value", value)


def validate_file_path(file_path: str) -> List[ValidationError]:
    """
    Validate a file path.
    
    Args:
        file_path: Path to validate
        
    Returns:
        List of validation errors
    """
    return validator.validate_field("file_path", file_path) 