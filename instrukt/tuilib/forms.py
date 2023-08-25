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
from typing import Any, Generic, TypeVar

from pydantic.error_wrappers import ValidationError
from rich.text import Text
from textual import events, on
from textual.app import ComposeResult
from textual.containers import Container
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input, Label, Select


class FormState(Enum):
    """Represent the state of the form"""
    INITIAL = 0
    INVALID = 1
    VALID = 2
    PROCESSING = 3
    CREATED = 4


F = TypeVar('F')

#REFACT: use textual Input validator
class FormValidity(Generic[F]):

    def __init__(self,
                 form: F,
                 value: bool = True,
                 error: ValidationError | None = None) -> None:
        self.form = form
        self.value = bool(value)
        self.error = error

    def __call__(self) -> "FormValidity[F]":
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


# class FormGroup(Container, can_focus=True):
class FormGroup(Container):

    DEFAULT_CSS = """
    FormGroup {
        border-top: wide $foreground 20%;
        border-title-color: $text;
        padding: 0 2;
        height: auto;
        margin-right: 1;
    }

    FormGroup Input {
        width: auto;
        min-width: 30%;
        margin-top: 0;
    }

    FormGroup.error {
        border-top: wide $error;
    }
    """

    state = reactive(FormState.INITIAL)
    collapsed = reactive(False)

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
        self._collapsed = False

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

    # @on(events.Click)
    # def toggle_collapse(self, e: events.Click) -> None:
    #     if not self._collapsed:
    #         self._collapsed = True
    #         self.set_styles("height: 0;")
    #     else:
    #         self._collapsed = False
    #         self.set_styles("height: auto;")

    # def watch_collapsed(self, collapsed: bool) -> None:
    #     if collapsed:
    #         self.add_class("--collapsed")
    #     else:
    #         self.remove_class("--collapsed")

    @on(events.Focus)
    def uncollapse(self, event: events.Focus) -> None:
        if self.collapsed:
            self.collapsed = False

        for sib in self.siblings:
            sib.collapsed = True


class FormControl(Container):

    DEFAULT_CSS = """
    FormControl {
        height: auto;
        margin: 1 0;
        border-bottom: solid $panel;
    }

    FormControl Label {
        margin: 0 1;
        color: $text-muted;
    }

    FormControl Input {
        width: auto;
        min-width: 30%;
        border: none;
    }

    FormControl Input:focus {
        border: none;
        border-right: inner $warning;
        border-left: inner $warning;
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
        self.lbl = Label(self._build_label())

    def _build_label(self, err: str | None = None) -> str:
        label = f"{self.label}"
        if self.required and err is None:
            label += " [b light_coral]*[/]required"
        elif self.required and err:
            label += f" [yellow] {err}[/]"
        return label

    def compose(self) -> ComposeResult:
        yield self.lbl
        yield from self.__children

    def set_error(self, msg: str) -> None:
        self.lbl.update(self._build_label(err=msg))

    def unset_error(self) -> None:
        self.lbl.update(self._build_label())

    @property
    def inner_controls(self) -> list[Widget]:
        """Return inner controls of the form control"""
        assert self.parent is not None
        _controls = self.parent.query("FormControl *")

        def wanted(c):
            return type(c) in (Input, Select)

        return list(filter(wanted, _controls))
