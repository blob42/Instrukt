## 
##  Copyright (c) 2023 Chakib Ben Ziane <contact@blob42.xyz>. All rights reserved.
## 
##  SPDX-License-Identifier: AGPL-3.0-or-later
## 
##  This file is part of Instrukt.
## 
##  This program is free software: you can redistribute it and/or modify it under
##  the terms of the GNU Affero General Public License as published by the Free
##  Software Foundation, either version 3 of the License, or (at your option) any
##  later version.
## 
##  This program is distributed in the hope that it will be useful, but WITHOUT
##  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
##  FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
##  details.
## 
##  You should have received a copy of the GNU Affero General Public License along
##  with this program.  If not, see <http://www.gnu.org/licenses/>.
## 
"""Command history management."""
import datetime
import os
from collections import deque
from typing import Any, List, Optional

from pydantic import BaseModel, Field, PrivateAttr
from pydantic_yaml import YamlModelMixin

from ..config import Settings


class HistEntry(YamlModelMixin, BaseModel):
    """Represents a history entry."""

    entry: str
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)


class CommandHistory(YamlModelMixin, BaseModel):
    max_size: int = Field(500, exclude=True)
    config: Settings = Field(default=Settings, exclude=True)
    _history: deque[HistEntry] = PrivateAttr()
    history: Optional[List[HistEntry]] = Field(None) # exported to hist file
    _current_index: int = PrivateAttr(0)

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._history = deque(maxlen=self.max_size)


    def add(self, command: str) -> None:
        """Add a command to the history."""
        self._history.append(HistEntry(entry=command))
        self._current_index = len(self._history)

    def get(self, index: int) -> HistEntry:
        """Get a command from the history."""
        if len(self._history) == 0:
            return ""
        return self._history[index]

    def load(self) -> None:
        """Restore command history"""
        path = self.config.history_file
        assert path.endswith(".yaml")
        if os.path.exists(path):
            new_hist = self.parse_file(path)
            self.clear()
            self._history = deque(sorted(new_hist.history, key=lambda x: x.timestamp),
                                  maxlen=self.max_size)
            self._current_index = len(self._history)


        # order by timestamp
        self._history = deque(sorted(self._history, key=lambda x: x.timestamp),
                              maxlen=self.max_size)
        self._current_index = len(self._history)

    def save(self) -> None:
        """Store command history in yaml format"""
        self.history = list(self._history)
        path = self.config.history_file 
        assert path.endswith(".yaml")
        with open(path, 'w') as f:
            f.write(self.yaml())

    # TEST: should get the last command
    def get_previous(self) -> HistEntry:
        """Get the previous command from the history."""
        if self._current_index > 0:
            self._current_index -= 1
        return self.get(self._current_index)

    def get_next(self) -> HistEntry:
        """Get the next command from the history.

        Return empty string if the current command is the last one."""
        if self._current_index < len(self._history):
            self._current_index += 1

        if self._current_index == len(self._history):
            self._current_index -= 1
            return self.get(self._current_index)

        return self.get(self._current_index)

    def get_match(self, prefix: str) -> HistEntry:
        """Get the most recent command that matches the prefix."""
        for command in reversed(self._history):
            if command.entry.startswith(prefix):
                return command
        return ""

    def clear(self) -> None:
        """Clears the history."""
        self._history.clear()
        self._current_index = 0

    def __len__(self) -> int:
        """Return the number of commands in the history."""
        return len(self._history)

    def __iter__(self) -> Any:
        """Return an iterator over the history."""
        return iter(self._history)

    def __getitem__(self, index: int) -> HistEntry:
        """Get a command from the history."""
        return self.get(index)

    def __setitem__(self, index: int, command: HistEntry):
        """Set a command in the history."""
        self._history[index] = command

    def __delitem__(self, index: int) -> None:
        """Delete a command from the history."""
        del self._history[index]

    def __repr__(self) -> str:
        """Return a string representation of the history."""
        return repr(self._history)

    def __str__(self) -> str:
        """Return a string representation of the history."""
