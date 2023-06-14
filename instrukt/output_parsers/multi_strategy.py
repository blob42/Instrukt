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
"""Output parsers library."""
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, Sequence, Tuple, TypeVar, Union

from xdg import BaseDirectory  # type: ignore
from langchain.agents.agent import AgentOutputParser
from langchain.agents.conversational_chat.prompt import FORMAT_INSTRUCTIONS
from langchain.schema import (
    AgentAction,
    AgentFinish,
    BaseOutputParser,
    OutputParserException,
)

from .strategies import json_react_strategies
from ..config import APP_SETTINGS

log = logging.getLogger(__name__)
# get logger to file


T = TypeVar("T")
S = TypeVar("S")

# type for a predicate
TPredicate = Callable[[str], bool]

# type for a strategy (callbale, predicate)
TStrategy = Tuple[Callable[[str], S], TPredicate]


class MultiStrategyParser(BaseOutputParser[T], ABC, Generic[T, S]):
    """A parser that tries multiple strategies to parse the output.


    The strategies are tried in order. The first one that succeeds is returned.

    A strategy is a callable that takes in text and returns some type.

    The returned type is then passed to the final_parse method to produce the
    final result compatible with the output parser interface.
    """

    strategies: Sequence[TStrategy[S]]
    """List of strategies to try. The first one that succeeds is returned."""

    def add_strategy(self, *strategy: TStrategy[S]) -> None:
        """Register a new strategy. 

        A strategy is a callbale that takes in text and returns some type 
        """
        self.strategies = [*self.strategies, *strategy]

    @abstractmethod
    def final_parse(self, text: str, parsed: S) -> T:
        """Parse the output of a strategy."""

    def parse(self, text: str) -> T:
        """Try all the strategies in order. The first one that succeeds is returned."""

        if len(self.strategies) == 0:
            raise OutputParserException("No strategy available")
        for strategy, predicate in self.strategies:
            log.debug(f"Trying strategy {strategy}")
            if not predicate(text):
                log.debug(f"Skipping strategy {strategy}")
            if predicate(text):
                try:
                    parsed = strategy(text)
                    result = self.final_parse(text, parsed)
                    log.debug(f"Strategy {strategy} succeeded. Result: {result}")
                    return result
                except Exception:
                    continue

        raise OutputParserException(f"Could not parse output: {text}")

    @property
    def _type(self) -> str:
        return "multi_strategy"


U = Union[AgentAction, AgentFinish]
TReactAgentOutput = U
W = dict[str, Any]


class ConvMultiStrategyParser(MultiStrategyParser[U, W], AgentOutputParser):
    """Multi strategy output parser for a chat conversation agent.

    Every strategy must parse the LLM output into a dict of the form:
        {
            "action": str,
            "action_input": str"
        }
    """

    def get_format_instructions(self) -> str:
        return FORMAT_INSTRUCTIONS

    def __init__(self, strategies: Sequence[TStrategy[W]], **kwargs) -> None:
        super().__init__(strategies=strategies, **kwargs)

    def final_parse(self, text: str, parsed: W) -> U:
        action, action_input = parsed["action"], parsed["action_input"]
        if action == "Final Answer":
            return AgentFinish({"output": action_input}, text)
        else:
            return AgentAction(action, action_input, text)


# Default parser
multi_parser = ConvMultiStrategyParser(json_react_strategies)
