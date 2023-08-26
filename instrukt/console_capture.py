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

from abc import ABC
import re
from logging import Filter, Formatter, LogRecord
from typing import ClassVar, Sequence


class ConsoleFilter(Filter, ABC):
    """Base filter class to use with output and log capture."""

    modules: ClassVar[Sequence[str]] = []
    formatter: ClassVar[Formatter] = Formatter('%(message)s')
    patterns: ClassVar[Sequence[re.Pattern]] = []

    def __init__(self,
                 module_filters: list[str] = [],
                 pattern_filters: list[str] = [],
                 **kwargs):
        super().__init__(**kwargs)
        self._module_filters = set(module_filters)
        self._pattern_filters = set(pattern_filters)

    @property
    def module_filters(self):
        return set(self._module_filters).union(self.modules)

    @module_filters.setter
    def module_filters(self, val):
        self._module_filters = val

    @property
    def pattern_filters(self):
        return set(self._pattern_filters).union(self.patterns)

    @pattern_filters.setter
    def pattern_filters(self, val):
        self._pattern_filters = val

    def match(self, record: LogRecord) -> bool:
        """Check if record should be filtered."""
        return any(p.match(record.getMessage())
                   for p in self.pattern_filters)

    def filter(self, record: LogRecord) -> bool:
        """Implements logging.Filter"""
        from .config import APP_SETTINGS
        if APP_SETTINGS.debug:
            return True
        return self.match(record) or self._filter(record)

    def _filter(self, record: LogRecord) -> bool:
        return any(record.name.startswith(module)
                   for module in self.module_filters)

    def __or__(self, other):
        new_filter = ConsoleFilter(module_filters=self.module_filters,
                                   pattern_filters=self.pattern_filters)
        new_filter.module_filters = new_filter.module_filters.union(
            other.module_filters)
        new_filter.pattern_filters = new_filter.pattern_filters.union(
            other.pattern_filters)
        return new_filter

    def __and__(self, other):
        new_filter = ConsoleFilter(module_filters=self.module_filters,
                                   pattern_filters=self.pattern_filters)
        new_filter.module_filters = new_filter.module_filters.intersection(
            other.module_filters)
        new_filter.pattern_filters = new_filter.pattern_filters.intersection(
            other.pattern_filters)
        return new_filter


class ErrorF(ConsoleFilter):
    """Matches errors and exceptions"""
    # match error | exception anywhere case insensitive
    patterns = (
            re.compile(r".*(error|exception).*", re.IGNORECASE),
            )


class LangchainF(ConsoleFilter):
    """Capture langchain output."""
    modules = ( "langchain", )

class IndexCreationF(ConsoleFilter):
    modules = (
            "sentence_transformers",
            "instrukt.indexes",
            "pdfminer" )
