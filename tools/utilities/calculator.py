"""NEXUS AI Agent - Calculator Tool"""

import math
import re
from typing import Union, Dict, Any, Optional, List


class Calculator:
    """Mathematical calculations"""

    def __init__(self):
        self._variables: Dict[str, float] = {}
        self._history: List[str] = []

        # Safe math functions
        self._functions = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'asin': math.asin,
            'acos': math.acos,
            'atan': math.atan,
            'sinh': math.sinh,
            'cosh': math.cosh,
            'tanh': math.tanh,
            'sqrt': math.sqrt,
            'log': math.log,
            'log10': math.log10,
            'log2': math.log2,
            'exp': math.exp,
            'abs': abs,
            'ceil': math.ceil,
            'floor': math.floor,
            'round': round,
            'factorial': math.factorial,
            'degrees': math.degrees,
            'radians': math.radians,
        }

        # Constants
        self._constants = {
            'pi': math.pi,
            'e': math.e,
            'tau': math.tau,
            'inf': math.inf,
        }

    def evaluate(self, expression: str) -> Union[float, str]:
        """
        Evaluate mathematical expression

        Args:
            expression: Math expression string

        Returns:
            Calculated result or error message
        """
        try:
            # Store original expression
            self._history.append(expression)

            # Clean expression
            expr = expression.strip()

            # Replace constants
            for name, value in self._constants.items():
                expr = re.sub(rf'\b{name}\b', str(value), expr, flags=re.IGNORECASE)

            # Replace variables
            for name, value in self._variables.items():
                expr = re.sub(rf'\b{name}\b', str(value), expr)

            # Replace ^ with **
            expr = expr.replace('^', '**')

            # Create safe namespace
            namespace = {
                '__builtins__': {},
                **self._functions
            }

            # Evaluate
            result = eval(expr, namespace)

            return float(result) if isinstance(result, (int, float)) else result

        except ZeroDivisionError:
            return "Error: Division by zero"
        except ValueError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Error: Invalid expression - {str(e)}"

    def set_variable(self, name: str, value: float) -> None:
        """Set a variable"""
        self._variables[name] = value

    def get_variable(self, name: str) -> Optional[float]:
        """Get a variable value"""
        return self._variables.get(name)

    def clear_variables(self) -> None:
        """Clear all variables"""
        self._variables.clear()

    def get_history(self) -> List[str]:
        """Get calculation history"""
        return self._history.copy()

    def clear_history(self) -> None:
        """Clear history"""
        self._history.clear()

    # Basic operations
    def add(self, a: float, b: float) -> float:
        """Add two numbers"""
        return a + b

    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a"""
        return a - b

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers"""
        return a * b

    def divide(self, a: float, b: float) -> float:
        """Divide a by b"""
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return a / b

    def power(self, base: float, exponent: float) -> float:
        """Raise base to exponent"""
        return base ** exponent

    def modulo(self, a: float, b: float) -> float:
        """Get remainder of a divided by b"""
        return a % b

    # Advanced operations
    def percentage(self, value: float, percent: float) -> float:
        """Calculate percentage of value"""
        return value * (percent / 100)

    def percent_change(self, old_value: float, new_value: float) -> float:
        """Calculate percent change"""
        if old_value == 0:
            return float('inf') if new_value > 0 else float('-inf')
        return ((new_value - old_value) / old_value) * 100

    def average(self, numbers: List[float]) -> float:
        """Calculate average"""
        if not numbers:
            return 0
        return sum(numbers) / len(numbers)

    def sum_numbers(self, numbers: List[float]) -> float:
        """Sum numbers"""
        return sum(numbers)

    def product(self, numbers: List[float]) -> float:
        """Product of numbers"""
        result = 1
        for n in numbers:
            result *= n
        return result

    def gcd(self, a: int, b: int) -> int:
        """Greatest common divisor"""
        return math.gcd(int(a), int(b))

    def lcm(self, a: int, b: int) -> int:
        """Least common multiple"""
        return abs(int(a) * int(b)) // math.gcd(int(a), int(b))

    # Trigonometry (angles in degrees)
    def sin_deg(self, angle: float) -> float:
        """Sine (degrees)"""
        return math.sin(math.radians(angle))

    def cos_deg(self, angle: float) -> float:
        """Cosine (degrees)"""
        return math.cos(math.radians(angle))

    def tan_deg(self, angle: float) -> float:
        """Tangent (degrees)"""
        return math.tan(math.radians(angle))

    # Financial calculations
    def simple_interest(
        self,
        principal: float,
        rate: float,
        time: float
    ) -> float:
        """Calculate simple interest"""
        return principal * (rate / 100) * time

    def compound_interest(
        self,
        principal: float,
        rate: float,
        time: float,
        n: int = 12
    ) -> float:
        """
        Calculate compound interest

        Args:
            principal: Initial amount
            rate: Annual interest rate (percentage)
            time: Time in years
            n: Compounding frequency per year

        Returns:
            Final amount
        """
        return principal * (1 + (rate / 100) / n) ** (n * time)

    def loan_payment(
        self,
        principal: float,
        annual_rate: float,
        months: int
    ) -> float:
        """
        Calculate monthly loan payment

        Args:
            principal: Loan amount
            annual_rate: Annual interest rate (percentage)
            months: Loan term in months

        Returns:
            Monthly payment
        """
        if annual_rate == 0:
            return principal / months

        monthly_rate = (annual_rate / 100) / 12
        payment = principal * (monthly_rate * (1 + monthly_rate) ** months) / \
                  ((1 + monthly_rate) ** months - 1)
        return payment

    # Unit conversions within calculator
    def celsius_to_fahrenheit(self, celsius: float) -> float:
        """Convert Celsius to Fahrenheit"""
        return (celsius * 9/5) + 32

    def fahrenheit_to_celsius(self, fahrenheit: float) -> float:
        """Convert Fahrenheit to Celsius"""
        return (fahrenheit - 32) * 5/9

    def km_to_miles(self, km: float) -> float:
        """Convert kilometers to miles"""
        return km * 0.621371

    def miles_to_km(self, miles: float) -> float:
        """Convert miles to kilometers"""
        return miles * 1.60934

