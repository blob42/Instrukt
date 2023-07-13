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

from pydantic import ValidationError
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Button, Input, Label, LoadingIndicator, Select

from ...indexes.loaders import LOADER_MAPPINGS
from ...indexes.schema import Index
from ...tuilib.forms import FormControl, FormGroup, FormState, InvalidForm, ValidForm

DEFAULT_NEW_INDEX_MSG = "Make sure the data is correct before creating the collection"
CREATING_INDEX_MSG = "Creating index ..."


class CreateIndex(VerticalScroll):
    """Create Index Form"""

    new_index: reactive[Index] = reactive(Index.construct())
    path: reactive[str] = reactive("")
    loader_type: reactive[str] = reactive("")
    state = reactive(FormState.INITIAL)

    class Status(Message):

        def __init__(self, state: FormState) -> None:
            super().__init__()
            self.state = state

    # def __init__(
    #     self,
    #     *children: Widget,
    #     name: str | None = None,
    #     id: str | None = None,
    #     classes: str | None = None,
    #     disabled: bool = False,
    # ) -> None:
    # super().__init__(
    #         *children,
    #         name=name,
    #         id=id,
    #         classes=classes,
    #         disabled=disabled
    # )

    # generator for loader type tuples for the Select widget
    def get_loader_types(self):
        yield from [(v[0].__name__, k) for k, v in LOADER_MAPPINGS.items()]

    def compose(self) -> ComposeResult:
        with FormGroup(border_title="new collection details:"):
            yield FormControl(Input(classes="form-input",
                                    placeholder="collection name",
                                    name="name"),
                              label="Name",
                              required=True)
            yield FormControl(
                Input(
                    classes="form-input",
                    placeholder=
                    "A short description of the collection. Helpful for agents.",
                    name="description"),
                label="Description",
                id="description",
            )
            yield FormControl(Horizontal(
                Input(
                    classes="form-input",
                    placeholder="Path to the data source (file or directory)",
                    name="path"),
                Button("Browse", id="browse", variant="primary",
                       disabled=True),
            ),
                              label="Path",
                              required=True,
                              id="path")

        # with FormGroup(border_title="indexing parameters:"):
        #     yield Placeholder()
        with FormGroup(border_title="data loader", id="data-loader"):
            # yield FormControl(
            #         Container(
            #             Label("Loader type:"),
            #
            #             classes="control-row"
            #             ),
            #             Button("Scan"),
            #         )
            yield FormControl(Horizontal(
                Select(self.get_loader_types(), id="loader"),
                Button("Scan", id="scan", disabled=True, variant="primary"),
            ),
                              label="loader type:")

        with Horizontal(id="submit"):
            #message for the user to make sure the data is correct before starting
            # the embedding process which will consume API tokens
            yield Label(
                "Make sure the data is correct before creating the collection",
                classes="status-message")
            yield Button("Create",
                         id="create-index",
                         variant="warning",
                         disabled=True)
            yield LoadingIndicator()

    def on_input_changed(self, event: Input.Changed) -> None:
        event.stop()
        input = event.control
        if len(input.value) > 0 and input.name is not None:
            setattr(self.new_index, input.name, input.value.strip())
        if input.name == "path":
            self.path = input.value

        if input.name == "description":
            t.cast(dict[str, t.Any],
                   self.new_index.metadata)["description"] = input.value

    # handle path submission
    def on_input_submitted(self, e: Input.Submitted) -> None:
        e.stop()
        #WARN: this is redundant it already happens in input changed
        # here we should just call the form validation logic
        input = e.input
        if len(input.value) > 0 and input.name is not None:
            setattr(self.new_index, input.name, input.value.strip())
        if input.name == "path":
            self.path = input.value

        form_group = next(
            (a for a in input.ancestors if isinstance(a, FormGroup)), None)
        if form_group is not None:
            self.validate_form(form_group)

    @on(Select.Changed)
    def select_changed(self, e: Select.Changed) -> None:
        if e.control is not None and e.control.id == "loader":
            self.new_index.loader_type = str(e.value)

    def on_form_group_blur(self, event: FormGroup.Blur) -> None:
        self.validate_form(event.form)

    def validate_form(self, form: FormGroup) -> None:
        """Validates the new index form"""
        form_controls = form.query(FormControl)

        if len(form_controls) == 0:
            return

        required_forms = [f for f in form_controls if f.required]
        if len(required_forms) == 0:
            return

        # if any required input is empty skip validation
        r_inputs = chain(*[f.query(Input) for f in required_forms])
        if any([len(i.value) == 0 for i in r_inputs]):
            return

        valid = self.__validate_new_index()
        if not valid:
            self.state = FormState.INVALID
            # add error class to form group
            form.add_class("error")
            form.border_subtitle = "invalid form"

            # validate all form controls
            for control in form_controls:
                try:
                    if control.id is None:
                        raise AttributeError
                    attr = getattr(self, control.id)
                    if attr is None or attr == "":
                        continue
                    # check if attr is reactive
                    if control.id not in self._reactives.keys():
                        raise AttributeError

                    # try to get validator for attr from Index
                    attr_validators: t.Any = Index.__validators__[control.id]
                    for v in attr_validators:
                        v.func(Index, attr)

                except (AttributeError, KeyError):
                    continue

                except ValueError as e:
                    # set the control's Input error
                    try:
                        input = control.query_one(Input)
                        input.border_subtitle = str(e)
                        input.add_class("error")
                    except NoMatches:
                        pass
        else:
            self.state = FormState.VALID
            form.remove_class("error")
            form.border_subtitle = ""

            # clear subtitles from all inputs
            inputs = self.query(Input)
            for input in inputs:
                input.border_subtitle = ""

    def watch_state(self, state: FormState) -> None:
        self.set_classes(state.name.lower())
        if state == FormState.VALID:
            self.screen.query_one("#create-index").disabled = False
        elif state == FormState.PROCESSING:
            submit_label = t.cast(Label, self.query_one("#submit Label"))
            submit_label.renderable = CREATING_INDEX_MSG
            submit_label.refresh()
            # create_btn = self.query_one("#create-index")
            # create_btn.display = False
            # self.query_one(LoadingIndicator).display = True
            # for form in self.query(FormGroup):
            #     form.display = False
        elif state == FormState.CREATED:
            self.reset_form()
        else:
            submit_label = t.cast(Label, self.query_one("#submit Label"))
            submit_label.renderable = DEFAULT_NEW_INDEX_MSG
            submit_label.refresh()
            self.query_one("Button#create-index").disabled = True

    def reset_form(self) -> None:
        self.new_index = Index.construct()
        self.path = ""
        self.state = FormState.INITIAL
        inputs = self.query(Input)
        for input in inputs:
            input.value = ""

    def __validate_new_index(self) -> ValidForm:
        """Validates the new_index form data"""
        try:
            valid_index = Index(**self.new_index.dict())
            self.new_index = valid_index
        except ValidationError as e:
            self.log.error(f"Invalid form data: {e}")
            return InvalidForm()

        return ValidForm()

    #WIP:
    @on(Button.Pressed, '#create-index')
    async def create_index(self, event: Button.Pressed) -> None:
        new_index = Index(**self.new_index.dict())
        self.log.info(f"Creating index\n{new_index}")
        self.state = FormState.PROCESSING
        idx_mg = self.app.context.index_manager
        await idx_mg.create(self.app.context, new_index)
        self.post_message(self.Status(FormState.CREATED))
        self.state = FormState.CREATED
