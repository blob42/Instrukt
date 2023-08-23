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
from typing import TYPE_CHECKING, Optional

from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory

from instrukt.agent.base import InstruktAgent
from instrukt.config import APP_SETTINGS
from instrukt.output_parsers.multi_strategy import multi_parser
from instrukt.tools.base import TOOL_REGISTRY

if TYPE_CHECKING:
    from instrukt.context import Context


class DocQAAgent(InstruktAgent):

    name = "chat_qa"
    description = "Conversational agent optimized for QA over indexes."
    display_name = "Chat QA"

    @classmethod
    def load(cls, ctx: 'Context') -> Optional[InstruktAgent]:
        """Load the docqa agent."""


        llm = ChatOpenAI(**APP_SETTINGS.openai.dict())
        agent_kwargs = {
            'output_parser': multi_parser,
        }
        executor_params = dict(
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            max_iterations=7,
            agent_kwargs=agent_kwargs,
            # return_intermediate_steps=True,
            # verbose=True,
        )

        wiki_tool = TOOL_REGISTRY.tools["Wikipedia"]
        wiki_tool.attached = False
        toolset = (
            wiki_tool,
            # INSERT TOOLS HERE
        )

        instrukt_agent = cls(toolset=toolset,
                             llm=llm,
                             executor_params=executor_params)

        return instrukt_agent

    @classmethod
    async def aload(cls, ctx: 'Context') -> Optional[InstruktAgent]:
        raise NotImplementedError("Use load instead")
        return None
