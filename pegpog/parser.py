"""Provides the resumable parser class

    >>> parser = Parser("ab", {"ab": OneOrMore(ExpectChoice("ab"))})
    >>> parser.add("ab")
    >>> parser.step()
    >>> parser.add("bab")
    >>> parser.step()
    >>> parser.step(eof=True)
    ('a', 'b', 'b', 'a', 'b')

"""
from typing import Optional, Callable
from collections.abc import Coroutine

from dataclasses import dataclass, field
from types import coroutine

from .util import JoinedStrings
from .rule import Reference
from .errors import *

__all__ = ["Parser"]

@dataclass
class Parser:
    """A resumable parser

    Strings can be added using the .add method. Parsing can be stepped forwards
    using the .step method.
    """
    start: Optional[str] = None
    rules: dict[str, Callable[[], Coroutine]] = field(default_factory=dict)
    strings: JoinedStrings = field(default_factory=JoinedStrings)
    pos: int = 0
    eof: bool = False
    saved: dict[tuple[str, int], tuple] = field(default_factory=dict)
    coro: Optional[Coroutine] = field(default=None, init=False)

    @staticmethod
    @coroutine
    def current_parser():
        """Returns the current parser"""
        return (yield "current_parser")

    @coroutine
    def more(self):
        """Waits for more input"""
        if self.eof:
            raise EOFFailure
        value = (yield "more")
        if isinstance(value, BaseException):
            raise value
        return value

    async def get(self):
        """Returns the char at the current position"""
        while True:
            try:
                return self.strings[self.pos]
            except IndexError:
                pass
            await self.more()

    def add(self, string):
        """Appends the string to the input"""
        if self.eof:
            raise ValueError("cannot add string to terminated parser")
        self.strings.append(string)

    def step(self, *, eof=False):
        """Steps the coroutine until it requires more input"""
        if self.eof:
            raise ValueError("cannot step on terminated parser")
        if self.coro is None:
            self.coro = Reference(self.start)(self)
            # self.coro = self.rules[self.start](self)
        if eof:
            self.eof = True
        send = None
        while True:
            try:
                action = self.coro.send(send)
            except StopIteration as e:
                self.coro = None
                return e.value
            if action == "more":
                if not eof:
                    return None
                send = EOFFailure()
            elif action == "current_parser":
                send = self
            else:
                raise ValueError(f"unknown action: {action}")
