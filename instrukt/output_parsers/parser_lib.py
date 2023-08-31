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

import json
import re
from typing import Any
from rich.markdown import Markdown

from langchain.output_parsers.json import (
    parse_json_markdown as __lc_parse_json_markdown,
)
from rich.markdown import Markdown

REGEXES = {
    "default": r"```(json)?(.*?)```",

    # Use greedy matching to match the outermost code block
    "nested_json_code_block": r"```(json)?(.*)```"
}


def parse_json_md_langchain(text: str) -> dict[str, Any]:
    """Extract a json object from markdown markup (langchain default)."""
    return __lc_parse_json_markdown(text)


def parse_json_md_nested_code_block(text: str) -> dict[str, Any]:
    """Extract the outermost code block. Can accomodate nested code blocks."""
    match = re.search(REGEXES["nested_json_code_block"], text, re.DOTALL)

    if match is None:
        json_str = text
    else:
        json_str = match.group(2)

    json_str = json_str.strip()

    parsed = json.loads(json_str)

    return parsed

def get_rich_md(markup: str,
                sanitize_md: bool = False,
                **kwargs) -> Markdown:
    _markup = markup
    # pre sanitize output
    _markup = re.sub(r"\\n", "\n", markup, re.MULTILINE)
    _markup = re.sub(r"\\t", "\t", _markup, re.MULTILINE)
    _markup = re.sub(r"\\'", "'",  _markup, re.MULTILINE)
    _markup = re.sub(r'\\"', '\"', _markup, re.MULTILINE)

    # post sanitize output
    if sanitize_md:
        return sanitize_md_code(Markdown(_markup, **kwargs))

    return Markdown(_markup, **kwargs)

def sanitize_md_code(md: Markdown) -> Markdown:
    """Cleans out markdown source code fences from broken escape characters."""
    # ref https://github.com/executablebooks/markdown-it-py/tree/master/markdown_it/rules_block
    for token in md._flatten_tokens(md.parsed):
        print(repr(token.content))
        node_type = token.type
        tag = token.tag
        # matches fenced code block (```)
        if (tag in md.inlines and node_type == "fence"):
            token.content = re.sub(r"\\n", "\n", token.content, re.MULTILINE)
            token.content = re.sub(r"\\t", "\t", token.content, re.MULTILINE)
            token.content = re.sub(r"\\'", "'", token.content, re.MULTILINE)
            token.content = re.sub(r'\\"', '\"', token.content, re.MULTILINE)
    return md

