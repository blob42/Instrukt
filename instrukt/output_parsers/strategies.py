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
from .parser_lib import (
        parse_json_md_langchain,
        parse_json_md_nested_code_block,
        )

T = dict[str, Any]

def is_bare_json(text: str) -> T:
    """Tries to load as bare json"""
    return json.loads(text.strip())


def json_markdown(text: str) -> T:
    """Extract a json object from markdown markup (langchain default)."""
    return parse_json_md_langchain(text)


def fix_code_in_json(text):
    """Use the dark force."""
    # Step 1: Extract the code block and replace it with a placeholder
    pattern = r"```([^`]*?)```"
    match = re.search(pattern, text)
    if match:
        code_block = match.group(1)
        text = re.sub(pattern, "CODE_BLOCK_PLACEHOLDER", text, count=1)

        # Step 2: Escape the special characters in the code block
        escaped_code_block = (code_block.
                              replace("\n", "\\n")
                              .replace("\t", "\\t")
                              .replace("\"", "\\\""))

        # add backtick pairs to escaped code block
        escaped_code_block = "[BEGIN_CODE]" + escaped_code_block + "[END_CODE]"

        # Replace the placeholder in the original text with the escaped code block
        text = text.replace("CODE_BLOCK_PLACEHOLDER", escaped_code_block)

    return text

def fix_json_with_embedded_code_block(text: str, max_loop: int = 20) -> T:
    loop = 0
    while True:
        if loop > max_loop:
            raise ValueError("Max loop reached")
        try:
            text = fix_code_in_json(text)
            json.loads(text)
            break
        except json.JSONDecodeError as e:
            if text[e.pos] == '\n':
                text = text[:e.pos] + "\\n" + text[e.pos + 1:]
                text = text.replace("[BEGIN_CODE]", "```")
            else:
                raise
        finally:
            loop += 1
    final_text = text.replace("[END_CODE]", "```")
    return json.loads(final_text)



def json_nested_code_block(text: str) -> T:
    """Extract the outermost code block. Can accomodate nested code blocks."""
    return parse_json_md_nested_code_block(text)

def fallback(text: str) -> T:
    """Fallback strategy"""
    return {"action": "Final Answer", "action_input": text}

json_react_strategies = (
        (is_bare_json, lambda text: text.startswith("{")),
         (json_markdown, lambda text: text.find("```") != -1),
         (json_nested_code_block, lambda text: text.find("```") != -1),
         (fix_json_with_embedded_code_block, lambda text: text.find("```") != -1),
         (fallback, lambda text: True),
        )
