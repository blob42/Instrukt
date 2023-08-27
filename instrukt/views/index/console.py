##
##  Copyright (c) 2023 Chakib Ben Ziane <contact@blob42.xyz> . All rights reserved.
##
##  SPDX-License-Identifier: AGPL-3.0-or-later
##
##  This file is part of Instrukt.
##
##  This program is free software: you can redistribute it and/or modify
##  it under the terms of the GNU Affero General Public License as
##  published by the Free Software Foundation, either version 3 of the
##  License, or (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU Affero General Public License for more details.
##
##  You should have received a copy of the GNU Affero General Public License
##  along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
"""Console for the index view."""
import re
import typing as t
from typing import Any

from rich.console import RenderableType
from textual import events, on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.reactive import var
from textual.widgets import (
    Label,
    ProgressBar,
    RichLog,
)

from ...messages.base import ConsoleClose, ConsoleOpen
from ..._logging import ANSI_ESCAPE_RE
from ...tuilib.widgets.progress import ProgressBarWrapper
from ...types import ProgressProtocol

if t.TYPE_CHECKING:
    from typing_extensions import Self


class ConsoleMessage(Message):

    def __init__(self, msg: Any):
        self.msg = msg
        super().__init__()


class ConsoleHeader(Horizontal):
    minimized = var[bool](False)

    def compose(self) -> ComposeResult:
        self.label = Label("\[c]onsole", classes="console--label")
        self.message = Label(classes="console--msg")
        self.progress = ProgressBar(show_eta=False, show_percentage=False)
        yield self.label
        yield self.message
        yield self.progress

    def update_label(self, content: RenderableType) -> None:
        self.label.update(content)

    def set_msg(self, content: RenderableType) -> None:
        self.message.update(content)

    @property
    def pbar(self) -> ProgressProtocol:
        """Returns wrapped progress bar with ProgressProtocol."""
        return ProgressBarWrapper(self.progress)


class IndexConsole(RichLog, can_focus=False, can_focus_children=False):
    minimized = var[bool](False)
    has_log = var[bool](False)
    user_minimzed = var[bool](False)

    def on_mount(self) -> None:
        # DEBUG:
        # self.set_msg("updating bar ...")
        self.minimize()
        self.call_later(self.begin_capture_print)

    def compose(self) -> ComposeResult:
        self.header = ConsoleHeader()
        yield self.header
        self.tl = RichLog(wrap=True, highlight=True)
        yield self.tl

    def watch_minimized(self, m: bool) -> None:
        if m and self.has_log:
            # self.border_title = "\[c]onsole [b yellow][/]"
            self.query_one(ConsoleHeader).update_label(
                "\[c]onsole [b yellow][/]")
        else:
            self.query_one(ConsoleHeader).update_label("\[c]onsole")

    def watch_has_log(self, m: bool) -> None:
        if m:
            self.query_one(ConsoleHeader).update_label(
                "\[c]onsole [b yellow][/]")
        else:
            self.query_one(ConsoleHeader).update_label("\[c]onsole")

    def on_print(self, event: events.Print) -> None:
        text = event.text
        text = text.strip()
        # clean up ansi escape sequences
        text = re.sub(ANSI_ESCAPE_RE, "", text, flags=re.MULTILINE)

        if len(text) > 0:
            self.tl.write(text, expand=True)
            self.has_log = True
            if self.minimized and not self.user_minimzed:
                self.open()

    def print(self, text: str) -> None:
        self.tl.write(text, expand=True)
        self.has_log = True
        if self.minimized and not self.user_minimzed:
            self.open()

    def clear(self):
        self.has_log = False
        return self.tl.clear()

    def on_click(self, event: events.Click) -> None:
        self.toggle_console(True)

    def toggle_console(self, user: bool = False) -> None:
        self.open() if self.minimized else self.minimize()
        if user:
            self.user_minimzed = True

    def minimize(self, user: bool = False) -> None:
        self.add_class("--minimize")
        self.post_message(ConsoleClose())
        self.minimized = True
        if user:
            self.user_minimzed = True

    def open(self) -> None:
        self.remove_class("--minimize")
        self.post_message(ConsoleOpen())
        self.minimized = False

    def is_empty(self) -> bool:
        return len(self.tl.lines) == 0

    def set_msg(self, content: RenderableType) -> None:
        self.header.set_msg(content)

    def clear_msg(self) -> "Self":
        self.header.set_msg("")
        return self

    @property
    def pbar(self) -> ProgressProtocol:
        """Returns wrapped progress bar with ProgressProtocol."""
        return self.header.pbar

    @on(events.ScreenResume)
    def on_resume(self, event: events.ScreenResume) -> None:
        self.begin_capture_print()
        self.user_minimzed = False

    @on(events.ScreenSuspend)
    def on_suspend(self, event: events.ScreenSuspend) -> None:
        self.end_capture_print()

        # WIP: should be done explicitly by the user
        self.clear()
        self.minimize()
