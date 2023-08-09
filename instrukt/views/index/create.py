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
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.message import Message
from textual.reactive import reactive, var
from textual.timer import Timer
from textual.widgets import Button, Input, Select
from textual.worker import Worker

from ...indexes.embeddings import EMBEDDINGS
from ...indexes.loaders import LOADER_MAPPINGS
from ...indexes.schema import Index
from ...tuilib.forms import (
    FormControl,
    FormGroup,
    FormState,
    FormValidity,
    InvalidForm,
    ValidForm,
)
from ...tuilib.modals.path_browser import PathBrowserModal
from ...types import InstruktDomNodeMixin
from ...workers import WorkResultMixin

if t.TYPE_CHECKING:
    from textual.dom import DOMNode

    from .main import IndexScreen

class Debouncer:

    def __init__(self, target, wait: float) -> None:
        self.target = target
        self.wait = wait
        self.timer: Timer | None = None

    def call(self, fn, *args, **kwargs):

        def callback():
            # self.target.log("debounce")
            fn(*args, **kwargs)

        if self.timer is not None:
            self.timer.stop()
        else:
            self.timer = Timer(self.target,
                               self.wait,
                               callback=callback,
                               repeat=0)
        self.timer._start()


class CreateIndex(VerticalScroll,
                  InstruktDomNodeMixin,
                  WorkResultMixin,
                  can_focus=False):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._debouncer = Debouncer(self.app, 0.1)

    class Status(Message):

        def __init__(self, state: FormState) -> None:
            super().__init__()
            self.state = state

    def update_state(self) -> None:
        """Compute final form state from sub FormGroup states."""
        # self.log.debug("updating state")
        forms = self.query(FormGroup)
        if all(form.state == FormState.VALID for form in forms):
            # self.log.debug("state valid")
            self.state = FormState.VALID
        else:
            # self.log.debug("state invalid")
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
        embedding_choices = self.get_embeddings()
        with VerticalScroll(classes="--container") as vs:
            vs.can_focus = False
            with FormGroup(border_title="embeddings",
                           name="embeddings",
                           state=FormState.VALID):
                yield FormControl(
                    Select(
                        embedding_choices,
                        value=self.embedding,
                        classes="form-input",
                        id="embedding-fn",
                    ),
                    label="embedding function",
                    id="embedding",
                    required=True,
                )

            # collction creation form group
            with FormGroup(border_title="new collection details:",
                           name="collection"):
                yield FormControl(
                    Input(classes="form-input",
                          placeholder="collection name",
                          name="name"),
                    label="name",
                    id="name",
                    required=True,
                )
                yield FormControl(
                    Input(
                        classes="form-input",
                        placeholder=
                        "A short description of the collection. Helpful for agents.",
                        name="description",
                    ),
                    label="description",
                    required=True,
                    id="description",
                )
                yield FormControl(
                    Horizontal(
                        Input(
                            classes="form-input",
                            placeholder=
                            "path to the data source (file or directory)",
                            id="path-input",
                            name="path",
                        ),
                        Button("Browse", id="browse-path", variant="default"),
                    ),
                    label="path",
                    required=True,
                    id="path",
                )

            # data loader form group
            with FormGroup(border_title="data loader",
                           name="data-loader",
                           state=FormState.VALID):
                yield FormControl(
                    Horizontal(
                        Select(self.get_loader_types(), id="loader"),
                        Button("Scan",
                               id="scan",
                               disabled=True,
                               variant="primary"),
                    ),
                    label="loader type:",
                )

    def parent_form_group(self, elm: "DOMNode") -> t.Optional["DOMNode"]:
        return next(filter(lambda a: isinstance(a, FormGroup), elm.ancestors),
                    None)

    def validate_parent_form(self, elm: "DOMNode"):
        form_group = t.cast(FormGroup, self.parent_form_group(elm))
        if form_group is not None:
            self.validate_form(form_group)

    @on(Input.Changed)
    def input_changed(self, event: Input.Changed) -> None:
        event.stop()
        input = event.control

        if input.name is not None:
            # self.log.debug(f"input changed: {input.name} -> {input.value}")
            setattr(self.new_index, input.name, input.value.strip())

        # when the form is pristine we done show form errors related to empty input
        if input.name == "path":
            self._pristine = False
            self.path = input.value
            if len(input.value) == 0:
                self.validate_parent_form(input)

        if input.name == "description":
            t.cast(dict[str, t.Any],
                   self.new_index.metadata)["description"] = input.value

    # handle path submission
    @on(Input.Submitted)
    def input_submitted(self, e: Input.Submitted) -> None:
        e.stop()
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
    def validate_form_on_blur(self, event: FormGroup.Blur) -> None:
        # self._debouncer.call(self.validate_form, event.form)
        self.validate_form(event.form)

    def clear_formgroup_state(self, form: FormGroup):
        form.state = FormState.VALID

        # clear all control states for this form
        form_controls = form.query("FormControl").results()
        for fc in form_controls:
            fc.remove_class("error")
            t.cast(FormControl, fc).unset_error()

        # inner controls (Input, Select ...)
        # controls = chain(*[
        #                 t.cast(FormControl, c).inner_controls
        #                 for c in form_controls
        #                 ])   # type: ignore

    def handle_form_errors(self, control: FormControl, form: FormGroup,
                           invalid: "FormValidity") -> None:
        assert invalid.error is not None
        errors = invalid.error.errors()
        for e in errors:
            locs: tuple[int | str, ...] = e.get("loc", tuple())
            for loc in locs:
                if loc == control.id:
                    form.state = FormState.INVALID
                    control.add_class("error")
                    # only set the control whose `name` is the same as control.id
                    # clen = len(control.inner_controls)
                    # self.log.debug(f"control: {control.id} clen: {clen}")

                    control.set_error(e.get("msg", ""))

                    # if len(control.inner_controls) == 1:
                    #     control.inner_controls[0].border_subtitle = e.get(
                    #         "msg"
                    #     )
                    # elif len(control.inner_controls) > 1:
                    #
                    #     def set_subtitle(c):
                    #         if c.name == control.id:
                    #             c.border_subtitle = e.get("msg")
                    #
                    #     for c in control.inner_controls:
                    #         set_subtitle(c)

    def validate_form(self, form: FormGroup) -> None:
        """Validates the new index form"""
        # self.log.debug("validating form")
        self.log.debug(self.new_index)

        #FIX: only clear the controls wihtout errors otherwise there is a flicker
        # on the controls which have the same error
        self.clear_formgroup_state(form)
        form_controls = form.query(FormControl)

        # if all formcontrols are empty return

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

        def is_empty(i):
            return len(i.value) == 0

        # if all inputs are empty
        empty_inputs = map(lambda i: len(i.value) == 0,
                           chain(*[fc.query(Input) for fc in form_controls]))
        # if empty_inputs is not empty
        if any(empty_inputs) and all(empty_inputs):
            return

        self.__validate_new_index(form)

    # TODO!: loading progress indicator
    def watch_state(self, state: FormState) -> None:
        # self.log.warning(f"Full form state is {state}")
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

            self.screen.query_one("Button#create").disabled = True

    def reset_form(self) -> None:
        self.new_index = Index.construct()
        self.path = ""
        inputs = self.query(Input)
        for input in inputs:
            input.value = ""
        self.state = FormState.INITIAL

    @work(exclusive=True, thread=True, name="validate_new_index")
    def __validate_new_index(self, form: FormGroup) -> FormValidity[FormGroup]:
        """Validates the new_index form data"""
        try:
            valid_index = Index(**self.new_index.dict())
            self.new_index = valid_index
        except ValidationError as e:
            self.log.error(f"Invalid form data: {e}")
            return InvalidForm(form, e)

        return ValidForm(form)

    def _on_new_index_validated(self, valid: FormValidity[FormGroup]):
        if not valid:
            # self.log.debug("form is not valid")

            # validate all form controls under this FormGroup
            form_controls = valid.form.query(FormControl)
            for control in form_controls:
                assert isinstance(control, FormControl)
                try:
                    if control.id is None:
                        raise AttributeError

                    # attr = getattr(self, control.id)
                    #
                    # if attr is None:
                    #     continue

                    # # check if attr is reactive
                    # if control.id not in self._reactives.keys():
                    #     raise AttributeError

                    # try to get validator for attr from Index
                    # attr_validators: t.Any = Index.__validators__[control.id]
                    # for v in attr_validators:
                    #     v.func(Index, attr)

                    # if control.id is in the `loc` key of the list valid.error.errrors
                    # set error class on control
                    self.handle_form_errors(control, valid.form, valid)
                except (AttributeError, KeyError):
                    continue
        self._debouncer.call(self.update_state)

    @on(Worker.StateChanged)
    def _on_work_done(self, event: Worker.StateChanged) -> None:

        if self.work_success("validate_new_index", event):
            if event.worker.result is None:
                self.log.error(f"worker {event.worker.name} result is None")
                return

            self._on_new_index_validated(event.worker.result)

        # if self.work_success("create_index", event):
        # self.log.debug("index created work handler !")
        # successs means worker success

    @work(exclusive=True, thread=True)
    async def create_index(self) -> None:
        """Create the index, this is a slow operation"""
        if self.state != FormState.VALID:
            return
        new_index = Index(**self.new_index.dict())
        self.log.info(f"Creating index\n{new_index}")
        self.state = FormState.PROCESSING
        idx_mg = self._app.context.index_manager
        #TODO!: better notification ux
        notif = self.app.call_from_thread(self.notify,
                                          "creating index ...",
                                          timeout=9999)
        await idx_mg.create(self._app.context, new_index)
        self.post_message(self.Status(FormState.CREATED))
        self.app.call_from_thread(self.app.unnotify, notif)

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
