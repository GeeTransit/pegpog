"""Provides exceptions for various uses"""

from dataclasses import dataclass

__all__ = ["ParseError", "ParseFailure", "EOFFailure", "UnexpectedChar"]

class ParseError(Exception):
    """Cannot be backtracked from"""
    pass

class ParseFailure(ParseError):
    """Can be backtracked from"""
    pass

class EOFFailure(ParseFailure):
    """Raised when trying to access beyond end of input string"""
    pass

@dataclass
class UnexpectedChar(ParseFailure):
    """Raised on an unexpected character"""
    pos: int = -1
    expected: str = ""
    actual: str = ""
