"""Provides rules that can be combined to create more complex rules

These rules also have readable string representations that can be turned back
into objects using the peg module's create_rule function.

    >>> rule = OneOrMore(ExpectChoice("ab"))
    >>> print(rule)
    'ab'+

"""
from typing import ClassVar, Container

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .errors import *

__all__ = [
    "Join", "Choice", "Error", "Positive", "Negative", "Ignore", "Fuse",
    "Repeat", "ZeroOrMore", "OneOrMore", "Optional", "Pack", "Empty", "Expect",
    "ExpectChoice", "ExpectJoin", "Inject", "Any", "Reference",
]

# Abstract class for rules
class Rule(ABC):
    """Abstract class for rules

    A rule should be callable with one argument - the parser.

    The precedence class variable signifies whether the rule should be wrapped
    in parentheses in their string representation. A larger number means a
    higher precedence and vice versa. Using an example, addition could have
    a precedence of 1 whereas multiplication has a precedence of 2.

    """
    precedence: ClassVar[int] = -1

    @abstractmethod
    def __call__(self, parser):
        raise NotImplementedError

    def _wrap(self, other):
        """Wraps other in parentheses if it has a lower precedence than own"""
        if not hasattr(other, "precedence"):
            return f"{other!r}"
        if other.precedence >= self.precedence:
            return f"{other}"
        return f"({other})"

@dataclass(frozen=True)
class Choice(Rule):
    """Returns the result of the first rule that succeeds"""
    precedence: ClassVar[int] = 1
    rules: tuple[Rule]

    def __init__(self, *rules):
        if not rules:
            raise ValueError("rules cannot be empty")
        if len(rules) < 2:
            raise ValueError("at least two rules required")
        object.__setattr__(self, "rules", rules)

    def __repr__(self):
        return f"{type(self).__name__}({', '.join(map(repr, self.rules))})"

    def __str__(self):
        return " | ".join(map(self._wrap, self.rules))

    async def __call__(self, parser):
        for i, rule in enumerate(self.rules):
            try:
                return await rule(parser)
            except ParseFailure:
                if i == len(self.rules)-1:
                    raise

@dataclass(frozen=True)
class Join(Rule):
    """Returns the joined results of all rules"""
    precedence: ClassVar[int] = 2
    rules: tuple[Rule]

    def __init__(self, *rules):
        if not rules:
            raise ValueError("rules cannot be empty")
        if len(rules) < 2:
            raise ValueError("at least two rules required")
        object.__setattr__(self, "rules", rules)

    def __repr__(self):
        return f"{type(self).__name__}({', '.join(map(repr, self.rules))})"

    def __str__(self):
        return " ".join(map(self._wrap, self.rules))

    async def __call__(self, parser):
        old = parser.pos
        result = []
        try:
            for rule in self.rules:
                result += await rule(parser)
        except ParseFailure:
            parser.pos = old
            raise
        else:
            return tuple(result)

@dataclass(frozen=True)
class Error(Rule):
    """Raises a ParseError with a message"""
    precedence: ClassVar[int] = 3
    message: str

    def __repr__(self):
        return f"{type(self).__name__}({self.message!r})"

    def __str__(self):
        return f"^{self.message!r}"

    async def __call__(self, parser):
        raise ParseError(self.message)

@dataclass(frozen=True)
class Positive(Rule):
    """Ensures the rule matches and resets the parser's position"""
    precedence: ClassVar[int] = 4
    rule: Rule

    def __repr__(self):
        return f"{type(self).__name__}({self.rule!r})"

    def __str__(self):
        return f"&{self._wrap(self.rule)}"

    async def __call__(self, parser):
        old = parser.pos
        try:
            await self.rule(parser)
        except ParseFailure:
            raise
        else:
            return ()
        finally:
            parser.pos = old

@dataclass(frozen=True)
class Negative(Rule):
    """Ensures the rule doesn't matches and resets the parser's position"""
    precedence: ClassVar[int] = 4
    rule: Rule

    def __repr__(self):
        return f"{type(self).__name__}({self.rule!r})"

    def __str__(self):
        return f"!{self._wrap(self.rule)}"

    async def __call__(self, parser):
        old = parser.pos
        try:
            await self.rule(parser)
        except ParseFailure:
            return ()
        else:
            raise ParseFailure(self.rule)
        finally:
            parser.pos = old

@dataclass(frozen=True)
class Ignore(Rule):
    """Returns an empty tuple instead of the rule's result"""
    precedence: ClassVar[int] = 4
    rule: Rule

    def __repr__(self):
        return f"{type(self).__name__}({self.rule!r})"

    def __str__(self):
        return f":{self._wrap(self.rule)}"

    async def __call__(self, parser):
        await self.rule(parser)
        return ()

@dataclass(frozen=True)
class Fuse(Rule):
    """Flattens the rule's result and returns a single joined string"""
    precedence: ClassVar[int] = 4
    rule: Rule

    def __repr__(self):
        return f"{type(self).__name__}({self.rule!r})"

    def __str__(self):
        return f"~{self._wrap(self.rule)}"

    async def __call__(self, parser):
        value = await self.rule(parser)
        stack = [iter(value)]
        flattened = []
        while stack:
            try:
                element = next(stack[-1])
            except StopIteration:
                stack.pop()
                continue
            if isinstance(element, str):
                flattened.append(element)
                continue
            stack.append(iter(element))
        return ("".join(flattened),)

@dataclass(frozen=True)
class Repeat(Rule):
    """Tries matching the rule greedily"""
    precedence: ClassVar[int] = 5
    rule: Rule

    def __repr__(self):
        return f"{type(self).__name__}({self.rule!r})"

    def __str__(self):
        return f"{self._wrap(self.rule)}*"

    async def __call__(self, parser):
        result = []
        while True:
            old = parser.pos
            try:
                value = await self.rule(parser)
                result += value
            except ParseFailure:
                parser.pos = old
                break
        return tuple(result)
ZeroOrMore = Repeat

@dataclass(frozen=True)
class OneOrMore(Rule):
    """Tries matching the rule greedily and at least once"""
    precedence: ClassVar[int] = 5
    rule: Rule

    def __repr__(self):
        return f"{type(self).__name__}({self.rule!r})"

    def __str__(self):
        return f"{self._wrap(self.rule)}+"

    async def __call__(self, parser):
        value = await self.rule(parser)
        result = [*value]
        while True:
            old = parser.pos
            try:
                value = await self.rule(parser)
                result += value
            except ParseFailure:
                parser.pos = old
                break
        return tuple(result)

@dataclass(frozen=True)
class Optional(Rule):
    """Matches the rule or an empty string"""
    precedence: ClassVar[int] = 5
    rule: Rule

    def __repr__(self):
        return f"{type(self).__name__}({self.rule!r})"

    def __str__(self):
        return f"{self._wrap(self.rule)}?"

    async def __call__(self, parser):
        old = parser.pos
        try:
            return await self.rule(parser)
        except ParseFailure:
            parser.pos = old
            return ()

@dataclass(frozen=True)
class Pack(Rule):
    """Returns a one-tuple with the rule's result"""
    precedence: ClassVar[int] = 6
    rule: Rule

    def __repr__(self):
        return f"{type(self).__name__}({self.rule!r})"

    def __str__(self):
        return f"{{ {self.rule} }}"

    async def __call__(self, parser):
        return (await self.rule(parser),)

@dataclass(frozen=True)
class Empty(Rule):
    """Returns a one-tuple"""
    precedence: ClassVar[int] = 6

    def __str__(self):
        return "()"

    async def __call__(self, parser):
        return ()

@dataclass(frozen=True)
class Expect(Rule):
    """Matches a single character"""
    precedence: ClassVar[int] = 6
    char: str

    def __repr__(self):
        return f"{type(self).__name__}({self.char!r})"

    def __str__(self):
        string = repr(self.char)[1:-1]
        string = string.replace('"', '\\"').replace("\\'", "'")
        return f'"{string}"'

    async def __call__(self, parser):
        actual = await parser.get()
        if actual != self.char:
            raise UnexpectedChar(parser.pos, self.char, actual)
        parser.pos += 1
        return (actual,)

@dataclass(frozen=True)
class ExpectChoice(Rule):
    """Matches any of the characters given"""
    precedence: ClassVar[int] = 6
    chars: str
    char_set: Container[str] = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "char_set", frozenset(self.chars))

    def __repr__(self):
        return f"{type(self).__name__}({self.chars!r})"

    def __str__(self):
        string = repr(self.chars)[1:-1]
        string = string.replace("'", "\\'").replace('\\"', '"')
        return f"'{string}'"

    async def __call__(self, parser):
        actual = await parser.get()
        if actual not in self.char_set:
            raise UnexpectedChar(parser.pos, self.chars, actual)
        parser.pos += 1
        return (actual,)

@dataclass(frozen=True)
class ExpectJoin(Rule):
    """Matches all of the characters given"""
    precedence: ClassVar[int] = 6
    chars: str

    def __repr__(self):
        return f"{type(self).__name__}({self.chars!r})"

    def __str__(self):
        string = repr(self.chars)[1:-1]
        string = string.replace('"', '\\"').replace("\\'", "'")
        return f'"{string}"'

    async def __call__(self, parser):
        old = parser.pos
        for char in self.chars:
            actual = await parser.get()
            if actual != char:
                break
            parser.pos += 1
        else:
            return (self.chars,)
        pos = parser.pos
        parser.pos = old
        raise UnexpectedChar(pos, char, actual)

@dataclass(frozen=True)
class Inject(Rule):
    """Returns the given string"""
    precedence: ClassVar[int] = 6
    string: str

    def __repr__(self):
        return f"{type(self).__name__}({self.string!r})"

    def __str__(self):
        string = repr(self.string)[1:-1]
        string = string.replace("\\'", "'").replace('\\"', '"')
        return f'`{string}`'

    async def __call__(self, parser):
        return (self.string,)

@dataclass(frozen=True)
class Any(Rule):
    """Matches a single character"""
    precedence: ClassVar[int] = 6

    def __str__(self):
        return "."

    async def __call__(self, parser):
        char = await parser.get()
        parser.pos += 1
        return (char,)

@dataclass(frozen=True)
class Reference(Rule):
    """Returns the result of the rule with the given name"""
    precedence: ClassVar[int] = 6
    name: str

    def __repr__(self):
        return f"{type(self).__name__}({self.name!r})"

    def __str__(self):
        return self.name

    async def __call__(self, parser):
        if (self.name, parser.pos) not in parser.saved:
            rule = parser.rules[self.name]
            old = parser.pos
            try:
                value = await rule(parser)
            except ParseFailure as e:
                parser.saved[self.name, old] = e, None
            else:
                parser.saved[self.name, old] = value, parser.pos
            finally:
                parser.pos = old
        value, pos = parser.saved[self.name, parser.pos]
        if pos is None:
            raise ParseFailure(self.name) from value
        parser.pos = pos
        return value
