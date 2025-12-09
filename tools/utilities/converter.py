"""NEXUS AI Agent - Unit Converter"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ConversionResult:
    """Conversion result"""
    value: float
    from_unit: str
    to_unit: str
    result: float
    formula: str


class Converter:
    """Unit conversion tool"""

    def __init__(self):
        # Length conversions (base: meters)
        self._length = {
            'mm': 0.001,
            'cm': 0.01,
            'm': 1.0,
            'km': 1000.0,
            'in': 0.0254,
            'ft': 0.3048,
            'yd': 0.9144,
            'mi': 1609.34,
            'nm': 1852.0,  # nautical mile
        }

        # Weight conversions (base: grams)
        self._weight = {
            'mg': 0.001,
            'g': 1.0,
            'kg': 1000.0,
            't': 1000000.0,  # metric ton
            'oz': 28.3495,
            'lb': 453.592,
            'st': 6350.29,  # stone
        }

        # Volume conversions (base: liters)
        self._volume = {
            'ml': 0.001,
            'l': 1.0,
            'gal': 3.78541,  # US gallon
            'qt': 0.946353,  # US quart
            'pt': 0.473176,  # US pint
            'cup': 0.236588,
            'fl_oz': 0.0295735,  # US fluid ounce
            'm3': 1000.0,
        }

        # Area conversions (base: square meters)
        self._area = {
            'mm2': 0.000001,
            'cm2': 0.0001,
            'm2': 1.0,
            'km2': 1000000.0,
            'ha': 10000.0,  # hectare
            'in2': 0.00064516,
            'ft2': 0.092903,
            'yd2': 0.836127,
            'ac': 4046.86,  # acre
            'mi2': 2590000.0,
        }

        # Speed conversions (base: m/s)
        self._speed = {
            'm/s': 1.0,
            'km/h': 0.277778,
            'mph': 0.44704,
            'kn': 0.514444,  # knots
            'ft/s': 0.3048,
        }

        # Time conversions (base: seconds)
        self._time = {
            'ms': 0.001,
            's': 1.0,
            'min': 60.0,
            'h': 3600.0,
            'd': 86400.0,
            'wk': 604800.0,
            'mo': 2629746.0,  # average month
            'yr': 31556952.0,  # average year
        }

        # Data size conversions (base: bytes)
        self._data = {
            'b': 1,
            'kb': 1024,
            'mb': 1024 ** 2,
            'gb': 1024 ** 3,
            'tb': 1024 ** 4,
            'pb': 1024 ** 5,
        }

        # Temperature (special handling)
        self._temperature_units = ['c', 'f', 'k']

        self._categories = {
            'length': self._length,
            'weight': self._weight,
            'volume': self._volume,
            'area': self._area,
            'speed': self._speed,
            'time': self._time,
            'data': self._data,
        }

    def convert(
        self,
        value: float,
        from_unit: str,
        to_unit: str
    ) -> ConversionResult:
        """
        Convert between units

        Args:
            value: Value to convert
            from_unit: Source unit
            to_unit: Target unit

        Returns:
            ConversionResult object
        """
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()

        # Handle temperature separately
        if from_unit in self._temperature_units or to_unit in self._temperature_units:
            result = self._convert_temperature(value, from_unit, to_unit)
            return ConversionResult(
                value=value,
                from_unit=from_unit,
                to_unit=to_unit,
                result=result,
                formula=f"Temperature conversion"
            )

        # Find category
        category = self._find_category(from_unit, to_unit)
        if not category:
            raise ValueError(f"Unknown units: {from_unit}, {to_unit}")

        units = self._categories[category]

        # Convert to base then to target
        base_value = value * units[from_unit]
        result = base_value / units[to_unit]

        return ConversionResult(
            value=value,
            from_unit=from_unit,
            to_unit=to_unit,
            result=result,
            formula=f"{value} {from_unit} × {units[from_unit]} / {units[to_unit]} = {result} {to_unit}"
        )

    def _find_category(self, from_unit: str, to_unit: str) -> Optional[str]:
        """Find category for units"""
        for category, units in self._categories.items():
            if from_unit in units and to_unit in units:
                return category
        return None

    def _convert_temperature(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert temperature"""
        # Convert to Celsius first
        if from_unit == 'c':
            celsius = value
        elif from_unit == 'f':
            celsius = (value - 32) * 5 / 9
        elif from_unit == 'k':
            celsius = value - 273.15
        else:
            raise ValueError(f"Unknown temperature unit: {from_unit}")

        # Convert from Celsius to target
        if to_unit == 'c':
            return celsius
        elif to_unit == 'f':
            return celsius * 9 / 5 + 32
        elif to_unit == 'k':
            return celsius + 273.15
        else:
            raise ValueError(f"Unknown temperature unit: {to_unit}")

    # Convenience methods
    def length(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert length"""
        return self.convert(value, from_unit, to_unit).result

    def weight(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert weight"""
        return self.convert(value, from_unit, to_unit).result

    def volume(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert volume"""
        return self.convert(value, from_unit, to_unit).result

    def area(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert area"""
        return self.convert(value, from_unit, to_unit).result

    def speed(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert speed"""
        return self.convert(value, from_unit, to_unit).result

    def time(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert time"""
        return self.convert(value, from_unit, to_unit).result

    def data_size(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert data size"""
        return self.convert(value, from_unit, to_unit).result

    def temperature(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert temperature"""
        return self._convert_temperature(value, from_unit.lower(), to_unit.lower())

    def get_available_units(self, category: str) -> list:
        """Get available units for category"""
        if category.lower() == 'temperature':
            return self._temperature_units
        return list(self._categories.get(category.lower(), {}).keys())

    def get_categories(self) -> list:
        """Get available categories"""
        return list(self._categories.keys()) + ['temperature']

    # Number base conversions
    def decimal_to_binary(self, value: int) -> str:
        """Convert decimal to binary"""
        return bin(value)[2:]

    def binary_to_decimal(self, value: str) -> int:
        """Convert binary to decimal"""
        return int(value, 2)

    def decimal_to_hex(self, value: int) -> str:
        """Convert decimal to hexadecimal"""
        return hex(value)[2:].upper()

    def hex_to_decimal(self, value: str) -> int:
        """Convert hexadecimal to decimal"""
        return int(value, 16)

    def decimal_to_octal(self, value: int) -> str:
        """Convert decimal to octal"""
        return oct(value)[2:]

    def octal_to_decimal(self, value: str) -> int:
        """Convert octal to decimal"""
        return int(value, 8)

