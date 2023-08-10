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
"""Console/ output capture and redirection."""

from abc import ABC, abstractmethod
from logging import Filter, Formatter, Handler, LogRecord
from typing import ClassVar, Optional


class ConsoleFilter(Filter, ABC):
    """Base filter class to use with output and log capture."""

    module: ClassVar[str]
    formatter: ClassVar[Formatter] = Formatter('%(message)s')

    def filter(self, record: LogRecord) -> bool:
        """Implements logging.Filter"""
        return record.name.startswith(self.module)


class SentenceTransformersFilter(ConsoleFilter):
    """Capture sentence_transofmers output."""
    module = "sentence_transformers"
