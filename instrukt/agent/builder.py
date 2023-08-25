##
##  Copyright (c) 2023 Chakib Ben Ziane <contact@blob42.xyz>. All rights reserved.
##
##  SPDX-License-Identifier: AGPL-3.0-or-later
##
##  This file is part of Instrukt.
##
##  This program is free software: you can redistribute it and/or modify it under
##  the terms of the GNU Affero General Public License as published by the Free
##  Software Foundation, either version 3 of the License, or (at your option) any
##  later version.
##
##  This program is distributed in the hope that it will be useful, but WITHOUT
##  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
##  FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
##  details.
##
##  You should have received a copy of the GNU Affero General Public License along
##  with this program.  If not, see <http://www.gnu.org/licenses/>.
##
"""Agent composer."""

import typing as t
from dataclasses import dataclass, field

from langchain.chat_models.openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory

from ..config import APP_SETTINGS
from ..tools.base import TOOL_REGISTRY
from .base import InstruktAgent

if t.TYPE_CHECKING:
    from langchain.chat_models.base import BaseChatModel
    from langchain.memory.chat_memory import BaseChatMemory

    from ..tools.base import SomeTool


def make_chat_memory() -> "BaseChatMemory":
    """Create a memory instance."""
    return ConversationBufferMemory(memory_key="chat_history",
                                    return_messages=True)


def make_llm() -> "BaseChatModel":
    return ChatOpenAI(**APP_SETTINGS.openai.dict())


@dataclass
class AgentBuilder():
    """Helper class to build agents.

    Args:
        
        llm:
            Language model to use.
        output_parser:
            Output parser to use.
        toolset:
            List of tools to use.
        with_tools:
            List of tools to create from name. Can be any tool supported by
            langchain
    """
    llm: t.Optional["BaseChatModel"] = field(default_factory=make_llm)

    # output_parser: t.Optional["BaseOutputParser[t.Any]"] = None
    output_parser: t.Any = None

    memory: "BaseChatMemory" = field(default_factory=make_chat_memory)

    toolset: list["SomeTool"] | None = None
    """Extra tools to add to the agent."""

    with_tools: list["str"] | None = None
    """Extra registered tool names to add to the agent."""

    def __post_init__(self):
        if self.with_tools is not None:
            if self.toolset is None:
                self.toolset = []
            self.toolset.extend(TOOL_REGISTRY.get_tools(*self.with_tools))

    #WIP:
    def build_agent(self, cls_name: str, name: str,
                    description: str) -> "InstruktAgent":
        """Build the agent.

        A dynamic class is created with the given name and the agent is
        """
        if self.with_tools is not None:
            self.toolset = []
            self.toolset.extend(TOOL_REGISTRY.get_tools(*self.with_tools))

        cls_kwargs = {
            "name": name,
            "description": description,
            "llm": self.llm,
            "memory": self.memory,
            "load": lambda: None,
            # "output_parser": self.output_parser,
        }

        #FIXME: toolset: cannot pickele module object
        if self.toolset is not None:
            cls_kwargs["toolset"] = self.toolset

        return type(cls_name, (InstruktAgent, ), cls_kwargs)()
