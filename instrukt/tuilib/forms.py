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
from enum import Enum
from typing import Any

from rich.text import Text
from textual.app import ComposeResult
from textual import events
from textual.containers import Container
from textual.widget import Widget
from textual.widgets import Label, Input
from textual.message import Message



class FormGroup(Container):

    DEFAULT_CSS = """
    FormGroup {
        border: wide $foreground 40%;
        border-title-color: $text;
        padding: 0 2;
        height: auto;
        margin-right: 1;
    }

    FormGroup Input {
        width: auto;
        min-width: 30%;
    }
    """

    class Blur(Message):
        def __init__(self, form: 'FormGroup') -> None:
            self.form = form
            super().__init__()


    def __init__(self,
                 *args: Any,
                 border_title: str | Text = "",
                 border_subtitle: str | Text = "",
                 **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.border_title = border_title
        self.border_subtitle = border_subtitle

    def on_descendant_blur(self) -> None:
        self.post_message(self.Blur(self))



class FormControl(Container):

    DEFAULT_CSS = """
    FormControl {
        height: auto;
        margin: 1 0;
    }

    FormControl Label {
        margin: 0 1;
    }

    FormControl Input {
        width: auto;
        min-width: 30%;
        border: tall transparent;
    }

    FormControl Input:focus {
        border: tall transparent;
        border-bottom: tall $secondary;
    }
    """

    def __init__(self,
                 *children: Widget,
                 label: str | Text = "",
                 required: bool = False,
                 **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.label = label
        self.required = required
        self.__children = children

    def compose(self) -> ComposeResult:
        label = f"{self.label}"
        if self.required:
            label += " [b red]*[/]required"
        yield Label(label)
        yield from self.__children


class ValidForm:
    def __init__(self, value: bool = True, message: str | None = None) -> None:
        self.value = bool(value)
        self.message = message

    def __call__(self) -> "ValidForm":
        return self

    def __bool__(self) -> bool:
        return self.value

    def __eq__(self, other) -> bool:
        if isinstance(other, ValidForm):
            return (self.value == other.value) and (self.message == other.message)
        return self.value == bool(other)

InvalidForm = ValidForm(False)


class FormState(Enum):
    """Represent the state of the form"""
    INITIAL = 0
    INVALID = 1
    VALID = 2
    PROCESSING = 3
    CREATED = 4
