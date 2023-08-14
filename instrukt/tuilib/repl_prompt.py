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
"""Main prompt."""
from enum import Enum
from importlib import import_module
from typing import (
    Any,
    Optional,
    Union,
)

from textual.binding import Binding
from textual.widgets import Input
from textual import on
from textual.worker import Worker, WorkerState

from ..agent import AgentEvents
from ..commands.command import CMD_PREFIX
from ..commands.history import CommandHistory
from ..messages.agents import AgentMessage
from ..messages.log import LogMessage
from .input import blur_on
from .windows import ConsoleWindow
from ..types import InstruktDomNodeMixin


class CmdMsg(str):
    """A message destined to the REPL."""
    pass


class ToAgentMsg(str):
    """A message destined to agents."""
    pass


@blur_on(key="escape")
class REPLPrompt(Input, InstruktDomNodeMixin):

    BINDINGS = [
        Binding("up", "history_prev", "previous command", show=False),
        Binding("down", "history_next", "next command", show=False),
        Binding("ctrl+s", "stop_agent", "stop running agent", show=False),
        Binding("ctrl+e", "external_editor", "external editor", show=True,
                key_display="ctrl+e")
    ]

    class Mode(Enum):
        NORMAL = 0
        SEARCH = 1

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.placeholder = ""
        self.cmd_history = CommandHistory(
            config=self._app.context.config_manager.config)
        self.cmd_history.load()

        #WIP: use reactive attribute here
        self.mode = self.Mode.NORMAL

    def on_mount(self) -> None:
        self.main_buffer = self._app.query_one(ConsoleWindow)

    def _parse_input(self, msg: str) -> Optional[Union[CmdMsg, ToAgentMsg]]:
        if len(msg) == 0:
            return None
        if msg in ["help", "h", "?"]:
            self.cmd_history.add(msg)
            return CmdMsg("help")
        if msg == "%debug":
            import_module("instrukt.commands.debug")
            self._write_main_buffer(LogMessage.info("Debug mode activated."))
            return CmdMsg("debug")
        elif msg[0] in CMD_PREFIX:
            self.cmd_history.add(msg)
            return CmdMsg(msg[1:])
        elif len(msg) > 0:
            self.cmd_history.add(msg)
            return ToAgentMsg(msg)
        else:
            return None

    async def _update_curosr_pos(self) -> None:
        self.cursor_position = len(self.value)

    async def action_history_prev(self) -> None:
        self.value = self.cmd_history.get_previous().entry
        self.call_next(self._update_curosr_pos)


    # see https://github.com/Textualize/textual/discussions/165
    def action_external_editor(self) -> None:
        """Open an external editor for editing with an optinal starting text."""
        import tempfile
        import subprocess
        import os
        self.app._driver.stop_application_mode()
        initial = self.value
        try:
            with tempfile.NamedTemporaryFile(mode="w+") as ef:
                ef.write(initial)
                ef.flush()
                # Need to create a separate backup copy
                # If we don't, the edited text will not be saved into the current file
                # get EDITOR from env
                editor = os.environ.get('EDITOR', 'vim')
                subprocess.call([editor, '+set backupcopy=yes', ef.name])
                ef.seek(0)
                input_ = ef.read()
                self.value = input_.strip()
                self.call_next(self._update_curosr_pos)
        finally:
            self.app.refresh()
            self.app._driver.start_application_mode()




    async def action_history_next(self) -> None:
        self.value = self.cmd_history.get_next().entry
        self.call_next(self._update_curosr_pos)

    def _write_main_buffer(self, msg: Any) -> None:
        """Write on main buffer"""
        self.main_buffer.write(msg, expand=True)

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        self.value = ''
        parsed = self._parse_input(message.value.strip())

        if parsed is None:
            msg = f"commands must start with `{CMD_PREFIX}`"
            self._write_main_buffer(msg)

        if isinstance(parsed, CmdMsg):
            if parsed == "debug":
                return
            try:
                output = await self._app.cmd_handler.execute(self._app.context, parsed)
                if output is not None:
                    self._write_main_buffer(output)
            except Exception as e:
                self._write_main_buffer(LogMessage.error(e))

        # if this is a message to the agent
        if isinstance(parsed, ToAgentMsg):
            #HACK: should be implemented as an event
            if self._app.active_agent is not None:
                self.run_worker(
                    self._app.active_agent.send_message(self._app.context,
                                                       parsed), name="agent_work")
                post_msg = AgentMessage(AgentEvents.HumanMessage, data=parsed)
                self.app.post_message(post_msg)


    @on(Worker.StateChanged)
    def handle_agent_work(self, event: Worker.StateChanged) -> None:
        if event.state == WorkerState.CANCELLED:
            cancel_msg = AgentMessage(AgentEvents.AgentCancelled)
            self.app.post_message(cancel_msg)
            agent = self._app.agent_manager.active_agent
            assert agent is not None, "agent should be active"
            agent.state.update_state(AgentEvents.AgentCancelled.value)

    async def action_stop_agent(self) -> None:
        """Stop the running agent."""
        agent = self._app.agent_manager.active_agent
        if agent is not None:
            await agent.stop_agent(self._app.context)
