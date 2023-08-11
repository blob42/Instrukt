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
from asyncio.locks import Lock
import re
import typing as t
from dataclasses import dataclass
from itertools import chain
from typing import Optional, Sequence

from rich.console import RenderableType
from textual import events, on
from textual.app import ComposeResult, RenderResult
from textual.binding import Binding
from textual.containers import Container, Grid, VerticalScroll, Horizontal
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
from ...context import index_manager

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

    def new_index(self) -> None:
        """Activates the New entry"""
        lv = self.query_one(ListView)
        lv.index = len(lv) - 1
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
            lv = self.query_one(ListView)
            lv.action_select_cursor()
        else:
            self.screen.query_one(IndexConsole).minimize()
            self.screen.add_class("--create-form")
            # show the create index form

    @on(ListView.Selected)
    def collection_selected(self, event: ListView.Selected) -> None:
        if event.item.id == "new":
            self.screen.add_class("--create-form")
        else:
            self.screen.remove_class("--create-form")


class IndexDetails(AsyncDataContainer):

    def on_mount(self) -> None:
        self.border_title = "index details:"


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
        self.count = idx.count
        if isinstance(idx, ChromaWrapper):
            self.collection_type = "Chroma DB"
        else:
            self.collection_type = type(idx).__name__

class ConsoleHeader(Horizontal):
    
    minimized = var[bool](False)

    def compose(self) -> ComposeResult:
        self.label =  Label("\[c]onsole", classes="console--label")
        self.message =  Label(classes="console--msg")
        yield self.label
        yield self.message

    def update_label(self, content: RenderableType) -> None:
        self.label.update(content)

    def update_msg(self, content: RenderableType) -> None:
        self.message.update(content)


class IndexConsole(TextLog):

    minimized = var[bool](False)
    has_log = var[bool](False)

    def on_mount(self) -> None:
        self.minimize()
        self.call_later(self.begin_capture_print)

    def compose(self) -> ComposeResult:
        self.header = ConsoleHeader()
        yield self.header
        self.tl = TextLog(wrap=True, highlight=True)
        yield self.tl

    def watch_minimized(self, m: bool) -> None:
        if m and self.has_log:
            # self.border_title = "\[c]onsole [b yellow][/]"
            self.query_one(ConsoleHeader).update_label("\[c]onsole [b yellow][/]")
        else:
            self.query_one(ConsoleHeader).update_label("\[c]onsole")

    def watch_has_log(self, m: bool) -> None:
        if m:
            self.query_one(ConsoleHeader).update_label("\[c]onsole [b yellow][/]")
        else:
            self.query_one(ConsoleHeader).update_label("\[c]onsole")

    def on_print(self, event: events.Print) -> None:
        text = event.text
        text = text.strip()
        # clean up ansi escape sequences
        text = re.sub(ANSI_ESCAPE_RE, "", text, flags=re.MULTILINE)

        if len(text) > 0:
            self.tl.write(text, expand=True)
            self.has_log = True
            if self.minimized:
                self.open()

    def clear(self):
        self.has_log = False
        return self.tl.clear()

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

    def is_empty(self) -> bool:
        return len(self.tl.lines) == 0

    def update_msg(self, content: RenderableType) -> None:
        self.header.update_msg(content)

    def clear_msg(self) -> None:
        self.header.update_msg("")

    @on(events.ScreenResume)
    def on_resume(self, event: events.ScreenResume) -> None:
        self.begin_capture_print()

    @on(events.ScreenSuspend)
    def on_suspend(self, event: events.ScreenSuspend) -> None:
        self.end_capture_print()
        self.clear()
        self.minimize()


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

    @property
    def embedding(self) -> EmbeddingDetails:
        with index_manager() as im:
            return im.get_embedding_fn(self.name)

    @property
    def error(self) -> str:
        return self.embedding.extra.get("error", "")


class IndexEntry(Horizontal):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.classes = "entry"


class IndexInfo(Container, InstruktDomNodeMixin):

    _lock: asyncio.Lock = Lock()

    collection: reactive[Collection] = reactive(Collection("", "", {}))

    class Deleted(Message):
        pass

    def compose(self) -> ComposeResult:
        # yield IndexDetails()
        with IndexDetails(classes="--details --container"):
            yield IndexEntry(Label("Name:", classes="--label"),
                             FutureLabel(bind="{X.name}"))
            yield IndexEntry(Label("Count:", classes="--label"),
                             FutureLabel(bind="{X.count}"))
            with Horizontal(classes="entry"):
                yield Label("Type:", classes="--label")
                yield FutureLabel(bind="{X.type}")
            yield FutureLabel(label="Embeddings: ",
                              nospin=True,
                              bind="{X.error}",
                              classes="--padding-top-1")
            with Horizontal(classes="entry"):
                yield Label("Class:", classes="--label")
                yield FutureLabel(bind="{X.embedding.fn_short}")
            with Horizontal(classes="entry"):
                yield Label("Model:", classes="--label")
                yield FutureLabel(bind="{X.embedding.model_name}")

    async def watch_collection(self, collection: Collection) -> None:
        self.count = -1

        async def get_idx_details():
            async with self._lock:
                with index_manager() as im:
                    idx = await im.aget_index(self.collection.name)
                    assert idx is not None
                    return _IndexDetails(idx)

        self.query_one(AsyncDataContainer).future = asyncio.create_task(
            get_idx_details())

    async def action_delete_collection(self) -> None:
        idx_name = self.collection.name
        with index_manager() as im:
            await im.adelete_index(idx_name)
            self.post_message(self.Deleted())

    def clear(self) -> None:
        self.collection = Collection("", "", {})


class IndexScreen(Screen[t.Any], InstruktDomNodeMixin):

    BINDINGS = [
        ActionBinding("C", "create_index", "reate", btn_id="create",
                      variant="success"),
        ActionBinding("D", "delete_collection", "elete", btn_id="delete"),
        ActionBinding(
            "escape",
            "dismiss",
            "dismiss",
            key_display="esc",
        ),
        ActionBinding("n",
                      "new_index",
                      "ew_index",
                      btn_id="new_index",
                      key_display="n"),
        Binding("c", "toggle_console", "console", key_display="c")
    ]

    AUTO_FOCUS = "IndexList ListView"

    reset_form = reactive(True)

    def on_mount(self) -> None:
        t.cast('HeaderTitle',
               self.query_one("HeaderTitle")).text = "Index Management"

    async def action_create_index(self) -> None:
        self.query_one(IndexConsole).open()
        await self.query_one(CreateIndex).create_index()

    def action_toggle_console(self) -> None:
        self.query_one(IndexConsole).toggle_console()

    def action_delete_collection(self) -> None:
        idx_info = self.query_one(IndexInfo)
        self.call_next(idx_info.action_delete_collection)

    def action_new_index(self) -> None:
        self.query_one(IndexList).new_index()

    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield IndexList()
            with Grid(id="main"):
                yield IndexInfo()
                yield CreateIndex(id="add-index-form")
                yield IndexConsole(id="idx-console")
                yield ActionBar()

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
        idx_console.post_message(events.ScreenResume())

    @on(events.ScreenSuspend)
    def suspend_screen(self) -> None:
        idx_console = self.query_one(IndexConsole)
        idx_console.post_message(events.ScreenSuspend())

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

            #NOTE: auto close index console when switching to it ?
            # ic = self.query_one(IndexConsole)
            # self.set_timer(2, ic.minimize)

        if is_status_created(e):
            self.query_one(IndexConsole).clear_msg()
        #   ...

    @on(CreateIndex.Creating)
    def _creating_index(self) -> None:
        self.query_one(IndexConsole).update_msg("creating index ...")


    # def action_quit_index(self):
    #     self.dismiss()
    #     self.app.uninstall_screen(self.screen)
