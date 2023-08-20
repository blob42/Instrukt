from instrukt.commands.command import CallbackOutput, CmdGroup, CmdLog
from instrukt.commands.root_cmd import ROOT as root
from instrukt.context import Context


@root.group(name="docqa")
class DocQACommands(CmdGroup):
    """DocQA commands"""

    @staticmethod
    async def cmd_test(ctx: Context) -> CallbackOutput:
        """test command"""
        return CmdLog("docqa test !")
