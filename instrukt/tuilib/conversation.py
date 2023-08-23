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

import pyperclip
from rich.console import RenderableType
from rich.markdown import Markdown as RichMarkdown
from textual import events, on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widgets import Label, Static

from ..config import APP_SETTINGS
from ..output_parsers.parser_lib import sanitize_md_code
from ..schema import AgentChatMessage, ChatMessage, HumanChatMessage
from ..subprocess import ExternalProcessMixin


class MessageContainer(Container):
    """Base widget for chat messages."""

    message: ChatMessage

    def __init__(self, msg: ChatMessage,
                 **kwargs: t.Any) -> None:
        super().__init__(**kwargs)
        self.is_human = False
        if isinstance(msg, HumanChatMessage):
            self.add_class("human")
            self.is_human = True
        else:
            self.add_class("agent")
        self.message = msg
        self.message_body = MessageBody(msg.content, is_human=self.is_human)

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        msg_from = ""
        if isinstance(self.message, HumanChatMessage):
            msg_from = "You"
        else:
            msg_from = "Agent"
        self.border_title = msg_from
        yield self.message_body


class ChatBubble(Horizontal, ExternalProcessMixin, can_focus=True):
    """A chat bubble."""

    BINDINGS = [
            Binding("ctrl+e", "external_editor", "edit", key_display="C-e"),
            ]

    def __init__(self, msg: ChatMessage, **kwargs) -> None:
        super().__init__(**kwargs)
        self._message_box = MessageContainer(msg)
        self._msg = msg
        if self._message_box.is_human:
            self.can_focus = False

    def compose(self) -> ComposeResult:
        yield Static(classes="left-space")
        yield self._message_box

    @on(events.Click)
    def copy_msg_clipboard(self, ev: events.Click) -> None:
        """Copy the content of the message to the clipboard."""
        if isinstance(self._msg, AgentChatMessage):
            try:
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
            md = RichMarkdown(
                    content,
                    code_theme=self.code_theme,
                    hyperlinks=False
                    )
            super().__init__(sanitize_md_code(md), markup=True, **kwargs)
        self._content = content

    def update(self, *content: RenderableType) -> None:
        """Update the text. Only one argument is allowed."""
        #HACK:
        self._content = str(content[0])
        if self._is_human:
            super().update(self._content)
        else:
            # sanitize source code first

            md = RichMarkdown(self._content,
                              code_theme=self.code_theme,
                              hyperlinks=False)
            super().update(sanitize_md_code(md))


    @on(events.Click)
    def hover(self):
        if self.parent is not None:
            self.call_next(self.parent.parent.focus, False)
