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

import typing as t
from pathlib import Path

from textual.widgets import DirectoryTree as _DirectoryTree

TFilter = t.Callable[[Path], bool]

def not_hidden(path: Path) -> bool:
    """Filter out hidden files."""
    return not path.name.startswith(".")

class DirectoryTree(_DirectoryTree):

    def __init__(self, path: str | Path,
                 filter: TFilter | None = None, *args, **kwargs) -> None:
        self._filter = filter
        super().__init__(path, *args, **kwargs)

    def filter_paths(self, paths: t.Iterable[Path]) -> t.Iterable[Path]:
        """Filter paths to only show directories."""
        if self._filter is None:
            return paths
        return filter(self._filter, paths)
