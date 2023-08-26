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
"""Index menu modal"""

import typing as t
import asyncio


from textual import on
from textual.app import ComposeResult
from textual.containers import Container
from textual.events import ScreenResume
from textual.reactive import reactive
from textual.widgets import Button, SelectionList
from textual.widgets.selection_list import Selection

from ...messages.agents import FutureAgentTask
from ...messages.indexes import IndexAttached
from ...context import index_manager
from ...types import InstruktDomNodeMixin
from ...views.index import IndexScreen
from .basemenu import BaseModalMenu

if t.TYPE_CHECKING:
    from ...indexes.schema import Collection
    from ...app import InstruktApp


class IndexMenuScreen(BaseModalMenu, InstruktDomNodeMixin):

    AUTO_FOCUS = "#menu SelectionList"

    collections: reactive[dict[str, "Collection"]] = reactive({})

    def compose(self) -> ComposeResult:

        with Container(id="menu"):
            yield Button("Manage Indexes", id="manage", variant="default")
            yield from self._build_menu()

    def index_attached_as_tool(self, index: str) -> bool:
        agent = self._app.agent_manager.active_agent
        assert agent is not None, "No active agent"
        return index in agent.attached_tools


    def _build_menu(self, *args, **kwargs) -> ComposeResult:

        index_manager = self._app.context.index_manager
        self.collections = {
            c.name: c
            for c in index_manager.list_collections()
        }

        col_sels: map[Selection[str]] = map(
            lambda c: Selection(*c),
            [(k.capitalize(), k, self.index_attached_as_tool(k))
             for k, v in self.collections.items()])

        yield SelectionList(*col_sels)

    async def _update_menu(self) -> None:
        await self.query_one(SelectionList).remove()
        await self.query_one("Container#menu").mount_all(self._build_menu())
        self.query_one(SelectionList).focus()


    async def add_index_as_tool(self, index_name: str) -> None:
        """Add selected index as tool to the active agent."""
        async with self.app._alock:
            with index_manager() as im:
                index = await im.aget_index(index_name)
                if index is None:
                    self._app.context.error(f"Index {index_name} not found")
                    return
                # get tool from index, return_direct
                tool = index.get_retrieval_tool(return_direct=True,
                                        with_sources=True)

                # add tool to active agent
                agent = self._app.agent_manager.active_agent
                if agent is None:
                    self._app.context.error("No active agent")
                    return

                agent.add_tool(tool)
                self._app.context.info(f"Index <{index_name}> added to agent")


    def detach_index_tool(self, index_name: str) -> None:
        agent = self._app.agent_manager.active_agent
        assert agent is not None, "No active agent"
        agent.dettach_tool(index_name)
        self.dismiss()


    async def _sync_collections(self):
        changed=False
        self.log.debug("sync collections")
        # check if there are new collections and update local one
        async with self.app._alock:
            with index_manager() as im:
                for index in im.indexes:
                    if index not in self.collections:
                        self.collections[index] = im.get_index(index)
                        changed = True

                _to_remove = []
                for c in self.collections.keys():
                    if c not in im.indexes:
                        _to_remove.append(c)
                        changed=True

                for c in _to_remove:
                    del self.collections[c]

                if changed:
                    await self._update_menu()


    @on(ScreenResume)
    async def check_attached_indexes(self, event: ScreenResume) -> None:
        self.log.debug("screen resume")
        self.call_later(self._sync_collections)

        # synchronize attached index tools with active agent and current selection list
        sel_list: SelectionList[str] = self.query_one(SelectionList)
        # im = self._app.context.index_manager
        agent = self._app.agent_manager.active_agent
        assert agent is not None, "No active agent"
        for col in self.collections:
            # index = im.get_index(col)
            # assert index is not None, f"Index {col} not found"
            if agent.is_attached_tool(col):
                sel_list.select(col)
            else:
                sel_list.deselect(col)


    @on(Button.Pressed, "#manage")
    def create_index_view(self) -> None:
        self.dismiss()
        self.app.push_screen(IndexScreen())

    @on(SelectionList.SelectionToggled)
    async def update_selected_index(self, s: SelectionList.SelectionMessage) -> None:
        self.log.debug("Selection toggled")
        # self.log.debug(s.selection_list.selected)

        # selected index: inject as tool
        if s.selection.value in s.selection_list.selected:
            self.dismiss()
            add_index_task = asyncio.create_task(
                self.add_index_as_tool(s.selection.value))

            def tool_added_cb():
                self.post_message(IndexAttached(s.selection.value))

            def notify_tool_change():
                self.post_message(FutureAgentTask(future=add_index_task))

            add_index_task.add_done_callback(lambda _: tool_added_cb())
            self.set_timer(0.05, notify_tool_change)





        # deselected: detach underlying tool if attached
        else:
            self.log.debug("deselected")
            # remove selected index as tool
            self.detach_index_tool(s.selection.value)
