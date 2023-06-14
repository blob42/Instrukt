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
from itertools import chain


from textual import on
from textual import events
from textual.reactive import reactive
from textual.app import ComposeResult, RenderResult
from textual.containers import Container, Grid, VerticalScroll, Horizontal
from textual.screen import Screen
from textual.css.query import NoMatches
from textual.message import Message
from textual.widgets import (Header,
                             Footer,
                             Button,
                             Label,
                             ListItem,
                             Placeholder,
                             Static,
                             Label,
                             Input,
                             Select
                             )
from typing import Optional, Sequence
from .create import CreateIndex
from ...tuilib.forms import FormGroup, FormControl, FormState
from ...indexes.schema import Collection, Index
from ...indexes.chroma import ChromaWrapper
from ...tuilib.widgets.listview import ListView
from ...errors import IndexError
from ...types import InstruktDomNodeMixin


if t.TYPE_CHECKING:
    from ...app import InstruktApp
    from ...tuilib.widgets.header import HeaderTitle


class IndexCollectionItem(ListItem):
    def __init__(self,
                 collection: Collection,
                 *args: t.Any,
                 **kwargs: t.Any) -> None:

        super().__init__(*args, **kwargs)
        self.collection = collection

class IndexList(VerticalScroll):

    collections: reactive[Sequence[Collection]] = reactive([],
                                                           always_update=True)

    def fetch_collections(self) -> None:
        """Updates the collections list from the index manager.

        Call this method to refresh the list of collections.
        """
        index_manager = t.cast('InstruktApp', self.app).context.index_manager
        self.collections = index_manager.list_collections()

    def watch_collections(self) -> None:
        try:
            lv = t.cast(ListView, self.query_one(ListView))
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
                col_item = IndexCollectionItem(col, Label(col.name), name=col.name)
                lv.mount(col_item, before=-1)
                lv.index = len(lv) - 1



    def compose(self) -> ComposeResult:
        self.fetch_collections()
        yield Label("Collections", classes="header")
        with ListView():
            for col in self.collections:
                yield IndexCollectionItem(col, Label(col.name), name=col.name)
            yield ListItem(Label("New"), id="new")

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if isinstance(event.item, IndexCollectionItem):
            index_details = self.screen.query_one(IndexDetails)
            index_details.collection = event.item.collection



class IndexDetails(Static):

    collection: reactive[Collection] = reactive(Collection("","",{}))
    collection_type = reactive("")
    count = reactive(0)

    def render(self) -> RenderResult:
        return f"""
    Collection Name: {self.collection.name}
    Document Count: [r]{self.count}[/]
    Type: {self.collection_type}
        """

    def get_index(self) -> Optional[ChromaWrapper]:
        return t.cast('InstruktApp', self.app).context.index_manager.get_index(
            self.collection.name)

    def compute_count(self) -> int:
        idx_manager = self.app.context.index_manager  # type: ignore
        try:
            _col = idx_manager.get_index(self.collection.name)
            return _col.count()
        except ValueError:
            pass
        return 0

    def watch_collection(self, collection: Collection) -> None:
        idx = self.get_index()
        if isinstance(idx, ChromaWrapper):
            self.collection_type = "Chroma DB"
        else:
            self.collection_type = type(idx).__name__




class IndexInfo(Container, InstruktDomNodeMixin):

    class Deleted(Message):
        pass

    def compose(self) -> ComposeResult:
        yield IndexDetails()
        with Container(classes="action-bar"):
            yield Label("index actions:", classes="header")
            with Horizontal():
                yield Button("delete", id="delete", variant="warning")

    @on(Button.Pressed, "#delete")
    async def action_delete_collection(self, event: Button.Pressed) -> None:
        idx_name = self.query_one(IndexDetails).collection.name
        await self._app.context.index_manager.remove_index(idx_name)
        self.post_message(self.Deleted())



class IndexScreen(Screen[t.Any]):

    BINDINGS = [("escape", "dismiss", "Dismiss")]

    def on_mount(self) -> None:
        t.cast('HeaderTitle', self.query_one("HeaderTitle")).text = "Index Management"
        t.cast(Header, self.query_one("Header")).tall = True


    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield IndexList()
            # yield Placeholer("progress bar")
            with Grid(id="main"):
                yield IndexInfo()
                yield CreateIndex(id="add-index-form")
        # with Grid(id="content"):
        #     yield Placeholder("indexes", id="list")
        #     yield Placeholder("index info", id="details")
        # yield Footer()

    def on_screen_resume(self) -> None:
        try:
            self.query("Input").first().focus()
        except NoMatches:
            pass

        # refresh the index list
        self.query_one(IndexList).fetch_collections()
        self.query_one(CreateIndex).reset_form()


    # def on_index_info_deleted(self, e: Message) -> None:
    #     e.stop()
    #     index_list = self.query_one(IndexList)
    #     index_list.fetch_collections()

    @on(IndexInfo.Deleted)
    @on(CreateIndex.Status)
    def index_deleted(self, e: Message) -> None:
        e.stop()
        def is_status_created(m: Message) -> bool:
            return isinstance(
                m, CreateIndex.Status) and m.state == FormState.CREATED

        if isinstance(e, IndexInfo.Deleted) or is_status_created(e):
            index_list = self.query_one(IndexList)
            self.call_later(index_list.fetch_collections)




    @on(ListView.Selected)
    def collection_selected(self, event: ListView.Selected) -> None:
        if event.item.id != "new":
            self.query_one(CreateIndex).display = False
            self.query_one(IndexInfo).display = True
        else:
            self.query_one(CreateIndex).display = True
            self.query_one(IndexInfo).display = False
            self.dismiss

    # def action_quit_index(self):
    #     self.dismiss()
    #     self.app.uninstall_screen(self.screen)
