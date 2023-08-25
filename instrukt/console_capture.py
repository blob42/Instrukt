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
from logging import Filter, Formatter, LogRecord
from typing import ClassVar, Sequence


class ConsoleFilter(Filter, ABC):
    """Base filter class to use with output and log capture."""

    modules: ClassVar[Sequence[str]]
    formatter: ClassVar[Formatter] = Formatter('%(message)s')

    def __init__(self, *module_filters: str, **kwargs):
        super().__init__(**kwargs)
        self._module_filters = set([*module_filters])

    @property
    def module_filters(self):
        return set(self._module_filters).union(self.modules)

    @module_filters.setter
    def module_filters(self, val):
        self._module_filters = val

    

    def filter(self, record: LogRecord) -> bool:
        """Implements logging.Filter"""
        from .config import APP_SETTINGS
        if APP_SETTINGS.debug:
            return True
        return any(record.name.startswith(module) for module in self.module_filters)

    def __or__(self, other):
        new_filter = self.__class__()
        new_filter.module_filters = self.module_filters.union(other.module_filters)
        return new_filter

    def __and__(self, other):
        new_filter = self.__class__()
        new_filter.module_filters = self.module_filters.intersection(other.module_filters)
        return new_filter


class LangchainF(ConsoleFilter):
    """Capture langchain output."""
    modules = ( "langchain", )

class IndexCreationF(ConsoleFilter):
    modules = (
            "sentence_transformers",
            "instrukt.indexes",
            "pdfminer" )
