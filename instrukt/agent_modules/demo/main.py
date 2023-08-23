from typing import TYPE_CHECKING, Optional

from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI
from langchain.tools.searx_search.tool import SearxSearchResults, SearxSearchRun
from langchain.utilities import SearxSearchWrapper

from instrukt.agent.base import InstruktAgent
from instrukt.config import APP_SETTINGS
from instrukt.output_parsers.multi_strategy import multi_parser
from instrukt.tools.base import TOOL_REGISTRY, LcToolWrapper
from instrukt.agent.memory import ConversationBufferWindowMemory

if TYPE_CHECKING:
    from instrukt.context import Context
    from instrukt.tools.base import SomeTool


# shows how to customize the agent's prompt
SUFFIX = """TOOLS
------
Assistant can ask the user to use tools to look up information that may be helpful in 
answering the users original question. The tools the human can use are:

{{tools}}

{format_instructions}

USER'S INPUT
--------------------
Here is the user's input (remember to respond with a markdown code snippet of a json 
blob with a single action, and NOTHING else):

{{{{input}}}}"""



class DemoAgent(InstruktAgent):

    name = "demo"
    description = "Demo conversational agent."
    display_name = "Demo QA"


    @classmethod
    def load(cls, ctx: 'Context') -> Optional[InstruktAgent]:
        """Load the docqa agent."""

        memory = ConversationBufferWindowMemory(memory_key="chat_history",
                                          return_messages=True, k=4)

        llm = ChatOpenAI(**APP_SETTINGS.openai.dict(
            exclude={"model", "temperature"}),
                         model="gpt-3.5-turbo-0613",
                         temperature=0.2)

        agent_kwargs = dict(
                human_message=SUFFIX,
                output_parser=multi_parser,
                )


        # example of adding searx tools
        # requires a self hosted searx instance to obtain resuts
        searx_wrapper = SearxSearchWrapper(searx_host="https://search.blob42.xyz")
        github_tool = SearxSearchResults(name="Github",
                                    description="Useful to search Github."
                                    "simplify the input to just the search term. "
                                    "Always print full links to the results.",
                                    wrapper=searx_wrapper,
                                    kwargs = {
                                        "engines": ["github"],
                                        })

        arxiv_tool = SearxSearchResults(name="Arxiv",
                                    description="Search for papers on arxiv. "
                                        "Use simple search terms.",
                                    wrapper=searx_wrapper,
                                    num_results=10,
                                    kwargs = {
                                        "engines": ["arxiv"]
                                        })

        searx_tool = SearxSearchRun(
                name="Search",
                wrapper=searx_wrapper,
                )
        wikipedia_tool = TOOL_REGISTRY.tools["Wikipedia"]
        wikipedia_tool.attached = False

        executor_params = dict(
                agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
                verbose=True,
                max_iterations=7,
                agent_kwargs=agent_kwargs,
                )

        tools: list["SomeTool"] = [
                LcToolWrapper(searx_tool, attached=False),
                LcToolWrapper(github_tool, attached=False),
                LcToolWrapper(arxiv_tool, attached=False),
                wikipedia_tool,
                ]

        instrukt_agent = cls(toolset=tools,
                             llm=llm,
                             memory=memory,
                             executor_params=executor_params)

        return instrukt_agent

    @classmethod
    async def aload(cls, ctx: 'Context') -> Optional[InstruktAgent]:
        raise NotImplementedError("Use load instead")
        return None
