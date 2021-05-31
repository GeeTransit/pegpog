"""Provides a joined strings class"""

from dataclasses import dataclass, field

__all__ = ["JoinedStrings"]

@dataclass
class JoinedStrings:
    """This wraps multiple strings and allows indexing them as a single string

    This class provides an .append method to grow the string.

    """
    strings: list[str] = field(default_factory=list)

    def append(self, string):
        """Add string to the back of the joined string"""
        self.strings.append(string)

    def __getitem__(self, index):
        original_index = index
        if index < 0:
            index += len(self)
        for string in self.strings:
            if index < len(string):
                return string[index]
            index -= len(string)
        raise IndexError(original_index)

    def __len__(self):
        return sum(map(len, self.strings))
