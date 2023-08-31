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
import typing as t
from difflib import get_close_matches
from enum import Enum
from importlib import import_module

from textual import events, on
from textual.binding import Binding
from textual.suggester import Suggester
from textual.widgets import Input
from textual.worker import Worker, WorkerState
from textual.messages import Message

from ..agent import AgentEvents
from ..commands.command import CMD_PREFIX
from ..commands.history import CommandHistory
from ..messages.base import RetrievalLLM
from ..messages.agents import AgentMessage
from ..messages.log import LogMessage
from ..subprocess import ExternalProcessMixin
from ..types import InstruktDomNodeMixin
from .input import blur_on
from .windows import ConsoleWindow


class Suggestion(t.NamedTuple):
    suggestion: str
    """Suggestion token"""

    action: str
    """Action to be called when the suggestion is selected"""

    def __str__(self) -> str:
        return self.suggestion

TSuggestion = str | Suggestion

class ActionSuggestions(dict[str, str]):
    """Dict like class for storing suggestions with actions"""

    def __init__(self, *suggestions: Suggestion, **kwargs) -> None:
        super().__init__(**kwargs)
        for suggestion in suggestions:
            self.add(suggestion)

    def add(self, suggestion: Suggestion) -> None:
        self[suggestion.suggestion] = suggestion.action

    def get_full(self, value: str) -> Suggestion | None:
        if value in self:
            return Suggestion(value, self[value])
        else:
            return None



class ReplSuggester(Suggester):

    suggestions: list[str] = [
            # "gpt-3.5-turbo",
            # "gpt-4",
            # "gpt-3.5-turbo-0613",
            ]

    action_suggestions = ActionSuggestions(
            # Suggestion("test", "say_hello"),
            Suggestion("r:gpt4", "ret_llm_mode('gpt-4')"),
            Suggestion("r:gpt3", "ret_llm_mode('gpt-3.5-turbo')"),
            )

    def __init__(self, *args, **kwargs):
        self.current_suggestion = None
        super().__init__(*args, **kwargs)

    def add(self, *content: TSuggestion) -> None:
        for c in content:
            if isinstance(c, Suggestion):
                self.action_suggestions.add(c)
            else:
                self.suggestions = list(set(self.suggestions + [c]))

    @property
    def current_suggestion(self):
        """The current_suggestion property."""
        if self._current_suggestion in self.action_suggestions:
            return self.action_suggestions.get_full(self._current_suggestion)
        return self._current_suggestion

    @current_suggestion.setter
    def current_suggestion(self, value):
        self._current_suggestion = value

    @property
    def all(self) -> list[str]:
        return self.suggestions + list(self.action_suggestions.keys())


    #FIX: return highest confidence
    async def get_suggestion(self, value) -> str | None:
        suggestion = get_close_matches(value, self.all, n=1, cutoff=0.3)
        res = suggestion[0] if suggestion else None
        if res is not None:
            self.current_suggestion = res
        else:
            self.current_suggestion = None
        return res


        


class CmdMsg(str):
    """A message destined to the REPL."""
    pass


class ToAgentMsg(str):
    """A message destined to agents."""
    pass


@blur_on(key="escape")
class REPLPrompt(Input, InstruktDomNodeMixin, ExternalProcessMixin):

    class CmdEvent(Message):
        """User input a command."""

    BINDINGS = [
        Binding("up", "history_prev", "previous command", show=False),
        Binding("down", "history_next", "next command", show=False),
        Binding("ctrl+s", "stop_agent", "stop agent", key_display="C-s"),
        Binding("ctrl+e", "external_editor", "editor", show=True,
                key_display="C-e")
    ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(suggester=ReplSuggester(), *args, **kwargs)
        self.placeholder = ""
        self.cmd_history = CommandHistory(
            config=self._app.context.config_manager.config)
        self.cmd_history.load()

        #WIP: use reactive attribute here
        self.llm_mode = None


    def on_mount(self) -> None:
        self.main_buffer = self._app.query_one(ConsoleWindow)

    def _parse_input(self, msg: str) -> t.Optional[CmdMsg | ToAgentMsg]:
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

    def action_external_editor(self) -> None:
        """Open an external editor for editing with an optinal starting text."""
        output = self.edit(self.value.strip())
        if output is not None:
            self.value = output.strip()
            self.call_next(self.action_submit)

    async def action_history_next(self) -> None:
        self.value = self.cmd_history.get_next().entry
        self.call_next(self._update_curosr_pos)

    def _write_main_buffer(self, msg: t.Any) -> None:
        """Write on main buffer"""
        self.main_buffer.write(msg, expand=True)

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        self.value = ''
        parsed = self._parse_input(message.value.strip())

        if parsed is None:
            msg = f"commands must start with `{CMD_PREFIX}`"
            self._write_main_buffer(msg)

        if isinstance(parsed, CmdMsg):
            self.post_message(self.CmdEvent())
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


    def key_tab(self, ev: events.Key) -> None:
        """Handle auto completion and modal actions."""
        self.log.debug(f"tab pressed {ev.key}")
        if self.suggester.current_suggestion is not None and len(self.value) != 0:
            ev.stop()
            self.log.debug("suggesting")
            self.log.debug(self.suggester.current_suggestion)
            cur_sug = self.suggester.current_suggestion
            if isinstance(cur_sug, Suggestion):
                # self.call_next(self.action_cursor_right)

                #WIP: repl modes
                self.call_next(self.run_action, cur_sug.action)
                self.action_delete_left_all()
            else:
                self.call_next(self.action_cursor_right)
                self.call_later(self.insert_text_at_cursor, ': ')


        else:
            self.log.debug("not suggesting")

    def action_ret_llm_mode(self, mode: str):
        self.post_message(RetrievalLLM(mode))

    # def action_say_hello(self) -> None:
    #     self.log.debug("hello")
