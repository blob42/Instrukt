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
import typing as t

from textual import on
from textual.app import ComposeResult
from textual.containers import Container
from textual.events import Mount, ScreenResume
from textual.reactive import reactive
from textual.widgets import Button, SelectionList

from ...types import InstruktDomNodeMixin
from .basemenu import BaseModalMenu

if t.TYPE_CHECKING:
    from ...agent.base import InstruktAgent
    from ...tools.base import SomeTool


class ToolsMenuScreen(BaseModalMenu, InstruktDomNodeMixin):

    BINDINGS = [("D", "dev_console", "dev console")]

    AUTO_FOCUS = "SelectionList"
    attached: reactive[list[str]] = reactive(list)
    toolset: reactive[t.Sequence["SomeTool"]] = reactive(list)

    @property
    def active_agent(self) -> t.Optional["InstruktAgent"]:
        if self._app.agent_manager is not None:
            return self._app.agent_manager.active_agent
        return None

    def compose(self) -> ComposeResult:
        # items = [("First", "first"), ("Second", "second")]
        with Container(id="menu"):
            yield from self._build_menu()
            # yield SelectionList(*items)
            yield Button("Manage", id="manage", variant="warning")

    def _build_menu(self, *args, **kwargs) -> ComposeResult:
        def tool_name(tool: "SomeTool") -> str:
            if tool.is_retrieval:
                return f"{tool.name.capitalize()} [b yellow]\[R][/]"
            else:
                return tool.name.capitalize()
        self.sel_list = SelectionList(*[(tool_name(t), t.name)
                                        for t in self.toolset])
        yield self.sel_list


    def _attached(self, name: str) -> bool:
        """Check if a tool is attached to the active agent."""
        return name in self.attached

    async def _update_menu(self) -> None:
        """rebuild the menu."""
        container = self.query_one(Container)
        await container.remove_children()
        container.mount(*self._build_menu())
        container.query_one(SelectionList).focus()

    def _mark_selected_tools(self) -> None:
        """Mark attached tools in the menu."""
        selected = self.sel_list.selected
        for tool in self.toolset:
            if self._attached(tool.name) and tool.name not in selected:
                self.sel_list.select(tool.name)

    async def watch_toolset(self) -> None:
        self.log.debug("watch toolset")
        await self._update_menu()

    def watch_attached(self) -> None:
        self._mark_selected_tools()

    @on(Mount)
    @on(ScreenResume)
    async def _on_resume(self) -> None:
        if self.active_agent is not None:
            self.toolset = self.active_agent.toolset or []
            self.attached = [t.name for t in self.toolset
                             if self.active_agent.is_attached_tool(t.name)]
        
        self.call_later(self._mark_selected_tools)

    @on(SelectionList.SelectionToggled)
    def selection_changed(self, event: SelectionList.SelectionToggled) -> None:
        """Update the agent's attached tools"""
        self.log.debug(event.selection.value)
        self.log.debug(event.selection_list.selected)
        # agent.detach_tool(tool)
        if self.active_agent is None:
            self.log.error("No active agent")
            return

        # dettached
        if event.selection.value not in event.selection_list.selected:
            try:
                self.attached.remove(event.selection.value)
            except ValueError:
                self.log.warning(f"Tool {event.selection.value} not attached")
            self.active_agent.dettach_tool(event.selection.value)
        # attached
        else:
            # add to list without duplicated
            if event.selection.value not in self.attached:
                self.attached.append(event.selection.value)
                self.active_agent.attach_tool(event.selection.value)


