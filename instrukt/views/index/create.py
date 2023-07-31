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
from pathlib import Path

from langchain.embeddings import HuggingFaceEmbeddings, OpenAIEmbeddings
from pydantic import ValidationError
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll, Container
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive, var
from textual.widgets import Button, Input, Label, LoadingIndicator, Select
from textual import events

from ...indexes.embeddings import EMBEDDINGS
from ...indexes.loaders import LOADER_MAPPINGS
from ...indexes.schema import Index
from ...tuilib.forms import FormControl, FormGroup, FormState, InvalidForm, ValidForm
from ...tuilib.modals.path_browser import PathBrowserModal
from ...tuilib.widgets import ActionBar
from ...types import InstruktDomNodeMixin

if t.TYPE_CHECKING:
    from textual.dom import DOMNode

    from ...tuilib.forms import FormValidity
    from .main import IndexScreen

DEFAULT_NEW_INDEX_MSG = "Make sure the data is correct before creating the collection"
CREATING_INDEX_MSG = "Creating index ..."


class CreateIndex(VerticalScroll, InstruktDomNodeMixin):
    """Index creation form.

    Creating a form using form control IDs as lookup keys for the
    Index BaseModal.__validators__.

    Form Validation
    ---------------
    FormGroups can be validated against a Pydantic model. It is recommended to use
    separate FormGroups for distinct sections of the form for better organization
    and clarity.

    Each FormGroup should be assigned a unique `id`.

    For FormControls with multiple controls, only a single element can be bound to the
    Pydantic model validator. This binding is achieved using the `name` attribute of
    the control.

    Additional Features
    -------------------
    A FormControl has options to include a label and to indicate if the field is
    required for form submission. These options provide more context to the user and
    enforce necessary inputs.
    """

    new_index: reactive[Index] = reactive(Index.construct())
    path: reactive[str] = reactive("")
    loader_type: reactive[str] = reactive("")
    embedding: reactive[str] = reactive("default")
    state = reactive(FormState.INITIAL, always_update=True)
    _pristine = var(True)
 
    class Status(Message):
        def __init__(self, state: FormState) -> None:
            super().__init__()
            self.state = state


    def on_mount(self):
        create_btn = self.query_one("Button#create")
        create_btn.variant = "success"   # type: ignore

    def update_state(self) -> None:
        """Compute final form state from sub FormGroup states."""
        forms = self.query(FormGroup)
        if all(form.state == FormState.VALID for form in forms):
            self.log.debug("state valid")
            self.state = FormState.VALID
        else:
            self.log.debug("state invalid")
            self.state = FormState.INVALID

    # generator for loader type tuples for the Select widget
    def get_loader_types(self):
        yield from [(v[0].__name__, k) for k, v in LOADER_MAPPINGS.items()]

    def get_embeddings(self):
        for k, v in EMBEDDINGS.items():
            if issubclass(v.fn, HuggingFaceEmbeddings):
                # get model name, try to split by `/` and get the last element
                model_name = v.kwargs["model_name"].split("/")[-1]
                assert model_name, "model name is empty"
                yield (f"{v.name}: {model_name}", k)
            elif issubclass(v.fn, OpenAIEmbeddings):
                model_field = OpenAIEmbeddings.__fields__.get("model")
                assert model_field is not None
                yield (f"{v.name}: {model_field.default}", k)
            else:
                yield (v.name, k)

    def compose(self) -> ComposeResult:
        # embeddings form group
        # TODO!: index embeddings form
        with VerticalScroll(classes="--container"):
            with FormGroup(border_title="embeddings",
                            name="embeddings",
                           state=FormState.VALID):
                yield FormControl(
                    Select(
                        self.get_embeddings(),
                        value=self.embedding,
                        classes="form-input",
                        id="embedding-fn",
                    ),
                    label="embedding function",
                    id="embedding",
                    required=True,
                )

            # collction creation form group
            with FormGroup(border_title="new collection details:", name="collection"):
                yield FormControl(
                    Input(classes="form-input", placeholder="collection name", name="name"),
                    label="Name",
                    required=True,
                )
                yield FormControl(
                    Input(
                        classes="form-input",
                        placeholder="A short description of the collection. Helpful for agents.",
                        name="description",
                    ),
                    label="Description",
                    id="description",
                )
                yield FormControl(
                    Horizontal(
                        Input(
                            classes="form-input",
                            placeholder="Path to the data source (file or directory)",
                            id="path-input",
                            name="path",
                        ),
                        Button("Browse", id="browse-path", variant="primary"),
                    ),
                    label="Path",
                    required=True,
                    id="path",
                )

            # data loader form group
            with FormGroup(border_title="data loader",
                           name="data-loader",
                           state=FormState.VALID):
                # yield FormControl(
                #         Container(
                #             Label("Loader type:"),
                #
                #             classes="control-row"
                #             ),
                #             Button("Scan"),
                #         )
                yield FormControl(
                    Horizontal(
                        Select(self.get_loader_types(), id="loader"),
                        Button("Scan", id="scan", disabled=True, variant="primary"),
                    ),
                    label="loader type:",
                )

            # with Horizontal(id="submit"):
            #     # message for the user to make sure the data is correct before starting
            #     # the embedding process which will consume API tokens
            #     yield Label(
            #         "Make sure the data is correct before creating the collection",
            #         classes="status-message",
            #     )
            #     # yield Button("Create",
            #     #              id="create-index",
            #     #              variant="warning",
            #     #              disabled=True)
            #     yield LoadingIndicator()

        yield ActionBar()

    def parent_form_group(self, elm: "DOMNode") -> t.Optional["DOMNode"]:
        return next(filter(lambda a: isinstance(a, FormGroup), elm.ancestors), None)

    def validate_parent_form(self, elm: "DOMNode"):
        form_group = self.parent_form_group(elm)
        if form_group is not None:
            self.validate_form(form_group)

    @on(Input.Changed)
    def input_changed(self, event: Input.Changed) -> None:
        event.stop()
        input = event.control

        if input.name is not None:
            self.log.debug(f"input changed: {input.name} -> {input.value}")
            setattr(self.new_index, input.name, input.value.strip())

        # when the form is pristine we done show form errors related to empty input 
        if input.name == "path":
            self._pristine = False
            self.path = input.value
            if len(input.value) == 0:
                self.validate_parent_form(input)



        if input.name == "description":
            t.cast(dict[str, t.Any], self.new_index.metadata)[
                "description"
            ] = input.value

    # handle path submission
    @on(Input.Submitted)
    def input_submitted(self, e: Input.Submitted) -> None:
        e.stop()
        # WARN: this is redundant it already happens in input changed
        # here we should just call the form validation logic
        input = e.input
        if len(input.value) > 0 and input.name is not None:
            setattr(self.new_index, input.name, input.value.strip())

        if input.name == "path":
            self.path = input.value
            self.validate_parent_form(input)
        self.update_state()

    @on(Select.Changed)
    def select_changed(self, e: Select.Changed) -> None:
        if e.control is not None:
            if e.control.id == "loader":
                self.new_index.loader_type = str(e.value)
            elif e.control.id == "embedding-fn":
                self.embedding = str(e.value)
                self.new_index.embedding = self.embedding
                self.validate_parent_form(e.control)

    @on(FormGroup.Blur)
    def form_group_blur(self, event: FormGroup.Blur) -> None:
        self.validate_form(event.form)
        self.update_state()

    def clear_formgroup_state(self, form: FormGroup):
        form.state = FormState.VALID
        # clear all control states for this form
        form_controls = form.query("FormControl").results()
        controls = chain(*[
                        t.cast(FormControl, c).inner_controls
                        for c in form_controls
                        ])   # type: ignore
        for c in controls:
            c.remove_class("error")
            c.border_subtitle = ""

    def handle_form_errors(self,
                           control: FormControl,
                           form: FormGroup,
                           invalid: "FormValidity"
                        ) -> None:
        assert invalid.error is not None
        errors = invalid.error.errors()
        for e in errors:
            locs: tuple[int | str, ...] = e.get("loc", tuple())
            for loc in locs:
                if loc == control.id:
                    form.state = FormState.INVALID
                    [c.add_class("error") for c in control.inner_controls]
                    # only set the control whose `name` is the same as control.id
                    # clen = len(control.inner_controls)
                    # self.log.debug(f"control: {control.id} clen: {clen}")
                    if len(control.inner_controls) == 1:
                        control.inner_controls[0].border_subtitle = e.get(
                            "msg"
                        )
                    elif len(control.inner_controls) > 1:

                        def set_subtitle(c):
                            if c.name == control.id:
                                c.border_subtitle = e.get("msg")

                        for c in control.inner_controls:
                            set_subtitle(c)




    def validate_form(self, form: FormGroup) -> None:
        """Validates the new index form"""
        self.log.debug("validating form")
        self.log.debug(self.new_index)
        self.clear_formgroup_state(form)
        form_controls = form.query(FormControl)

        if len(form_controls) == 0:
            return

        required_forms = [f for f in form_controls if f.required]

        # only do form validation for FormControls with required controls
        if len(required_forms) == 0:
            return

        #NOTE: if any required input is empty skip validation but marked full
        # form as invalid

        # if an input with name `path` == 0
        r_inputs = chain(*[f.query(Input) for f in required_forms])
        if self._pristine:
            if any([len(i.value) == 0 for i in r_inputs]):
                return


        valid_form = self.__validate_new_index()

        if not valid_form:
            self.log.debug("form is not valid")
            # form.state = FormState.INVALID
            # add error class to form group
            # form.add_class("error")
            # form.border_subtitle = "invalid form"

            # validate all form controls under this FormGroup
            for control in form_controls:
                assert isinstance(control, FormControl)
                try:
                    if control.id is None:
                        raise AttributeError

                    attr = getattr(self, control.id)

                    if attr is None or (control.id != "path" and attr == ""):
                        continue

                    # check if attr is reactive
                    if control.id not in self._reactives.keys():
                        raise AttributeError

                    # try to get validator for attr from Index
                    # attr_validators: t.Any = Index.__validators__[control.id]
                    # for v in attr_validators:
                    #     v.func(Index, attr)

                    # if control.id is in the `loc` key of the list valid.error.errrors
                    # set error class on control
                    self.handle_form_errors(control, form, valid_form)
                except (AttributeError, KeyError):
                    continue



    # TODO!: loading progress indicator
    def watch_state(self, state: FormState) -> None:
        self.log.warning(f"Full form state is {state}")
        self.set_classes(state.name.lower())
        if state == FormState.VALID:
            create_btn = self.screen.query_one("Button#create")
            create_btn.disabled = False

        elif state == FormState.PROCESSING:
            self.log.warning(f"total state is {state}")
            # submit_label = t.cast(Label, self.query_one("#submit Label"))
            # submit_label.renderable = CREATING_INDEX_MSG
            # submit_label.refresh()

            # create_btn = self.query_one("#create-index")
            # create_btn.display = False
            # self.query_one(LoadingIndicator).display = True
            # for form in self.query(FormGroup):
            #     form.display = False
        elif state == FormState.CREATED:
            self.log.warning(f"total state is {state}")
            self.reset_form()
        else:
            # self.log.warning(f"total state is {state}")
            # submit_label = t.cast(Label, self.query_one("#submit Label"))
            # submit_label.renderable = DEFAULT_NEW_INDEX_MSG
            # submit_label.refresh()

            self.query_one("Button#create").disabled = True

    def reset_form(self) -> None:
        self.new_index = Index.construct()
        self.path = ""
        # self.state = FormState.INITIAL
        inputs = self.query(Input)
        for input in inputs:
            input.value = ""

    def __validate_new_index(self) -> "FormValidity":
        """Validates the new_index form data"""
        try:
            valid_index = Index(**self.new_index.dict())
            self.new_index = valid_index
        except ValidationError as e:
            self.log.error(f"Invalid form data: {e}")
            return InvalidForm(e)

        return ValidForm()

    async def create_index(self) -> None:
        new_index = Index(**self.new_index.dict())
        self.log.info(f"Creating index\n{new_index}")
        self.state = FormState.PROCESSING
        idx_mg = self._app.context.index_manager
        await idx_mg.create(self._app.context, new_index)
        self.post_message(self.Status(FormState.CREATED))
        self.state = FormState.CREATED

    @on(Button.Pressed, "#browse-path")
    async def browse_path(self, event: Button.Pressed) -> None:
        """Show path browser."""

        def handle_path(path: Path | None) -> None:
            """Set path input value."""
            self.log.debug(f"selected path: {path}")
            if path is not None:
                input = t.cast(Input, self.query_one("Input#path-input"))
                input.value = str(path)
                t.cast("IndexScreen", self.screen).reset_form = False

        self.app.push_screen(PathBrowserModal(), handle_path)
