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
from contextvars import copy_context
from functools import partial
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
from textual.validation import Function
from textual.widgets import Button, Input, Label, Pretty, Select
from textual.worker import Worker, WorkerFailed, WorkerState

from ...context import index_manager_var
from ...indexes.embeddings import EMBEDDINGS
from ...indexes.loaders import (
    LOADER_MAPPINGS,
    AutoDirLoader,
    src_by_lang,
)
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
from .console import ConsoleMessage

if t.TYPE_CHECKING:
    import contextvars

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


def valid_path(path: str) -> bool:
    p = Path(path).expanduser()
    return any((Path(p).is_file(), Path(p).is_dir()))


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

    new_index: var[Index] = var(Index.construct())
    path: reactive[str] = reactive("")
    state = reactive(FormState.INITIAL, always_update=True)
    _pristine = var(True)
    _current_work: Worker[t.Any] | None = None
    can_scan = var[bool](True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._debouncer = Debouncer(self.app, 0.1)

    class Status(Message):

        def __init__(self, state: FormState) -> None:
            super().__init__()
            self.state = state

    class Creating(Message):
        pass

    def update_state(self) -> None:
        """Compute final form state from sub FormGroup states."""
        self.log.debug("updating state")
        forms = self.query(FormGroup)
        if all(form.state == FormState.VALID for form in forms):
            self.log.debug("state valid")
            self.state = FormState.VALID
        else:
            self.log.debug("state invalid")
            self.state = FormState.INVALID
        self.log.debug(self.new_index)

    # generator for loader type tuples for the Select widget
    def get_loader_types(self):
        loader_types = []
        # loader is Tuple(cls, dict, str)
        for ext, loader in LOADER_MAPPINGS.items():
            name = loader[0].__name__
            if loader[2] is not None:
                name = loader[2]
            loader_types.append((name, ext))

        yield from loader_types
        # yield from [(v[0].__name__, k) for k, v in LOADER_MAPPINGS.items()]

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
                        value=self.new_index.embedding,
                        classes="form-input",
                        id="embedding-fn",
                    ),
                    label="embeddings function",
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
                        Input(classes="form-input",
                              placeholder=
                              "path to data [file | directory] (default to .)",
                              id="path-input",
                              name="path",
                              validators=[
                                  Function(valid_path, "path is not valid")
                              ]),
                        Button("Browse", id="browse-path", variant="default"),
                    ),
                    label="path",
                    required=True,
                    id="path",
                )

            # data loader form group
            with FormGroup(border_title="data loader",
                           name="data-loader",
                           id="data-loader",
                           state=FormState.VALID):
                yield FormControl(
                    Horizontal(
                        Select(self.get_loader_types(),
                               prompt="auto detect",
                               id="loader"),
                        Button("Scan",
                               id="scan",
                               disabled=True,
                               variant="primary"),
                    ),
                    label="loader type:",
                    id="loader-type",
                )
                yield FormControl(
                    Horizontal(
                        Input(
                            classes="form-input",
                            placeholder=
                            "custom `glob` for matching files (e.g. `**/*.py`)",
                            id="glob-input",
                            name="glob",
                        ), ),
                    label="path glob pattern",
                    id="glob",
                )
                with VerticalScroll(id="data-loader-details") as vs:
                    vs.can_focus = False
                    yield Label("detected content:")
                    yield Pretty(None)

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
            setattr(self.new_index, input.name, input.value.strip())

        # when the form is pristine we show form errors related to empty input
        if input.name == "path":
            self._pristine = False
            self.path = input.value

            if event.validation_result.is_valid:
                self.can_scan = True
            else:
                self.can_scan = False

            if len(input.value) == 0:
                self.validate_parent_form(input)

        if input.name == "description":
            t.cast(dict[str, t.Any],
                   self.new_index.metadata)["description"] = input.value

        if input.name == "glob" and len(input.value) == 0:
            self.new_index.glob = None

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
                if e.value is not None:
                    self.new_index.loader_type = str(e.value)
                else:
                    self.new_index.loader_type = None

            elif e.control.id == "embedding-fn":
                self.new_index.embedding = str(e.value)
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
                           invalid: "FormValidity[FormGroup]") -> None:
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
        if all(empty_inputs):
            return

        self.__validate_new_index(form)

    def watch_can_scan(self, v):
        if v:
            self.screen.query_one("Button#scan_data_btn").disabled = False
            self.screen.query_one("Button#scan").disabled = False
        else:
            self.screen.query_one("Button#scan_data_btn").disabled = True
            self.screen.query_one("Button#scan").disabled = True

    def validate_path(self, path: str) -> str:
        return str(Path(path).expanduser())

    # TODO!: loading progress indicator
    def watch_state(self, state: FormState) -> None:
        # self.log.warning(f"Full form state is {state}")
        self.set_classes(state.name.lower())
        if state == FormState.VALID:
            create_btn = self.screen.query_one("Button#create")
            create_btn.disabled = False

        # elif state == FormState.PROCESSING:
        #     self.log.debug(f"total state is {state}")
        elif state == FormState.CREATED:
            # self.log.debug(f"total state is {state}")
            self.reset_form()
        else:
            self.screen.query_one("Button#create").disabled = True

    def reset_form(self) -> None:
        self.new_index = Index.construct()
        self.path = ""
        inputs = self.query(Input)
        for input in inputs:
            input.value = ""
        self.state = FormState.INITIAL

    @work(thread=True,
          name="validate_new_index",
          exit_on_error=False)
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
    def _on_work_change(self, event: Worker.StateChanged) -> None:
        #TODO!: handle error state at app level
        # if event.worker.state == WorkerState.ERROR:
        #     self.log.error(f"worker {event.worker.name} failed")

        if self.work_success("validate_new_index", event):
            if event.worker.result is None:
                self.log.error(f"worker {event.worker.name} result is None")
                return

            self._on_new_index_validated(event.worker.result)

        if self.work_success("create_index", event):
            self.log.debug("index created work handler !")
            # successs means worker success

        if self.work_success("data_scan", event):
            doc_stats = event.worker.result
            self.query_one(Pretty).update(doc_stats)
            self.query_one("VerticalScroll.--container").scroll_end()
            console = self.screen.query_one("IndexConsole")
            console.remove_class("--loading")
            c_header = console.header
            c_header.progress.update(total=None, progress=0)
            c_header.progress.refresh()
            c_header.set_msg("")


        # clear loading state for cancelled and failed workers
        if event.worker.name != "validate_new_index":
            if event.worker.state == WorkerState.CANCELLED or \
                    event.worker.state == WorkerState.ERROR:

                self.screen.remove_class("--loading")  # type: ignore
                self.screen.query_one("IndexConsole").clear_msg().remove_class( "--loading")

            if event.worker.state == WorkerState.ERROR:
                self.post_message(ConsoleMessage(event.worker.error))

    async def create_index(self) -> None:
        """Create the index, this is a slow operation"""
        if self.state != FormState.VALID:
            return
        console = self.screen.query_one("IndexConsole")
        console.header.progress.update(total=None, progress=0)
        new_index = Index(**self.new_index.dict())
        self.log.info(f"Creating index\n{new_index}")
        self.post_message(self.Creating())
        self.state = FormState.PROCESSING
        ctx = copy_context()

        def _create_index_worker(ctx: 'contextvars.Context', new_index):
            im = ctx.run(index_manager_var.get)
            assert im is not None
            im.create(ctx, new_index)
            self.post_message(self.Status(FormState.CREATED))
            self.app.log("TODO: FormState.CREATED")

        worker = partial(_create_index_worker, ctx, new_index)
        self._current_work = self.app.run_worker(
            worker,
            thread=True,
            name="create_index",
            exclusive=True,
            description="create vectorstore index",
            exit_on_error=False)

    @on(Button.Pressed, "#browse-path")
    async def browse_path(self, event: Button.Pressed) -> None:
        """Show path browser."""

        def handle_path(path: Path | None) -> None:
            """Set path input value."""
            self.log.debug(f"selected path: {path}")
            if path is not None:
                input = t.cast(Input, self.query_one("Input#path-input"))
                input.value = self.new_index.path = self.path = str(path)
                self.call_next(self.validate_parent_form, input)
            t.cast("IndexScreen", self.screen).reset_form = False

        selected_path = t.cast(Input, self.query_one("Input#path-input")).value
        path = Path(selected_path).expanduser() if len(
            selected_path) > 0 else None
        path = path if path is not None and path.exists() else None
        self.app.push_screen(PathBrowserModal(path), handle_path)

    #REFACT:
    @on(Button.Pressed, "#scan, #scan_data_btn")
    async def scan_data(self, event: Button.Pressed | None = None):
        self.cancel_work()
        if not self.can_scan:
            return
        console = self.screen.query_one("IndexConsole")
        c_header = console.header
        console.minimize(True)
        console.add_class("--loading")
        c_header.progress.update(total=None)
        pbar_thread = console.pbar
        im = index_manager_var.get()
        assert im is not None
        loader = im.get_loader(self.path, self.new_index.loader_type)
        loader.pbar = pbar_thread
        if self.new_index.glob is not None:
            loader.glob = [self.new_index.glob]
        if not isinstance(loader, AutoDirLoader):
            return
        assert isinstance(loader, AutoDirLoader)

        c_header.set_msg("scanning data ...")  # type: ignore
        files = loader.detect_files()

        self._current_work = self.run_worker(lambda: src_by_lang(files, True),
                                             name="data_scan",
                                             thread=True,
                                             exclusive=True,
                                             exit_on_error=False)

    def cancel_work(self) -> None:
        if self._current_work is not None:
            self._current_work.cancel()
