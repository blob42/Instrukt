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
"""Keybindings Screen"""

from textual.containers import ScrollableContainer
from textual.widgets import Markdown, Header, Label, Static
from textual.screen import ModalScreen
from textual.app import ComposeResult
from rich.text import Text

# TODO: dynamically generate app bindings
# TODO: store bindings in config file

BINDING_TEXT = """
[b r] General [/]

Index Management	[b]I[/]
Dev Console		[b]D[/]
Help/Manual		[b]?[/]
Quit App		[b]Q[/]
Force Quit		[b]ctrl+c[/]
Focus On Prompt		[b]/ (slash)[/]

[b r] Prompt (focused) [/]

Stop Running Agent 	[b]ctrl+s[/]
History			[b]up / down[/]

[b r] Agent Conversation [/]

Copy Message		click on message

"""

class KeyBindingsScreen(ModalScreen[None]):

    BINDINGS = [
        ("escape", "dismiss", "dismiss"),
    ]

    def compose(self) -> ComposeResult:
        container = ScrollableContainer(
                Static(BINDING_TEXT, markup=True)
                )
        container.border_title = "Key Bindings"
        yield container
