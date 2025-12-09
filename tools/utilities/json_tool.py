"""NEXUS AI Agent - JSON Tool"""

import json
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass


@dataclass
class JSONValidationResult:
    """JSON validation result"""
    valid: bool
    error: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None


class JSONTool:
    """JSON manipulation utilities"""

    def parse(self, json_string: str) -> Any:
        """
        Parse JSON string

        Args:
            json_string: JSON string to parse

        Returns:
            Parsed Python object
        """
        return json.loads(json_string)

    def stringify(
        self,
        obj: Any,
        indent: Optional[int] = 2,
        sort_keys: bool = False
    ) -> str:
        """
        Convert object to JSON string

        Args:
            obj: Object to convert
            indent: Indentation level
            sort_keys: Sort object keys

        Returns:
            JSON string
        """
        return json.dumps(obj, indent=indent, sort_keys=sort_keys, ensure_ascii=False)

    def validate(self, json_string: str) -> JSONValidationResult:
        """
        Validate JSON string

        Args:
            json_string: JSON string to validate

        Returns:
            JSONValidationResult
        """
        try:
            json.loads(json_string)
            return JSONValidationResult(valid=True)
        except json.JSONDecodeError as e:
            return JSONValidationResult(
                valid=False,
                error=str(e),
                line=e.lineno,
                column=e.colno
            )

    def get_value(
        self,
        obj: Dict[str, Any],
        path: str,
        default: Any = None
    ) -> Any:
        """
        Get value at path using dot notation

        Args:
            obj: JSON object
            path: Dot-separated path (e.g., "user.address.city")
            default: Default value if not found

        Returns:
            Value at path or default
        """
        keys = path.split('.')
        current = obj

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            elif isinstance(current, list):
                try:
                    index = int(key)
                    current = current[index]
                except (ValueError, IndexError):
                    return default
            else:
                return default

        return current

    def set_value(
        self,
        obj: Dict[str, Any],
        path: str,
        value: Any
    ) -> Dict[str, Any]:
        """
        Set value at path

        Args:
            obj: JSON object
            path: Dot-separated path
            value: Value to set

        Returns:
            Modified object
        """
        keys = path.split('.')
        current = obj

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value
        return obj

    def delete_key(self, obj: Dict[str, Any], path: str) -> Dict[str, Any]:
        """
        Delete key at path

        Args:
            obj: JSON object
            path: Dot-separated path

        Returns:
            Modified object
        """
        keys = path.split('.')
        current = obj

        for key in keys[:-1]:
            if key not in current:
                return obj
            current = current[key]

        if keys[-1] in current:
            del current[keys[-1]]

        return obj

    def merge(
        self,
        obj1: Dict[str, Any],
        obj2: Dict[str, Any],
        deep: bool = True
    ) -> Dict[str, Any]:
        """
        Merge two JSON objects

        Args:
            obj1: First object
            obj2: Second object (takes precedence)
            deep: Deep merge nested objects

        Returns:
            Merged object
        """
        result = obj1.copy()

        for key, value in obj2.items():
            if deep and key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge(result[key], value, deep=True)
            else:
                result[key] = value

        return result

    def diff(
        self,
        obj1: Dict[str, Any],
        obj2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get difference between two objects

        Args:
            obj1: First object
            obj2: Second object

        Returns:
            Dict with added, removed, and changed keys
        """
        diff = {
            "added": {},
            "removed": {},
            "changed": {}
        }

        all_keys = set(obj1.keys()) | set(obj2.keys())

        for key in all_keys:
            if key not in obj1:
                diff["added"][key] = obj2[key]
            elif key not in obj2:
                diff["removed"][key] = obj1[key]
            elif obj1[key] != obj2[key]:
                diff["changed"][key] = {
                    "old": obj1[key],
                    "new": obj2[key]
                }

        return diff

    def flatten(
        self,
        obj: Dict[str, Any],
        separator: str = "."
    ) -> Dict[str, Any]:
        """
        Flatten nested object

        Args:
            obj: Object to flatten
            separator: Key separator

        Returns:
            Flattened object
        """
        result = {}

        def _flatten(current: Any, prefix: str = ""):
            if isinstance(current, dict):
                for key, value in current.items():
                    new_key = f"{prefix}{separator}{key}" if prefix else key
                    _flatten(value, new_key)
            elif isinstance(current, list):
                for i, item in enumerate(current):
                    new_key = f"{prefix}{separator}{i}" if prefix else str(i)
                    _flatten(item, new_key)
            else:
                result[prefix] = current

        _flatten(obj)
        return result

    def unflatten(
        self,
        obj: Dict[str, Any],
        separator: str = "."
    ) -> Dict[str, Any]:
        """
        Unflatten object

        Args:
            obj: Flattened object
            separator: Key separator

        Returns:
            Nested object
        """
        result: Dict[str, Any] = {}

        for key, value in obj.items():
            parts = key.split(separator)
            current = result

            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            current[parts[-1]] = value

        return result

    def query(
        self,
        obj: Union[Dict, List],
        path: str
    ) -> List[Any]:
        """
        Query JSON using simple path expressions

        Supports:
        - Dot notation: user.name
        - Array index: items[0]
        - Wildcard: items[*].name

        Args:
            obj: JSON object/array
            path: Query path

        Returns:
            List of matching values
        """
        import re

        results = [obj]

        # Parse path into parts
        parts = re.findall(r'([^\.\[\]]+)|\[(\d+|\*)\]', path)

        for part in parts:
            key = part[0] or part[1]
            new_results = []

            for item in results:
                if key == '*':
                    if isinstance(item, list):
                        new_results.extend(item)
                    elif isinstance(item, dict):
                        new_results.extend(item.values())
                elif key.isdigit():
                    index = int(key)
                    if isinstance(item, list) and index < len(item):
                        new_results.append(item[index])
                else:
                    if isinstance(item, dict) and key in item:
                        new_results.append(item[key])

            results = new_results

        return results

    def schema(self, obj: Any) -> Dict[str, Any]:
        """
        Generate simple schema from object

        Args:
            obj: JSON object

        Returns:
            Schema dict
        """
        def get_type(value: Any) -> str:
            if value is None:
                return "null"
            elif isinstance(value, bool):
                return "boolean"
            elif isinstance(value, int):
                return "integer"
            elif isinstance(value, float):
                return "number"
            elif isinstance(value, str):
                return "string"
            elif isinstance(value, list):
                return "array"
            elif isinstance(value, dict):
                return "object"
            return "unknown"

        def build_schema(value: Any) -> Dict[str, Any]:
            type_name = get_type(value)
            schema: Dict[str, Any] = {"type": type_name}

            if type_name == "object" and value:
                schema["properties"] = {}
                for k, v in value.items():
                    schema["properties"][k] = build_schema(v)

            elif type_name == "array" and value:
                schema["items"] = build_schema(value[0])

            return schema

        return build_schema(obj)

