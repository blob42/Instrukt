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
from rich.text import Text
from textual.app import RenderResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widget import Widget


class HeaderTitle(Widget):

    text: reactive[str] = reactive("")

    def render(self) -> RenderResult:
        text = Text(self.text, no_wrap=True, overflow="ellipsis")
        return text

class MenuWrapper(Container):
    """Main instrukt menu."""

    #TODO!: main app menu
    # def compose(self) -> ComposeResult:
    #     yield Button(label="≡", id="main")

class InstruktHeader(Widget):


    def compose(self):
        yield MenuWrapper()
        yield HeaderTitle()

    def on_mount(self) -> None:

        def set_title(title: str) -> None:
            self.query_one(HeaderTitle).text = title

        self.watch(self.app, "title", set_title)

