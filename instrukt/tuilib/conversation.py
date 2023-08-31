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
"""UI elements used for conversations with agents."""

import typing as t
from pathlib import Path

import pyperclip
from langchain.schema import Document
from rich.console import RenderableType
from rich.markdown import Markdown as RichMarkdown
from textual import events, on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widgets import Label, Static

from ..config import APP_SETTINGS
from ..output_parsers.parser_lib import get_rich_md
from ..schema import AgentChatMessage, ChatMessage, HumanChatMessage
from ..subprocess import ExternalProcessMixin

if t.TYPE_CHECKING:
    from .repl_prompt import REPLPrompt


class MessageContainer(Container):
    """Base widget for chat messages."""

    message: ChatMessage

    def __init__(self, msg: ChatMessage, **kwargs: t.Any) -> None:
        super().__init__(**kwargs)
        self._path_map: dict[str, Document] = {}
        self.sources: list[Document] = []
        self.is_human = False

        if isinstance(msg, HumanChatMessage):
            self.add_class("human")
            self.is_human = True
        else:
            self.add_class("agent")

        if isinstance(msg.content, str):
            self.message = msg
            self.message_body = MessageBody(msg.content,
                                            is_human=self.is_human)
        elif isinstance(msg.content, dict):
            if 'ret_output' in msg.content:
                self.message = msg
                self.message_body = MessageBody(msg.content['ret_output'],
                                                is_human=self.is_human)
                self.sources = msg.content.get("source_documents", [])

    @property
    def source_paths(self) -> t.Iterable[str]:
        """Return a list of source paths."""
        for src in self.sources:
            src_path = src.metadata.get("source")
            if src_path is not None:
                if src_path.startswith(str(Path.home())):
                    src_path = Path(src_path).relative_to(Path.home())
                src_path = str(Path(".../", *(Path(src_path).parts)[-3:]))
                self._path_map[src_path] = src
        return self._path_map.keys()

    @property
    def with_sources(self) -> bool:
        """Return True if the message has sources."""
        return bool(self.sources)

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        msg_header = ""
        # if isinstance(self.message, HumanChatMessage):
        #     msg_header = "You"
        if isinstance(self.message, AgentChatMessage):
            if self.with_sources:
                msg_header = "C-e \[edit] | C-p \[select source]"
            else:
                msg_header = "C-e \[edit]"
        self.message_body.border_title = msg_header
        yield self.message_body
        sources = Container(id="sources")
        sources.border_title = "sources"
        with sources:
            for src in set(self.source_paths):
                yield Label(src, shrink=True)


class ChatBubble(Horizontal, ExternalProcessMixin, can_focus=True):
    """A chat bubble."""

    BINDINGS = [
        Binding("ctrl+e", "external_editor", "edit", key_display="C-e"),
        Binding("ctrl+p", "select_source", "select source", key_display="C-p")
    ]

    def __init__(self, msg: ChatMessage, **kwargs) -> None:
        super().__init__(**kwargs)
        self._msg_container = MessageContainer(msg)
        self._msg = msg
        if self._msg_container.is_human:
            self.can_focus = False
        if isinstance(msg.content, dict):
            if 'ret_output' in msg.content:
                self.add_class("--with-sources")

    @property
    def content(self) -> str:
        if isinstance(self._msg.content, dict):
            if 'ret_output' in self._msg.content:
                return self._msg.content['ret_output']
        assert isinstance(self._msg.content, str)
        return self._msg.content

    def compose(self) -> ComposeResult:
        yield Static(classes="left-space")
        yield self._msg_container

    @on(events.Click)
    def copy_msg_clipboard(self, ev: events.Click) -> None:
        """Copy the content of the message to the clipboard."""
        self.focus()
        if isinstance(self._msg, AgentChatMessage):
            try:
                if pyperclip.is_available():
                    pyperclip.copy(self._msg.content)
            except pyperclip.PyperclipException as e:
                from ..messages.log import LogMessage
                self.app.post_message(LogMessage.error(e))

    def action_external_editor(self) -> None:
        output = self.edit(self.content.strip())
        if output is not None:
            prompt = t.cast("REPLPrompt", self.app.query_one("REPLPrompt"))
            assert prompt is not None
            prompt.value = output.strip()
            self.call_next(prompt.action_submit)

    def action_select_source(self) -> None:
        """Open document sources in external finder process.

        A finder can be any program that takes a list of items from stdin
        and returns the selected item on stdout.

        Examples: `fzf` or `rofi -dmenu`
        """
        selected = ""
        src_paths: t.Set[str] = set()
        for doc in self._msg_container.sources:
            src = doc.metadata.get("source")
            if src is not None:
                src_paths.add(src)

        if src_paths:
            selected = self.select(list(src_paths))

        if selected:
            self.open_path(selected)




class MessageBody(Label, can_focus=False):
    """Base widget for chat messages."""
    _content: str
    code_theme = APP_SETTINGS.interface.code_block_theme

    def __init__(self,
                 content: str,
                 is_human: bool = False,
                 **kwargs: t.Any) -> None:

        self._is_human = is_human
        if is_human:
            super().__init__(content, **kwargs)
        else:
            md = get_rich_md(content,
                              code_theme=self.code_theme,
                              hyperlinks=False)
            super().__init__(md, markup=True, **kwargs)
        self._content = content

    def update(self, *content: RenderableType) -> None:
        """Update the text. Only one argument is allowed."""
        #HACK:
        self._content = str(content[0])
        if self._is_human:
            super().update(self._content)
        else:
            md = get_rich_md(self._content,
                              code_theme=self.code_theme,
                              hyperlinks=False)
            super().update(md)

    @on(events.Click)
    def hover(self):
        if self.parent is not None:
            self.call_next(self.parent.parent.focus, False)
