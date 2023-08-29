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
"""Help commands"""

from .command import CallbackOutput
from .root_cmd import ROOT as root

"""Main help for the command interface to Instrukt."""
HELP_TEXT = """
[b]command line help[/]:

Call commands by prefixing them with a `.` or `/`, e.g. `/help`."""

@root.command
async def help(ctx, cmd: str | None = None, *args) -> CallbackOutput:
    """help command"""
    if cmd is None:
        return '\n'.join([HELP_TEXT, root.help()])
    else:
        if len(args) > 0:
            cmd_list = cmd + ' ' + ' '.join(args)
            _cmd = root.parse_cmd(cmd_list)
        else:
            _cmd = root.get_command(cmd)
        if isinstance(_cmd.help, str):
            return _cmd.help
        return _cmd.help()


@root.command
async def man(ctx, cmd: str | None = None, *args) -> CallbackOutput:
    """Display Instrukt's manual."""
    ctx.app.push_screen("manual_screen")
    return None

