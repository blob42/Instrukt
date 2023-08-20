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

from textual import events, on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Label, ListItem

from ..agent.loading import ModuleManager
from ..schema import AgentManifest
from ..types import InstruktDomNodeMixin
from .widgets.listview import ListView


class StartupMenu(Container, InstruktDomNodeMixin):
    """Startup menu"""
    agent_manifest: reactive[AgentManifest | None] = reactive(None)
    highlighted_agent: reactive[str | None] = reactive(None)

    def compose(self) -> ComposeResult:
        yield Container(id="welcome")
        with Horizontal(id="agents-container"):
            with Container(classes="-agents-list"):
                with ListView() as lv:
                    self._list = lv
                    yield from self.build_menu()
            yield Label(classes="-agent-info")

    def build_menu(self) -> ComposeResult:
        for agent_mod in ModuleManager.list_modules():
            yield ListItem(Label(agent_mod), name=agent_mod)

    @on(ListView.Highlighted)
    def agent_higlighted(self, event: ListView.Highlighted) -> None:
        if event.item is not None:
            highlighted = event.item.name
            if highlighted is not None:
                agent_manifest = ModuleManager.get_manifest(highlighted)
                agent_info: Label = self.query_one(".-agent-info")
                agent_info.update(agent_manifest.description)


    @on(ListView.Selected)
    async def agent_selected(self, event: ListView.Selected) -> None:
        if event.item is not None:
            await self._app.agent_manager.load_agent(event.item.name)

    @on(events.MouseScrollUp)
    def __on_scroll_up(self, event: events.MouseScrollUp) -> None:
        self._list.action_cursor_up()

    @on(events.MouseScrollDown)
    def __on_scroll_down(self, event: events.MouseScrollDown) -> None:
        self._list.action_cursor_down()

    @on(events.Click)
    def select(self, event: events.Click) -> None:
        if event.button == 3:
            self._list.action_select_cursor()
