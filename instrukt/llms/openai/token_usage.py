##
##  Copyright (c) 2023 Chakib Ben Ziane <contact@blob42.xyz>. All rights reserved.
##
##  SPDX-License-Identifier: AGPL-3.0-or-later AND MIT
##
##  This file incorporates code from the Langchain project covered by the MIT license.
##  The full text of the license can be found at:
##  https://opensource.org/licenses/MIT
##
##  Original code covered by the MIT license:
##  - [Harrison Chase]
##  - [other authors from langchain]
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

from langchain.callbacks.base import AsyncCallbackHandler
from langchain.callbacks.openai_info import (
    MODEL_COST_PER_1K_TOKENS,
    get_openai_token_cost_for_model,
    standardize_model_name,
)

from instrukt.utils.debug import notify

if t.TYPE_CHECKING:
    from langchain.schema import LLMResult


#TODO!: split into global and per tool/agent context handler
# currently used as a global tracker for all llms as well as last llm call
class OpenAICallbackHandler(AsyncCallbackHandler):
    """Callback Handler that tracks OpenAI info."""

    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    successful_requests: int = 0
    total_cost: float = 0.0

    last_prompt_tokens: int = 0
    last_completion_tokens: int = 0

    async def on_llm_end(self, response: "LLMResult", **kwargs: t.Any) -> None:
        """Collect token usage."""
        notify("on_llm_end")
        if response.llm_output is None:
            return None
        self.successful_requests += 1
        if "token_usage" not in response.llm_output:
            return None
        token_usage = response.llm_output["token_usage"]
        completion_tokens = token_usage.get("completion_tokens", 0)
        prompt_tokens = token_usage.get("prompt_tokens", 0)
        model_name = standardize_model_name(
            response.llm_output.get("model_name", ""))
        if model_name in MODEL_COST_PER_1K_TOKENS:
            completion_cost = get_openai_token_cost_for_model(
                model_name, completion_tokens, is_completion=True)
            prompt_cost = get_openai_token_cost_for_model(
                model_name, prompt_tokens)
            self.total_cost += prompt_cost + completion_cost
        self.total_tokens += token_usage.get("total_tokens", 0)
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.last_completion_tokens = completion_tokens
        self.last_prompt_tokens = prompt_tokens
