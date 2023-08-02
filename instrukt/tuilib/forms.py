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
from typing import Any, Sequence, TypeVar, Generic

from pydantic.error_wrappers import ValidationError
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Input, Select
from textual.css.query import DOMQuery
from textual import events, on


class FormState(Enum):
    """Represent the state of the form"""
    INITIAL = 0
    INVALID = 1
    VALID = 2
    PROCESSING = 3
    CREATED = 4


F = TypeVar('F')

class FormValidity(Generic[F]):

    def __init__(self,
                 form: F,
                 value: bool = True,
                 error: ValidationError | None = None) -> None:
        self.form = form
        self.value = bool(value)
        self.error = error

    def __call__(self) -> "FormValidity":
        return self

    def __bool__(self) -> bool:
        return self.value

    def __eq__(self, other) -> bool:
        if isinstance(other, FormValidity):
            return (self.value == other.value) and (self.error == other.error)
        return self.value == bool(other)


class InvalidForm(FormValidity[F]):

    def __init__(self, form: F, error: ValidationError) -> None:
        super().__init__(form, False, error)


class ValidForm(FormValidity[F]):

    def __init__(self, form: F) -> None:
        super().__init__(form, True)


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

    state = reactive(FormState.INITIAL)

    class Blur(Message):

        def __init__(self, form: "FormGroup", control: Widget | None) -> None:
            self.form = form
            self._control = control
            super().__init__()

        @property
        def control(self) -> Widget | None:
            return self._control

    def __init__(self,
                 *args: Any,
                 state: FormState = FormState.INITIAL,
                 border_title: str | Text = "",
                 border_subtitle: str | Text = "",
                 **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.state = state
        self.border_title = border_title
        self.border_subtitle = border_subtitle

    @on(events.DescendantBlur)
    def descendant_blur(self, event: events.DescendantBlur) -> None:
        self.post_message(self.Blur(self, event.control))

    def watch_state(self, state: FormState) -> None:
        if state == FormState.INVALID:
            self.add_class("error")
            self.border_subtitle = "invalid"
        else:
            self.remove_class("error")
            self.border_subtitle = ""


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

    @property
    def inner_controls(self) -> list[Widget]:
        assert self.parent is not None
        _controls = self.parent.query("FormControl *")
        def wanted(c):
            return type(c) in (Input, Select)
        return list(filter(wanted, _controls))

