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
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.widgets import Static, Tab, Tabs, Label, Button
from textual import events

from .strings import ICONS
from ..agent.state import AgentState
from ..messages.agents import AgentLoaded
from ..types import InstruktDomNodeMixin
from .repl_prompt import REPLPrompt
from .windows import AgentWindow, ConsoleWindow, RealmWindow, RealmWindowHeader


class MainConsole(Vertical):
    """Main console for REPL and commands output."""

    def compose(self) -> ComposeResult:
        yield ConsoleWindow(highlight=True,
                        markup=True,
                        wrap=True,
                        classes="window")



class Realm(Container):
    """Realm container"""

    def compose(self) -> ComposeResult:
        yield RealmWindowHeader(classes="--topbar")
        yield RealmWindow(highlight=True, wrap=True, classes="window")

#TODO: move to own module
class AgentTabs(Static, InstruktDomNodeMixin):

    active_agent: reactive[str | None] = reactive(None)
    tabs: Tabs
    NEW_TAB_ID = "new-tab"

    def watch_state(self, state: AgentState) -> None:
        self.log.debug("State changed")

    @on(AgentLoaded)
    async def handle_agent_loaded(self, message: AgentLoaded) -> None:
        self.active_agent = message.agent.name
        self.sync()
        message.stop()

    def sync(self) -> None:
        """Sync agents with tabs"""
        tab_ids = [t.id for t in self.tabs.query(Tab)]
        loaded_agents = self._app.agent_manager.loaded_agents

        # for missing tabs in tab_ids add tab
        # for missing agents in loaded_agents remove tab
        for agent_id in loaded_agents:
            if agent_id not in tab_ids:
                agent = self._app.agent_manager.from_name(agent_id)
                assert agent is not None
                assert agent.display_name is not None
                #FIX: see patch #2762 on textual
                # self.tabs.add_tab(Tab(agent.display_name, id=agent_id),
                #                   before=0)
                self.tabs.add_tab(Tab(agent.display_name, id=agent_id))
        for tab in tab_ids:
            if tab not in loaded_agents and tab != self.NEW_TAB_ID:
                self.tabs.remove_tab(tab)

        #activate active agent
        if self.active_agent is not None:
            self.tabs.active = self.active_agent

    def get_display_name(self, agent: str) -> str:
        """Get display for given agent id."""
        return self._app.agent_manager._agents[agent]

    async def rebuild(self) -> None:
        """Tears down and rebuilds all tabs."""
        await self.remove_children()
        self.mount(*self.build_tabs())

    def build_tabs(self) -> ComposeResult:
        agents = []
        # always add active agent
        if self.active_agent is not None:
            agents.append(
                    Tab(
                        self.get_display_name(self.active_agent),
                        id=self.active_agent)
                    )
        self.tabs = Tabs(
                *agents,
                Tab("+", id=self.NEW_TAB_ID)
                )
        yield self.tabs

    def compose(self) -> ComposeResult:
        yield from self.build_tabs()


    @on(Tabs.TabActivated)
    async def handle_tab_activated(self, message: Tabs.TabActivated) -> None:
        """Handle tab activated message."""
        if message.tab.id == self.NEW_TAB_ID:
            self.screen.add_class("-show-new-agent")
            self.screen.query_one("StartupMenu ListView").focus()
        else:
            self.active_agent = message.tab.id
            assert message.tab.id is not None
            await self._app.agent_manager.switch_agent(message.tab.id)
        message.stop()


class MonitorPane(Vertical, InstruktDomNodeMixin):
    """Monitor agent outputs including conversation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._realm: Realm | None = None

    def compose(self):
        self._agent_window = AgentWindow()
        yield self._agent_window
        yield AgentTabs()

    async def show_realm(self):
        """Show realm window for agents which support it."""
        if self._realm is None:
            self._realm = Realm(id="realm-container")
            await self.mount(self._realm, before=self._agent_window)
        self.add_class("-show-realm")



    def hide_realm(self):
        self.remove_class("-show-realm")
