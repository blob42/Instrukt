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
from pathlib import Path

from textual.app import ComposeResult
from textual.reactive import var
from textual.screen import ModalScreen
from textual.widgets import Footer, MarkdownViewer


class ManualScreen(ModalScreen[None]):
    BINDINGS = [
        ("t", "toggle_table_of_contents", "TOC"),
        ("b", "back", "Back"),
        ("f", "forward", "Forward"),
        ("escape", "dismiss", "exit manual"),
    ]

    path = var(Path(__file__).parent.parent /  "docs/index.md")

    @property
    def markdown_viewer(self) -> MarkdownViewer:
        """Get the Markdown widget."""
        return self.query_one(MarkdownViewer)

    def compose(self) -> ComposeResult:
        yield Footer()
        yield MarkdownViewer()

    async def on_mount(self) -> None:
        self.markdown_viewer.focus()
        if not await self.markdown_viewer.go(self.path):
            #TODO!: return error message
            # self.exit(message=f"Unable to load {self.path!r}")
            self.log.error(f"could not load {self.path!r}")

    def action_toggle_table_of_contents(self) -> None:
        self.markdown_viewer.show_table_of_contents = (
            not self.markdown_viewer.show_table_of_contents
        )

    async def action_back(self) -> None:
        await self.markdown_viewer.back()

    async def action_forward(self) -> None:
        await self.markdown_viewer.forward()

