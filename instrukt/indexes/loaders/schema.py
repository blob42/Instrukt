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
"""Schema used by loaders."""
import typing as t
from typing import NamedTuple

if t.TYPE_CHECKING:
    from langchain.text_splitter import TextSplitter

FileInfoMap = t.Dict[str, "FileInfo"]

Source = str

class LangSplitter(t.NamedTuple):
    lang: str
    """Langchain text splitter -> Language"""

    splitter: "TextSplitter"


class FileType(t.NamedTuple):
    mime: str
    ext: str | None
    encoding: str | None


class FileEncoding(NamedTuple):
    """File encoding as the NamedTuple."""

    encoding: str | None
    """The encoding of the file."""
    confidence: float
    """The confidence of the encoding."""
    language: str | None
    """The language of the file."""


class FileInfo(NamedTuple):
    ext: str | None = None
    """File extension"""

    mime: str | None = None
    """Mime type"""

    encoding: str | None = "utf8"
    """File encoding"""

    lang: str | None = None
    """language: both spoken or programming."""

    splitter: t.Optional["TextSplitter"] = None
    """Asociated splitter"""
