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
from datetime import datetime
from typing import Any

from ..config import APP_SETTINGS
from .parser_lib import (
    parse_json_md_langchain,
    parse_json_md_nested_code_block,
)
from .strategy import Strategy


class OutputParserException(ValueError):
    pass

T = dict[str, Any]


def is_bare_json(text: str) -> T:
    """Tries to load as bare json"""
    return json.loads(text.strip())


def json_markdown(text: str) -> T:
    """Extract a json object from markdown markup (langchain default)."""
    return parse_json_md_langchain(text)


def fix_code_in_json(text):
    """Use the dark force."""
    # extract the code block and replace it with a placeholder
    pattern = r"```([^`]*?)```"
    match = re.search(pattern, text)
    if match:
        code_block = match.group(1)
        text = re.sub(pattern, "CODE_BLOCK_PLACEHOLDER", text, count=1)

        # escape the special characters in the code block
        escaped_code_block = (code_block.replace("\n", "\\n").replace(
            "\t", "\\t").replace("\"", "\\\""))

        # add backtick pairs to escaped code block
        escaped_code_block = "[BEGIN_CODE]" + escaped_code_block + "[END_CODE]"

        # replace the placeholder in the original text with the escaped code block
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
                #NOTE: END_CODE must replaced in the end of the loop
            else:
                raise
        finally:
            loop += 1
    final_text = text.replace("[END_CODE]", "```")
    return json.loads(final_text)


def json_nested_code_block(text: str) -> T:
    """Extract the outermost code block. Can accomodate nested code blocks."""
    return parse_json_md_nested_code_block(text)


def json_recover_final_answer(text: str) -> T:
    """A last resort strategy when the final answer json 'output' field is a multiline
    string that breaks the json parser.


    Alrorithm:
        - text must match `"Final Answer"`
        - get rid of all text preceding `"action_input" ?:`
        - get rid of the last `}` in the text
        - put the result in a new json object and return it

    """
    if text.find("Final Answer") == -1:
        raise OutputParserException("Text does not contain 'Final Answer'")

    # get rid of all text preceding `"action_input" ?:`
    prefix_pattern = r".*\"action_input\" *: *\""
    res = re.sub(prefix_pattern, "", text, count=1, flags=re.DOTALL)

    # get rid of the json tail
    suffix_pattern = r"\"[ \n]*\}[ \n]*"
    res = re.sub(suffix_pattern, "", res, count=1, flags=re.DOTALL)
    return dict(action="Final Answer", action_input=res)




def fallback(text: str) -> T:
    """Fallback strategy"""
    if APP_SETTINGS.debug:
        llm_error_log_dir = APP_SETTINGS.llm_errors_logdir
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{llm_error_log_dir}/{timestamp}.output"
        with open(filename, "w") as file:
            file.write(text)
    return {"action": "Final Answer", "action_input": text}


json_react_strategies = (
    Strategy(is_bare_json, lambda text: text.startswith("{")),
    Strategy(json_markdown, lambda text: text.find("```") != -1),
    Strategy(json_nested_code_block, lambda text: text.find("```") != -1),
    Strategy(fix_json_with_embedded_code_block,
             lambda text: text.find("```") != -1),
    Strategy(json_recover_final_answer, lambda text: text.find("Final Answer") != -1),
    Strategy(fallback, lambda _: True),
)

