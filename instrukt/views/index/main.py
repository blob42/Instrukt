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
import asyncio
import re
import typing as t
from dataclasses import dataclass
from itertools import chain
from typing import Optional, Sequence

from textual import events, on
from textual.app import ComposeResult, RenderResult
from textual.binding import Binding
from textual.containers import Container, Grid, VerticalScroll
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive, var
from textual.screen import Screen
from textual.widgets import (
    Header,
    Label,
    ListItem,
    Static,
    TextLog,
)

from ..._logging import ANSI_ESCAPE_RE
from ...indexes.chroma import ChromaWrapper
from ...indexes.schema import Collection, EmbeddingDetails
from ...tuilib.forms import FormState
from ...tuilib.widgets.actionbar import ActionBar, ActionBinding
from ...tuilib.widgets.listview import ListView
from ...tuilib.widgets.spinner import AsyncDataContainer, FutureLabel
from ...types import InstruktDomNodeMixin
from .create import CreateIndex

if t.TYPE_CHECKING:
    from typing_extensions import Self

    from ...app import InstruktApp
    from ...indexes.manager import IndexManager
    from ...tuilib.widgets.header import HeaderTitle


class IndexCollectionItem(ListItem):

    def __init__(self, collection: Collection, *args: t.Any,
                 **kwargs: t.Any) -> None:

        super().__init__(*args, **kwargs)
        self.collection = collection


class IndexList(VerticalScroll, InstruktDomNodeMixin, can_focus=False):

    collections: reactive[Sequence[Collection]] = reactive([],
                                                           always_update=True)

    def fetch_collections(self) -> None:
        """Updates the collections list from the index manager.

        Call this method to refresh the list of collections.
        """
        index_manager = self._app.context.index_manager
        self.collections = index_manager.list_collections()

    def watch_collections(self) -> None:
        try:
            lv = self.query_one(ListView)
        except NoMatches:
            return

        col_names = [col.name for col in self.collections]
        for item in chain(lv.children):
            if isinstance(item, IndexCollectionItem):
                if item.name not in col_names:
                    item.remove()

        col_items = [
            item for item in chain(lv.children)
            if isinstance(item, IndexCollectionItem)
        ]
        for col in self.collections:
            if col.name not in [item.name for item in col_items]:
                col_item = IndexCollectionItem(col,
                                               Label(col.name),
                                               name=col.name)
                lv.mount(col_item, before=-1)

        if len(lv) > 1:
            # unhighlight the New button
            lv.query_one("ListItem#new").highlighted = False  # type: ignore
            lv.index = len(lv) - 2
            lv.action_select_cursor()
        elif lv.index == 0:
            lv.action_select_cursor()

    def compose(self) -> ComposeResult:
        self.fetch_collections()
        yield Label("Collections", classes="header")
        with ListView():
            for col in self.collections:
                yield IndexCollectionItem(col, Label(col.name), name=col.name)
            yield ListItem(Label("New"), id="new")

    @on(ListView.Highlighted)
    def collection_highlighted(self, event: ListView.Highlighted) -> None:

        if isinstance(event.item, IndexCollectionItem):
            self.screen.remove_class("--create-form")
            info = self.screen.query_one(IndexInfo)
            info.collection = event.item.collection
        else:
            # show the create index form
            self.screen.add_class("--create-form")


class IndexDetails(AsyncDataContainer):

    def on_mount(self) -> None:
        self.border_title = "index details:"

    def clear(self) -> None:
        self.log.warning("Not Implemented")


class BackupIndexDetails(Static, InstruktDomNodeMixin):

    collection: reactive[Collection] = reactive(Collection("", "", {}))
    collection_type = reactive("")
    count = reactive(-1)

    def on_mount(self) -> None:
        self.border_title = "index details:"

    def render(self) -> RenderResult:
        # if no collection is selected render nothing
        if len(self.collection.name) == 0:
            return ""

        embedding = self.embedding_fn
        return f"""
    Collection Name: {self.collection.name}
    Document Count: {"[dim]loading ..." if self.count < 0 else "[r]" + str(self.count)}[/]
    Type: {self.collection_type or "[dim]loading ...[/]"}

    [b]Embeddings:[/b]  {embedding.extra.get("error", "")}
    Function : {embedding.embedding_fn_cls} 
    Model: {embedding.model_name} 
        """

    @property
    def idx_manager(self) -> "IndexManager":
        return self._app.context.index_manager

    @property
    def embedding_fn(self) -> EmbeddingDetails:
        return self.idx_manager.get_embedding_fn(self.collection.name)

    def clear(self) -> None:
        self.collection = Collection("", "", {})
        self.collection_type = ""
        self.count = -1

    async def get_index(self) -> Optional[ChromaWrapper]:
        idx = await t.cast('InstruktApp',
                           self.app).context.index_manager.aget_index(
                               self.collection.name)
        return idx

    async def wwatch_collection(self, collection: Collection) -> None:
        self.count = -1
        idx = await self.get_index()
        if idx is None:
            return
        self.count = idx.count()
        if isinstance(idx, ChromaWrapper):
            self.collection_type = "Chroma DB"
        else:
            self.collection_type = type(idx).__name__


class IndexConsole(TextLog):

    minimized = var[bool](False)
    has_log = var[bool](False)

    def on_mount(self) -> None:
        self.begin_capture_print()
        self.border_title = "\[c]onsole"

    def watch_minimized(self, m: bool) -> None:
        if m and self.has_log:
            self.border_title = "\[c]onsole [b yellow][/]"
        else:
            self.border_title = "\[c]onsole"

    def on_print(self, event: events.Print) -> None:
        text = event.text
        text = text.strip()
        # clean up ansi escape sequences
        text = re.sub(ANSI_ESCAPE_RE, "", text, flags=re.MULTILINE)

        if len(text) > 0:
            self.write(text, expand=True)
            self.has_log = True

    def clear(self) -> "Self":
        self.has_log = False
        return super().clear()

    def on_click(self, event: events.Click) -> None:
        self.toggle_console()

    def toggle_console(self) -> None:
        self.open() if self.minimized else self.minimize()

    def minimize(self) -> None:
        self.add_class("--minimize")
        self.minimized = True

    def open(self) -> None:
        self.remove_class("--minimize")
        self.minimized = False


@dataclass(frozen=True)
class _IndexDetails:
    idx: ChromaWrapper

    @property
    def name(self) -> str:
        return self.idx.name

    @property
    def count(self) -> int:
        return self.idx.count

    @property
    def type(self) -> str:
        if isinstance(self.idx, ChromaWrapper):
            return "Chroma DB"
        else:
            return type(self.idx).__name__


class IndexInfo(Container, InstruktDomNodeMixin):

    collection: reactive[Collection] = reactive(Collection("", "", {}))

    class Deleted(Message):
        pass

    def compose(self) -> ComposeResult:
        # yield IndexDetails()
        with IndexDetails(classes="--details --container"):
            yield FutureLabel(label="name:", bind="{X.name}")
            yield FutureLabel(label="document count: ", bind="{X.count}")
            yield FutureLabel(label="vectorstore: ", bind="{X.type}")

    async def watch_collection(self, collection: Collection) -> None:
        self.count = -1

        async def get_idx_details():
            idx = await self._app.context.index_manager.aget_index(
                self.collection.name)
            assert idx is not None
            return _IndexDetails(idx)

        self.query_one(AsyncDataContainer).future = asyncio.create_task(
            get_idx_details())

    async def action_delete_collection(self) -> None:
        idx_name = self.query_one(IndexDetails).collection.name
        await self._app.context.index_manager.delete_index(idx_name)
        self.post_message(self.Deleted())


class IndexScreen(Screen[t.Any], InstruktDomNodeMixin):

    BINDINGS = [
        ActionBinding("C", "create_index", "create", variant="success"),
        ActionBinding("D", "delete_collection", "delete"),
        ActionBinding(
            "escape",
            "dismiss",
            "dismiss",
            key_display="esc",
        ),
        Binding("c", "toggle_console", "console", key_display="c")
    ]

    AUTO_FOCUS = "IndexList ListView"

    reset_form = reactive(True)

    def on_mount(self) -> None:
        t.cast('HeaderTitle',
               self.query_one("HeaderTitle")).text = "Index Management"

    def action_create_index(self) -> None:
        self.query_one(CreateIndex).create_index()

    def action_toggle_console(self) -> None:
        self.query_one(IndexConsole).toggle_console()

    def action_delete_collection(self) -> None:
        idx_info = self.query_one(IndexInfo)
        self.call_next(idx_info.action_delete_collection)

    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield IndexList()
            # yield Placeholer("progress bar")
            with Grid(id="main"):
                yield IndexInfo()
                yield CreateIndex(id="add-index-form")
                yield IndexConsole(id="idx-console", wrap=True, highlight=True)
                yield ActionBar()
        # with Grid(id="content"):
        #     yield Placeholder("indexes", id="list")
        #     yield Placeholder("index info", id="details")
        # yield Footer()

    @on(events.ScreenResume)
    def resume_screen(self) -> None:

        #only reset the form when not returning from modal
        if self.reset_form:
            # refresh the index list
            self.query_one(IndexList).fetch_collections()
            self.query_one(CreateIndex).reset_form()

        else:  # screen was resumed from an other modal
            self.reset_form = True

        # begin console capture
        idx_console = self.query_one(IndexConsole)
        idx_console.begin_capture_print()

    @on(events.ScreenSuspend)
    def suspend_screen(self) -> None:
        idx_console = self.query_one(IndexConsole)
        idx_console.end_capture_print()
        idx_console.clear()

    # def on_index_info_deleted(self, e: Message) -> None:
    #     e.stop()
    #     index_list = self.query_one(IndexList)
    #     index_list.fetch_collections()

    @on(IndexInfo.Deleted)
    @on(CreateIndex.Status)
    def msg_handler(self, e: Message) -> None:
        e.stop()

        def is_status_created(m: Message) -> bool:
            """Handle index created"""
            return isinstance(
                m, CreateIndex.Status) and m.state == FormState.CREATED

        if isinstance(e, IndexInfo.Deleted) or is_status_created(e):
            index_list = self.query_one(IndexList)
            self.call_later(index_list.fetch_collections)

            details = self.query_one(IndexDetails)
            details.clear()

            self.query_one(IndexConsole).minimize()

        # if is_status_created(e):
        #     # select last entry in list
        #     lv = self.query_one(ListView)
        #     lv.index = len(lv) - 1
        #     lv.action_select_cursor()

    @on(ListView.Selected)
    def collection_selected(self, event: ListView.Selected) -> None:
        if event.item.id != "new":
            self.query_one(CreateIndex).display = False
            self.query_one(IndexInfo).display = True
        else:
            # show the create index form
            self.query_one(CreateIndex).display = True
            self.query_one(IndexInfo).display = False

    # def action_quit_index(self):
    #     self.dismiss()
    #     self.app.uninstall_screen(self.screen)
