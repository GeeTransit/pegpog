"""Provides a grammar class that holds rules

    >>> grammar = Grammar("ab", {"ab": OneOrMore(ExpectChoice("ab"))})
    >>> grammar.parse("abbab")
    ('a', 'b', 'b', 'a', 'b')

"""
from typing import Optional

from dataclasses import dataclass, field

from .parser import Parser
from .rule import Rule

__all__ = ["Grammar"]

@dataclass
class Grammar:
    """Simplifies some common use cases with parsers"""
    rules: dict[str, Rule] = field(default_factory=dict)
    start: Optional[str] = None

    @classmethod
    def from_single(cls, rule):
        return cls(start="start", rules={"start": rule})

    def __str__(self):
        return "\n".join(
            f"{name} <- {rule}"
            for name, rule in self.rules.items()
        )

    def create_parser(self, *, start: Optional[str] = None) -> Parser:
        """Create a parser with own rules"""
        if start is None:
            start = self.start
        if start is None:
            raise ValueError("start rule is None")
        return Parser(start, self.rules)

    def parse(self, string: str, *, start: Optional[str] = None) -> list:
        """Fully parses the string and returns the result

        Note that the result may not match the whole string if the rule
        does not end with a !()

        """
        parser = self.create_parser(start=start)
        parser.add(string)
        return parser.step(eof=True)
