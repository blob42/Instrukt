from typing import TYPE_CHECKING, Optional

from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI

from instrukt.agent.base import InstruktAgent
from instrukt.config import APP_SETTINGS
from instrukt.output_parsers.multi_strategy import multi_parser
from instrukt.tools.base import TOOL_REGISTRY

from .prompt import PREFIX, SUFFIX

if TYPE_CHECKING:
    from instrukt.context import Context


class CodingAI(InstruktAgent):

    name = "coding_ai"
    description = "A conversational assistant optimized for technical and programming tasks."
    display_name = "Coding AI"

    @classmethod
    def load(cls, ctx: 'Context') -> Optional[InstruktAgent]:
        """Load the agent."""

        llm = ChatOpenAI(**APP_SETTINGS.openai.dict())
        # llm.model_name="gpt-4"
        llm.temperature=0.4
        agent_kwargs = dict(
            system_message=PREFIX,
            human_message=SUFFIX,
            output_parser= multi_parser,
        )
        executor_params = dict(
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            max_iterations=7,
            agent_kwargs=agent_kwargs,
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
