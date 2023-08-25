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
"""Module for progress bars"""

import logging
from contextlib import contextmanager
from unittest.mock import patch

import tqdm
from textual.widgets import ProgressBar

from ...types import ProgressProtocol
from ...messages.indexes import IndexProgress

log = logging.getLogger(__name__)


class ProgressBarWrapper(ProgressProtocol):
    """ Wrapper for Textual ProgressBar that simulates tqdm `update()`.

    It implements the functions required by the ProgressProtocol abstract base class.
    It is used to simulate the 'tqdm' progress bar while using the textual ProgressBar
    to do the actual updates.

    Attributes:
        progress (ProgressBar): A ProgressBar object.

    .. note:: This class is part of the ProgressProtocol abstract base class.
    .. seealso:: ProgressBar class
    """

    def __init__(self, progress: ProgressBar):
        self.progress = progress

    def update(self, progress: int):
        """
        Simulates the 'tqdm' progress bar. The function calls the 'advance' function of
        the ProgressBar object. This method is thread safe. 

        Args:
            progress (int): The progress value.
        """
        self.progress.app.call_from_thread(self.progress.advance, progress)

    @contextmanager
    def patch_tqdm_update(self):
        """Patches tqdm.tqdm.update to call the wrapped ProgressBar.advance function."""
        original_update = tqdm.tqdm.update
        with patch('tqdm.tqdm.update', autospec=True) as tqdm_update:

            def side_effect(self_arg, n):

                self.progress.app.call_from_thread(self.progress.update,
                                                   total=self_arg.total,
                                                   advance=n)

                return original_update(self_arg, n)

            tqdm_update.side_effect = side_effect

            yield

    def update_pbar(self, *args, **kwargs):
        """
        Updates the wrapped ProgressBar object. The function calls the 'update' function
        of the ProgressBar object. This method is thread safe.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        self.progress.app.call_from_thread(self.progress.update, *args,
                                           **kwargs)

    def update_msg(self, msg: str) -> None:
        #post_message is thread safe
        self.progress.app.post_message(IndexProgress(msg))

    @property
    def total(self) -> float | None:
        """Textual ProgressBar.total"""
        return self.progress.total

    @total.setter
    def total(self, total: float | None) -> None:
        self.progress.total = total
