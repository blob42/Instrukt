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
"""Async utilities."""
import asyncio
from typing import (
    TYPE_CHECKING,
    Any,
    Coroutine,
    Generator,
    Optional,
    TypeVar,
    Union,
)

if TYPE_CHECKING:
    from instrukt.context import Context


#TODO: use custom executor
async def run_async(func, *args, **kwargs):
    """Run a function asynchronously using a thread pool."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


_T = TypeVar("_T")


def create_ctx_task(coro: Union[Generator[Any, None, _T], Coroutine[Any, Any,
                                                                    _T]],
                    ctx: 'Context',
                    *,
                    name: Optional[str] = None) -> asyncio.Task[_T]:
    """Create an asynio task with a context."""
    def handle_exc(task : asyncio.Task[Any]):
        e = task.exception()
        if e is not None:
            ctx.error(e)
            raise e #raise again exception for extra log

    task = asyncio.create_task(coro, name=name)
    task.add_done_callback(handle_exc)
    return task
