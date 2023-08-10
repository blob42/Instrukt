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

from typing import TYPE_CHECKING, Tuple

from ..commands.command import CallbackOutput, CmdGroup, CmdLog
from ..commands.root_cmd import ROOT as root
from ..context import Context
from ..indexes.schema import Index
from ..utils.asynctools import create_ctx_task, run_async

if TYPE_CHECKING:
    from instrukt.indexes.schema import Collection




@root.group(name="index")
class IndexCommands(CmdGroup):
    """Index commands"""

    @staticmethod
    async def cmd_test(ctx: Context) -> CallbackOutput:
        """test command"""
        return CmdLog("index test !")

    @staticmethod
    async def cmd_list(ctx: Context) -> None:
        """List indexes"""

        def _list_collections(ctx: Context):
            idx_mg = ctx.index_manager
            _collections = idx_mg.list_collections()
            def get_col_count(col: 'Collection') -> Tuple['Collection', int]:
                idx = idx_mg.get_index(col.name)
                if idx is not None:
                    return (col, idx.count)
                return (col, -1)
            collections = list(map(get_col_count, _collections))
            # turn collections into tuple of (name, count) where count
            # is idx_mg.get_index(name).count()
            # if collection is not nont
            _col_names = '\n' + '\n'.join(
                    ['- ' + f"[b]{col[0].name}[/] ({col[1]})" for col in collections]
                    )
            ctx.post_message(CmdLog(f"\n[u]Available collections:[/] {_col_names}"))

        create_ctx_task(run_async(_list_collections, ctx), ctx)

    @staticmethod
    async def cmd_create(
        ctx,
        name: str,
        path: str,
    ) -> None:
        """Create an index for Q/A retrieval."""

        async def create_index(ctx: Context, name: str, path: str):
            im = ctx.index_manager
            await im.create(Index(name=name, path=path))
            ctx.post_message(CmdLog('Index created'))

        create_ctx_task(create_index(ctx, name, path), ctx)
