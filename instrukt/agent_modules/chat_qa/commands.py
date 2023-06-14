from instrukt.commands.root_cmd import ROOT as root
from instrukt.commands.command import CmdGroup, CallbackOutput, CmdLog
from instrukt.context import Context

@root.group(name="docqa")
class DocQACommands(CmdGroup):
    """DocQA commands"""

    @staticmethod
    async def cmd_test(ctx: Context) -> CallbackOutput:
        """test command"""
        return CmdLog("docqa test !")
