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

if t.TYPE_CHECKING:
    from .chroma import ChromaWrapper

TOOL_DESC_FULL = """Useful to lookup information about <{name}>: {tool_desc}."""
TOOL_DESC_SIMPLE = """Useful to lookup information about <{name}>."""
# TOOL_DESC_SUFFIX = """ NOTE: this tool is based on an LLM, do not summarize the user
# query. Enhance the query without losing context and nuances."""
TOOL_DESC_SUFFIX = """ [word-embedding db]""" 
def make_description(description: str | None,
                     index: "ChromaWrapper",
                     name: str) -> str:

    if description is None:
        if index.metadata is not None:
            desc = index.metadata.get("description")
            if desc is not None:
                description = TOOL_DESC_FULL.format(name=name, tool_desc=desc)
        else:
            description = TOOL_DESC_SIMPLE

    assert description is not None
    description.format(name=name)
    description += TOOL_DESC_SUFFIX
    return description
