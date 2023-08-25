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
"""Instrukt commands.

Commands are created with the Command class and registered using a Route.

`RootCmd` is the root of all command routes.  

# Defining new commands:

To define new commands use the @RootCmd.command decorator.
If you add a command on a separate module, make sure to only export the
decorated functions with __all__
"""
from .command import (
    CmdGroup,
    CmdLog,
    Command,
    Context,
)

"""register command modules here"""
CMD_MODULES = [
        'help',
        'ui',
        'agents',
        'config',
        'index',
        ]


__all__ = [
        'CmdGroup',
        'Command',
        'Context',
        'CmdLog',
        ]
