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
"""Agent window."""
import typing as t

from textual import on, work
from textual.app import ComposeResult, RenderResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Button, Label, Static

from ...agent.events import AgentEvents
from ...agent.state import AgentState
from ...config import APP_SETTINGS
from ...messages.agents import AgentLoaded, AgentMessage
from ...schema import (
    LC_TO_INSTRUKT_MESSAGES,
    AgentChatMessage,
    ChatMessage,
    HumanChatMessage,
)
from ...types import InstruktDomNodeMixin
from ..conversation import ChatBubble
from ..modals.basemenu import set_screen_menu_position
from ..strings import ICONS
from ..widgets.spinner import FutureSpinner, SpinnerWidget

if t.TYPE_CHECKING:
    from instrukt.agent.base import InstruktAgent

    from ..panels import MonitorPane


class LLMContext(Label):
    prompt_tokens: reactive[int] = reactive(0, layout=True)
    """Last prompt tokens."""

    def render(self) -> RenderResult:
        return f"prmpt: {self.prompt_tokens}"


class LLMTokens(Label):
    total_tokens: reactive[int] = reactive(0, layout=True)

    def render(self) -> RenderResult:
        return f"ttok: {self.total_tokens}"


class LLMCost(Label):
    total_cost: reactive[float] = reactive(0.0, layout=True)

    def render(self) -> RenderResult:
        return f"$: {self.total_cost:.4f}"


class AgentStatusBar(Horizontal, InstruktDomNodeMixin):
    DEFAULT_CLASSES = "ready"

    def compose(self) -> ComposeResult:
        yield Static(classes="spacer")
        yield Label("", id="model-name")
        yield LLMCost()
        yield LLMTokens()
        yield LLMContext()
        yield SpinnerWidget("noise", classes="spinner")

    def watch_state(self, state: AgentState) -> None:
        if state == AgentState.READY:
            self.add_class("ready")
            assert self._app.active_agent is not None
            # set model name
            self.query_one("#model-name").update(
                self._app.active_agent.llm.model_name)
            if self._app.active_agent.openai_cb_handler is None:
                return
            last_pr_tokens = self._app.active_agent.openai_cb_handler.last_prompt_tokens
            cost = self._app.active_agent.openai_cb_handler.total_cost
            total_tokens = self._app.active_agent.openai_cb_handler.total_tokens
            self.query_one(LLMContext).prompt_tokens = last_pr_tokens
            self.query_one(LLMCost).total_cost = cost
            self.query_one(LLMTokens).total_tokens = total_tokens
        else:
            self.remove_class("ready")


class AgentWindow(Container, InstruktDomNodeMixin):

    BINDINGS = [
            Binding("G", "goto_bottom", "end"),
            Binding("T", "goto_top", "top"),
            Binding("ctrl+n", "focus_next", "next" , show=False),
            Binding("ctrl+p", "focus_previous", "prev" , show=False),
            ]


    def compose(self) -> ComposeResult:
        yield AgentWindowHeader(classes="--topbar")
        yield AgentConversation(
            # highlight=True,
            #   markup=True,
            #   wrap=True,
            classes="window")
        yield AgentStatusBar()

    def watch_state(self, state: AgentState) -> None:
        if state == AgentState.READY:
            self.border_title = self._app.active_agent.display_name   # type: ignore


    def action_goto_bottom(self) -> None:
        self.query_one(AgentConversation).scroll_end()

    def action_goto_top(self) -> None:
        self.query_one(AgentConversation).scroll_home()



class AgentConversation(VerticalScroll, InstruktDomNodeMixin, can_focus=False):
    """Displays the conversation with the active agent."""

    _chat_messages: reactive[list["ChatMessage"]] = reactive([])

    @work(exclusive=True)
    async def preload_messages(self, agent: "InstruktAgent") -> None:
        """Load the chat messages from memory."""
        assert self._app.active_agent is not None
        assert agent.memory is not None

        # for each message in the agent's memory check if the pydantic model's title
        # has human or ai in it then load it as a local schema of
        # HumanMessage or AgentMessage
        for msg in agent.memory.chat_memory.messages:
            msg_cls = LC_TO_INSTRUKT_MESSAGES[type(msg)]
            self._chat_messages.append(msg_cls(msg.content))

        msg_bubbles = [self._make_msg(m) for m in self._chat_messages]
        await self.mount_all(msg_bubbles)
        self.scroll_end(animate=True, duration=0.15)

    async def push_msg(self,
                       message: "ChatMessage",
                       scroll: bool = True) -> None:
        """Push a message to the chat."""
        msg = self._make_msg(message)

        await self.mount(msg)
        if scroll:
            self.scroll_end(animate=False)

    def _make_msg(self, message: "ChatMessage") -> ChatBubble:
        msg = ChatBubble(message)
        if isinstance(message, HumanChatMessage):
            msg.add_class("human")
        else:
            msg.add_class("agent")
        return msg


    async def clear(self):
        await self.query("*").remove()
        self._chat_messages = []

    #TEST: state and observer when multiple agents running
    #NOTE: state observers execute on active agent or any agent ?
    @on(AgentLoaded)
    async def handle_agent_loaded_msg(self, message: AgentLoaded):
        """Handle the AgentLoaded message."""

        await self.clear()

        agent: "InstruktAgent" = message.agent
        monitor = t.cast('MonitorPane', self.app.query_one("#monitor-pane"))
        if agent.realm is not None:
            await monitor.show_realm()
            self._app.notify_realm_buffer(message)
        else:
            monitor.hide_realm()
        agent.state.register_observer(self)

        #TODO!: refactor code duplication to function
        # agent window
        agent_window = self.screen.query_one(AgentWindow)
        agent.state.register_observer(agent_window)

        # register AgentStatus widget
        status_widget = self.app.query_one(AgentStatus)
        agent.state.register_observer(status_widget)
        self.call_later(
            lambda: message.agent.state.set_state(AgentState.READY))

        # register realm window
        if agent.realm is not None:
            realm_info = self.screen.query_one("RealmInfo")
            agent.state.register_observer(realm_info)

        # register statusbar
        statusbar = self.screen.query_one("AgentStatusBar")
        agent.state.register_observer(statusbar)

        # register agent tabs
        agent_tabs = self.screen.query_one("AgentTabs")
        self._app.active_agent.state.register_observer(agent_tabs)
        agent_tabs.post_message(AgentLoaded(agent))

        # preload all messages from memory
        if len(agent.memory.chat_memory.messages) > 0:
            self.preload_messages(agent)

        message.stop()

    def watch_state(self, state: AgentState) -> None:
        """Implement the agents' state observer pattern"""
        pass

    @on(AgentMessage)
    async def handle_agent_msg(self, message: AgentMessage):
        """Main agent event handler."""
        #FIXME: reset the state of last used tool on agent finish
        if message.event in [AgentEvents.AgentFinish]:
            self.parent.query_one(AgentStatus).tool = ""   # type: ignore

            output = message.data.return_values['output']
            await self.push_msg(AgentChatMessage(content=output))

        #TODO: use model to get data out of message
        #NOTE: use this event for catching tool events in general
        # elif message.event == AgentEvents.ToolStart:
        #     tool = message.data['name']
        #     self.parent.query_one(AgentStatus).tool = tool

        elif message.event == AgentEvents.AgentAction:
            tool = message.data.tool
            self.parent.query_one(AgentStatus).tool = tool

        elif message.event == AgentEvents.ToolEnd:
            self.parent.query_one(AgentStatus).tool = ""

        elif message.event == AgentEvents.HumanMessage:
            await self.push_msg(HumanChatMessage(content=message.data))

        else:
            self.log.debug(f"received message {message}")

        message.stop()


class AgentStatus(Static):
    """Shows the agent's status in the top bar of the agent window."""

    agent_state = reactive(AgentState.NIL)
    status = reactive("")
    tool = reactive("")

    def watch_state(self, state: AgentState) -> None:
        """Implement the agents' state observer pattern"""
        self.agent_state = state

        if state == AgentState.READY:
            self.add_class("ready")

    def render(self) -> RenderResult:
        _status = self.status.split("_")
        if len(_status) == 2:
            msg = f"[b]{_status[1].capitalize().rstrip()}[/]"
            if len(self.tool) > 0:
                return f"{msg} -> {self.tool}"
            return msg
        else:
            return f"[b]{_status[0].capitalize().rstrip()}[/]"

    def compute_status(self) -> str:
        if self.agent_state == AgentState.NIL:
            return ""
        # elif self.agent_state == AgentState.TOOL_PROCESSING:
        #     return f"Processing[{self.tool}]"
        # elif self.agent_state == AgentState.IDLE:
        #     return "Ready"
        # elif self.agent_state == AgentState.RUNNING:
        #     return "Running"
        # elif self.agent_state == AgentState.FINISHED:
        #     return "Finished"
        # elif self.agent_state == AgentState.STOPPED:
        #     return "Stopped"
        # elif self.agent_state == AgentState.ERROR:
        #     return "Error"
        # else:
        #     return "Unknown"
        else:
            return self.agent_state.name.capitalize()


class AgentMenu(Horizontal):

    def on_mount(self):
        if APP_SETTINGS.interface.nerd_fonts:
            self.add_class("-nerd")

    def compose(self) -> ComposeResult:
        yield Button(label=ICONS.index, id="index")  # index (vectorstores)
        yield Button(label=ICONS.agent_tools, id="tools")  #tools
        yield Button(label=ICONS.agent_settings, id="settings",
                     disabled=True)  # settings

    @on(Button.Pressed, "#index")
    async def show_index_menu(self, event: Button.Pressed) -> None:
        await self.app.push_screen("index_menu")
        self.call_next(set_screen_menu_position, self.app, "index_menu",
                       event.button.region)

    @on(Button.Pressed, "#tools")
    async def show_tools_menu(self, event: Button.Pressed) -> None:
        await self.app.push_screen("tools_menu")
        self.call_next(set_screen_menu_position, self.app, "tools_menu",
                       event.button.region)


class AgentWindowHeader(Container):

    def compose(self) -> ComposeResult:

        with Horizontal(id="agent-menu"):
            with Horizontal(id="agent-menu-info"):
                yield AgentStatus(classes="--topbar-entry")
                yield FutureSpinner(spinner="bouncingBar", id="progress")

            yield AgentMenu()
