from instrukt.commands.command import CmdGroup
from instrukt.commands.root_cmd import ROOT as root
from instrukt.context import Context

"""
This code illustrates how to create commands for an agent module.

To create command groups, use the `@root.group` decorator over a class.

To define commands within the group, use the `@staticmethod` decorator over a method.
The method name must start with `cmd_`.

The method must accept a `Context` object and return a `CallbackOutput` object.

Command descriptions for the instrukt shell are taken from the docstrings \
of each command method.
"""

@root.group(name="demo")
class DemoAgentCommands(CmdGroup):
    """testing agent commands"""

    @staticmethod
    async def cmd_fake_mem(ctx: Context) -> None:
        """Load a fake chat history."""
        from .fake_conv import get_chat_messages
        agent = ctx.app.agent_manager.active_agent
        agent.memory.chat_memory.messages = get_chat_messages()
        conv = ctx.app.query_one("AgentConversation")
        conv.preload_messages(agent)
