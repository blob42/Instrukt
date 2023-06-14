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
"""Realm window."""

import typing as t

from textual.app import ComposeResult, RenderResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from ...agent.events import AgentEvents
from ...agent.state import AgentState
from ..strings import REALM_WINDOW_INTRO
from ..widgets.textlog import TextLogUp

if t.TYPE_CHECKING:
    from ...messages.agents import AgentLoaded, AgentMessage

#TODO: realm window hidden by default, show when realm active
class RealmWindow(TextLogUp, can_focus=False):
    """Window used for the agent's virtual environment"""

    def on_instrukt_app_ready(self):
        self.write(REALM_WINDOW_INTRO)

    async def on_instrukt_agent_loaded(self, message: 'AgentLoaded'):
        self.clear()

    async def on_instrukt_agent_message(self, message: 'AgentMessage'):
        tool_name = message.data['name']
        #HACK: other alternative to identify realm based tools
        if message.event == AgentEvents.ToolStart and tool_name == "Linux":
            self.write(message.data['input'])
        if message.event == AgentEvents.ToolEnd and tool_name == "Linux":
            self.write(f"{message.data['output']}")
        message.stop()
        self.scroll_end(animate=False)

class RealmInfo(Widget):
    """Show info about the agent's realm."""

    realm_info = reactive("")

    def watch_state(self, state: AgentState) -> None:
        """Implement the agents' state observer pattern (see AgentStateSubject)"""

        if state == AgentState.READY:
            jail_image = self.app.active_agent.realm.session.image_name
            realm_id = self.app.active_agent.realm.session.id
            self.realm_info = f"{jail_image}\[{realm_id}]"

    def render(self) -> RenderResult:
        return f"{self.realm_info}"


class RealmWindowHeader(Horizontal):

    def compose(self) -> ComposeResult:
        #TODO: use tool name
        yield Static("Linux Terminal", id="tool-name")
        yield Static("Realm\[docker]", id="filler")
        yield RealmInfo(id="realm-name", classes="header-entry")
