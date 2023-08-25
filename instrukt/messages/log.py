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
"""textual custom messages."""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, TypeAlias, Union

from rich.console import RenderableType
from rich.panel import Panel
from textual.message import Message


class LogLevel(Enum):
    """Message log level."""
    INFO = auto()
    ERROR = auto()
    DEBUG = auto()
    WARNING = auto()
    TIP = auto()


MsgType: TypeAlias = Union[RenderableType, BaseException, str]


@dataclass
class LogMessage(Message, namespace="instrukt"):
    """Instrukt base message class."""
    msg: MsgType
    level: LogLevel

    def __rich__(self) -> Any:
        if self.level == LogLevel.ERROR:
            exception = self.msg.__class__.__name__
            return Panel(f"{self.msg}",
                         expand=False,
                         title=exception,
                         title_align="left",
                         border_style="color(13)")
        elif self.level == LogLevel.WARNING:
            return Panel(f"{self.msg}",
                         expand=False,
                         title="Warning",
                         title_align="left",
                         border_style="yellow")

        elif self.level == LogLevel.INFO:
            return Panel(f"{self.msg}",
                         expand=False,
                         title="Info",
                         title_align="left")
        elif self.level == LogLevel.TIP:
            return Panel(f"{self.msg}",
                         expand=False,
                         title="Tip",
                         title_align="left",
                         border_style="cyan")
        else:
            return Panel(f"{self.msg}",
                         expand=False,
                         title="Debug",
                         title_align="left",
                         border_style="magenta")

    @classmethod
    def info(cls, msg: MsgType) -> 'LogMessage':
        return cls(msg, LogLevel.INFO)

    @classmethod
    def warning(cls, msg: MsgType) -> 'LogMessage':
        return cls(msg, LogLevel.WARNING)

    @classmethod
    def error(cls, msg: MsgType) -> 'LogMessage':
        return cls(msg, LogLevel.ERROR)

    @classmethod
    def tip(cls, msg: MsgType) -> 'LogMessage':
        return cls(msg, LogLevel.TIP)

