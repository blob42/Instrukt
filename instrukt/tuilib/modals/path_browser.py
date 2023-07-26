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
"""Path browser modal screen."""


import typing as t
from textual import on
from textual.reactive import var
from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import DirectoryTree, Tree, Label, Button, Footer
from textual.containers import Container, Horizontal
from textual import events
from textual.css.query import NoMatches
from textual.binding import Binding, BindingType
from pathlib import Path

from ...types import InstruktDomNodeMixin
from ..widgets import ActionBar


class PathBrowserModal(ModalScreen[Path | None], InstruktDomNodeMixin):
    """A modal screen to browse the filesystem."""


    #NOTE: custom tree bindings 
    TREE_BINDINGS = [
                ("enter", "select", "select"),
                ("space", "toggle_node", "toggle node"),
            ]

    BINDINGS = [
            *TREE_BINDINGS,
            ("escape", "dismiss(None)", "dismiss"),
            ]


    AUTO_FOCUS = "DirectoryTree"

    path: var[Path] = var(Path.cwd())

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.dirtree = DirectoryTree(".")
        self.dirtree.border_title = "Select any file or directory to index:"

    def on_mount(self) -> None:
        for binding in self.TREE_BINDINGS:
            self.dirtree._bindings.bind(*binding)


    def compose(self) -> ComposeResult:
        with Container():
            yield self.dirtree
            with Horizontal(id="selected-path", classes="container"):
                yield Label("selected path:", classes="path--label")
                yield Label(f"\[ {self.path.resolve()} ]",
                            classes="path--selected",
                            id="selected-path")
            yield ActionBar()

    def action_toggle_node(self) -> None:
        self.dirtree.action_toggle_node()

    def action_select(self) -> None:
        self.dismiss(self.path)

    def watch_path(self, path: Path) -> None:
        try:
            lbl = t.cast(Label, self.query_one("Label#selected-path"))
            lbl.update(f"\[ {path} ]")
        except NoMatches:
            pass


    @on(Tree.NodeHighlighted)
    def _on_tree_node_highlighted(self, event: Tree.NodeHighlighted):
        dir_entry = event.node.data

        if dir_entry is None:
            return

        _path = dir_entry.path

        if not _path.is_absolute():
            _path = _path.resolve()
        _path = "~" / _path.relative_to(Path.home())

        self.path = _path


