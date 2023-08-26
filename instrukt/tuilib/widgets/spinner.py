##
##  Copyright (c) 2023 Chakib Ben Ziane <contact@blob42.xyz>. All rights reserved.
##
##  SPDX-License-Identifier: AGPL-3.0-or-later
##
##  Adapted from the work of AstraLuma: 
##  https://github.com/AstraLuma/nat20/blob/trunk/pixelize/junk_drawer.py
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
"""All that spins."""
import asyncio
import contextvars
import json
import time
import typing as t
from typing import Any, Awaitable, Optional
import logging

import pkg_resources
from rich.console import RenderableType
from rich.spinner import Spinner
from rich.text import Text
from textual.reactive import reactive, var
from textual.widget import Widget
from textual.widgets import Label, Static

log = logging.getLogger(__name__)

SPINNERS = json.loads(
    pkg_resources.resource_string(__name__, 'spinners.json').decode('utf-8'))


class IntervalUpdater(Static):
    _renderable_object: RenderableType

    def update_rendering(self) -> None:
        self.update(self._renderable_object)

    def on_mount(self) -> None:
        self.interval_update = self.set_interval(1 / 60, self.update_rendering)


class SpinnerWidget(IntervalUpdater):
    """Basic spinner widget based on rich.spinner.Spinner"""
    def __init__(self, style: str, **kwargs) -> None:
        super().__init__("", **kwargs)
        self._renderable_object = Spinner(style)


class SpinningMixin(Widget):
    """
    Control speed with `auto_refresh`
    """
    #: See https://jsfiddle.net/sindresorhus/2eLtsbey/embedded/result/
    spinner = reactive[Optional[str]](None)

    _frames: list[str]

    def on_mount(self) -> None:
        if self.spinner is not None:
            self._spinner = self.spinner

    def spin(self) -> None:
        #backup spinner
        self.spinner = self._spinner

    def unspin(self) -> None:
        self.spinner = None

    def watch_spinner(self, spinner: str | None):
        if spinner is None:
            self.auto_refresh = None
            self._frames = []
        else:
            spininfo = SPINNERS[spinner]
            self.auto_refresh = spininfo['interval'] / 1000
            self._frames = spininfo['frames']

    def get_spin_frame(self) -> str | None:
        """
        Gets the current frame of the spinner, or returns None if spinning is
        disabled.
        """
        if self.auto_refresh is None or not self._frames:
            return None
        else:
            cur_frame = int(
                (time.monotonic() / self.auto_refresh) % len(self._frames))
            return self._frames[cur_frame]

class FutureSpinner(SpinningMixin):

    def __init__(self, spinner: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._spinner = spinner

    def track_future(self, fut: Any):
        """
        Set the spinner to track the given task/future/etc.

        This is not re-entrant; do not call multiple times. Instead use
        :func:`asyncio.gather`.

        Params:
            update: update the widget with the Future result when ready.
        """
        future = asyncio.ensure_future(fut)
        self.spin()
        self.refresh(layout=True)
        self.future = future

        @future.add_done_callback
        def done(fut):
            self.unspin()

        return future

    def render(self):
        if (frame := self.get_spin_frame()) is None:
            return ""
        else:
            text = Text(frame, style=self.text_style)
            return text


class FutureLabel(Label, SpinningMixin):

    _label: RenderableType
    markup = True

    def __init__(
            self,
            renderable: RenderableType = "",
            bind: str = "",  # fstring
            label: RenderableType = "",
            *,
            spinner: str = "aesthetic",
            nospin: bool = False,
            future: Awaitable[Any] | None = None,
            **kwargs) -> None:
        """

        Params:
            renderable: optional initial data, will be erased on the next data refresh
            bind: f-string binding in the form {X.path.to.data} (X == bound data)
            label: optional label prepended to the content
        """
        self.label = label
        self.bind = bind
        self.nospin = nospin
        content = self.concat_renderable(self.label, renderable)
        super().__init__(content, **kwargs)

        self.markup = True

        # backup spinner
        self._spinner = spinner
        if renderable == "":
            self.spin()

        elif future is not None:
            self.track_future(future)

    @staticmethod
    def concat_renderable(r1: RenderableType,
                          r2: RenderableType) -> RenderableType:
        return Text.from_markup(str(r1) + str(r2))

    @property
    def label(self) -> RenderableType:
        return self._label or ""

    @label.setter
    def label(self, renderable: RenderableType) -> None:
        if isinstance(renderable, str):
            if self.markup:
                self._label = Text.from_markup(renderable)
            else:
                self._label = Text(renderable, no_wrap=True)
        else:
            self._label = renderable

    def spin(self) -> None:
        if not self.nospin:
            self.spinner = self._spinner

    def track_future(self, fut: Any, update: bool = True) -> t.Awaitable[t.Any]:
        """
        Set the spinner to track the given task/future/etc.

        This is not re-entrant; do not call multiple times. Instead use
        :func:`asyncio.gather`.

        Params:
            update: update the widget with the Future result when ready.
        """
        future = asyncio.ensure_future(fut)
        self.spin()
        self.refresh(layout=True)
        self.future = future

        @future.add_done_callback
        def done(fut):
            self.spinner = None
            if update:
                self.update(fut.result())

        return future

    def render(self):
        if (frame := self.get_spin_frame()) is None:
            return super().render()
        else:
            text = Text.assemble(t.cast(Text, self.label), frame)
            text.expand_tabs(tab_size=4)
            text.stylize(self.text_style)
            return text

    def update(self, renderable: RenderableType = "") -> None:
        if isinstance(renderable, str):
            text = Text.assemble(t.cast(Text, self.label),
                                 Text.from_markup(renderable))
            text.expand_tabs(tab_size=4)
            self.renderable = text
        else:
            self.renderable = self.concat_renderable(self.label, renderable)
        self.refresh(layout=True)


class AsyncDataContainer(Static):
    """
    A class representing a data container where children can display async data.

    This class is designed to track a Future object and subsequently notify the children 
    objects when the data is ready. The class uses the asyncio library to handle 
    asynchronous operations. The asyncio.Future object represents a computation that 
    hasn’t completed yet.

    Attributes:
        ready (bool): Attribute to indicate when the data is ready.
        future (asyncio.Future | None): The Future object being tracked. 
        resolved (Any | None): Represents the resolved value from the Future object.

    """

    ready = var[bool](False)
    future = var[asyncio.Future[Any] | None](None)
    resolved = var[Any | None](None)

    def watch_future(self, fut: Any | None) -> None:
        if fut is None:
            return
        if fut is not None:
            self.ready = False
            self._track_future(fut)
            children = self.query(FutureLabel)
            for c in children:
                c.track_future(fut, False)

    def _on_future_ready(self,
                         fut: asyncio.Future,
                         context: contextvars.Context | None = None) -> None:
        """
        Method to be called when the Future object is ready.

        When the future object is ready, all children are updated with the result of the 
        future object. The resolved attribute is also set with the result.

        Args:
            fut (asyncio.Future): The Future object that is ready.
            context (contextvars.Context, optional): The context for the Future object. Defaults to None.

        Returns:
            None
        """
        try:
            self.resolved = fut.result()
            self.log.debug(f"{self} resolved to data: {self.resolved}")
            children = self.query(FutureLabel)
            #TEST:
            for c in children:
                fstring = f"f'{c.bind}'"
                res = eval(fstring, {}, {'X': self.resolved})
                c.update(res)

            self.ready = True
        except Exception as e:
            log.error(f"Error in {self}: {e}")
        finally:
            self.future = None

    def _track_future(self, fut: Any) -> asyncio.Future | None:
        """
        Private method to add the Future object to the asyncio event loop.

        When called, it ensures that the future is scheduled in the asyncio event loop. 
        It also adds a callback to be called when the Future object is ready.

        Args:
            fut (Any): The Future object to be tracked.

        Returns:
            asyncio.Future | None: The future after being added to the asyncio event
            loop. 
            Returns None if no future was initially set.
        """
        if self.future is None:
            return None
        future = asyncio.ensure_future(self.future)
        future.add_done_callback(self._on_future_ready)
        return future
