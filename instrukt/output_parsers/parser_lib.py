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

from typing import (Any)
import re
import json
from langchain.output_parsers.json import parse_json_markdown as __lc_parse_json_markdown

REGEXES = {
        "langchain_json_markdown": r"```(json)?(.*?)```",

        # Use greedy matching to match the outermost code block
        "nested_code_block": r"```(json)?(.*)```"

        }

def parse_json_md_langchain(text: str) -> dict[str, Any]:
    """Extract a json object from markdown markup (langchain default)."""
    return __lc_parse_json_markdown(text)

def parse_json_md_nested_code_block(text: str) -> dict[str,Any]:
    """Extract the outermost code block. Can accomodate nested code blocks."""
    match = re.search(REGEXES["nested_code_block"], text, re.DOTALL)

    if match is None:
        json_str = text
    else:
        json_str = match.group(2)

    json_str = json_str.strip()

    parsed = json.loads(json_str)

    return parsed

