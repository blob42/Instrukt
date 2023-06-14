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
"""Quit app modal"""

from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Button, Label
from textual.containers import Grid

class TestModalScreen(ModalScreen[None]):

    def compose(self) -> ComposeResult:
        yield Grid(
                Label("Do you really want to quit?", id="question"),
                Button("Yes", variant="error", id="quit"),
                Button("No", variant="primary", id="cancel"),
                id="dialog"
                )
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()
        elif event.button.id == "cancel":
            self.app.pop_screen()

