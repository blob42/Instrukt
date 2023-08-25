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
"""Document loader mappings."""
import typing as t

from langchain.document_loaders.parsers.pdf import PDFMinerParser
from langchain.document_loaders import (
    PDFMinerLoader,
    TextLoader,
)
from dataclasses import dataclass

from ...types import AnyDict

if t.TYPE_CHECKING:
    from langchain.document_loaders.base import BaseBlobParser

TLoaderType = t.Tuple[t.Type["BaseLoader"] | t.Type["AutoDirLoader"],
                      t.Optional[AnyDict], str | None]
#                            Parser class	opt parametrs for instance
TParserType = t.Tuple[t.Type["BaseBlobParser"], t.Optional[AnyDict]]

@dataclass
class PDF:
    loader = PDFMinerLoader
    parser = PDFMinerParser

class ParserMapping(t.NamedTuple):
    parser_cls: t.Type["BaseBlobParser"]
    options: AnyDict


PARSER_MAPPINGS: dict[str, ParserMapping] = {
        ".pdf": ParserMapping(PDF.parser, {})
        }

LOADER_MAPPINGS: dict[str, TLoaderType] = {
    ".txt": (TextLoader, {
        "autodetect_encoding": True
    }, "Text"),
    ".pdf": (PDF.loader, {}, "PDF with PdfMiner"),
    "._dir": (None, {}, None)
}
"""Document loader tuples in the form (loader_cls, loader_kwargs)"""
