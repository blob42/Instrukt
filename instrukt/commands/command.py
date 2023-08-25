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
"""Main command classes.

Implements the main command classes that are used to register and execute commands.
"""

#TODO: allow for command aliases

import inspect
from functools import wraps
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Dict,
    Generator,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
)

from rich.console import RenderableType
from textual.message import Message

from ..context import Context
from ..errors import (
    CommandAlreadyRegistered,
    CommandError,
    CommandGroupError,
    CommandNotFound,
    NoCommandsRegistered,
)
from ..utils.misc import MISSING

__all__ = [
        'CmdGroup',
        'Command',
        'CmdLog',
        ]

T = TypeVar('T')
CallbackOutput = Optional[Any]
F = TypeVar('F', bound=Callable[..., CallbackOutput])
CallbackT = Callable[..., Awaitable[CallbackOutput]]

AnyOrAwaitable = Union[Any, Awaitable[CallbackOutput]]

Coro = Coroutine[Any, Any, T]
ACmdGroup = Union[Type['CmdGroup'], 'CmdGroup']

CMD_PREFIX = [".", "/"]

class CmdLog(Message):
    """Arbitrary log from a command execution.

    Useful for commands with side effects who wish to also print some log.
    """

    namespace = "instrukt"

    __slots__ = ("msg",)

    def __init__(self, msg: RenderableType):
        self.msg = msg
        super().__init__()

    def __repr__(self):
        return self.msg.__repr__()

    def __str__(self):
        return self.msg.__str__()

    def __rich__(self):
        return f"\n[green]{self.msg}[/]\n"

class Command:
    """A command class representing a command that can be executed in the REPL.

    Args:
        callback: A function that takes at least a context and
        returns Optional[Any].
    """

    def __init__(self,
                 name: str,
                 callback: CallbackT,
                 description: Optional[str] = MISSING,
                 alias: Optional[str] = None,
                 parent: Optional['CmdGroup'] = None,
                 help: Optional[str] = MISSING,
                 ) -> None:
        self.name = name
        self.alias = alias
        self.callback = callback
        self.parent: Optional[CmdGroup] = parent

        if description is MISSING:
            if callback.__doc__:
                self.description = callback.__doc__.splitlines()[0]
            else:
                raise CommandError("Command needs a description")
        else:
            if not isinstance(description, str):
                raise CommandError("Command description must be a string")
            self.description = description

        if help is MISSING:
            if callback.__doc__:
                self.help = callback.__doc__
            else:
                self.help = "No help available"


        sig = inspect.signature(callback)
        if len(sig.parameters) == 0:
            raise CommandError("Command needs at least a context argument")



    async def execute(self, ctx, *args) -> CallbackOutput:
        """Execute the command with the given arguments."""
        if not isinstance(ctx, Context):
            raise CommandError("Context must be a Context instance")

        return await self.callback(ctx, *args)

    @property
    def root_parent(self) -> Optional['CmdGroup']:
        """Return the root parent of this command"""
        if self.parent is None:
            return None

        root: 'CmdGroup' = self.parent
        while root.parent is not None:
            root = root.parent

        return root


    def __str__(self) -> str:
        return f"{self.name}: {self.description}"

class CmdGroup:
    """A class representing a group of commands."""

    def __init__(self,
                 name: str,
                 description: str,
                 parent: Optional['CmdGroup'] = None,
                 ) -> None:
        self.name = name
        self.description = description
        self._children: Dict[str, Union[Command, CmdGroup]] = {}
        self.parent: Optional[CmdGroup] = parent

    def help(self) -> str:
        """Generate the help for the current group. 

        List all the commands under the current group and their description.

        If the group is the root group, then it will list all the commands.
        """

        if self.is_root:
            output = "[b]Root commands[/b]:\n\n"
        else:
            output = f"Commands under {self.name}:\n\n"

        is_root_cmd = self.is_root

        for command in self.commands:
            if is_root_cmd:
                output += f"[yellow]{CMD_PREFIX[0]}{command.name}[/]: {command.description}\n"
            else:
                output += f"[yellow]{command.name}[/]: {command.description}\n"

        return output


    def add_command(self, command: Union[Command, 'CmdGroup'], override: bool = False) -> None:
        """Add a Command or CmdGroup to this group."""

        if not override and command.name in self._children:
            raise CommandAlreadyRegistered(command.name)

        self._children[command.name] = command
        command.parent = self

    def get_command(self, name: str, /) -> Optional[Union[Command, 'CmdGroup']]:
        """Retrive a command or a group from its name or alias."""
        cmd = self._children.get(name)
        if cmd is not None:
            return cmd
        else: # search for alias
            for command in self._children.values():
                if isinstance(command, Command) and command.alias == name:
                    return command

    #TEST: 
    def parse_cmd(self, cmd_list: str) -> Optional[Union[Command, 'CmdGroup']]:
        """Given a commands string, return the command or group that matches the string."""
        if cmd_list == '':
            return self

        cmd_list = cmd_list.split(' ')
        if len(cmd_list) == 1:
            return self.get_command(cmd_list[0])
        else:
            cmd = self.get_command(cmd_list[0])
            if cmd is None:
                return None
            else:
                if isinstance(cmd, CmdGroup):
                    return cmd.parse_cmd(' '.join(cmd_list[1:]))
                else:
                    return None
            

    def walk_commands(self) -> Generator[Union[Command, 'CmdGroup'], None, None]:
        """Iterator that recursively walks through all commands that this group contains.

        Yields
        ---------
        Union[:class:`Command`, :class:`CmdGroup`]
            The commands in this group.
        """

        for command in self._children.values():
            yield command
            if isinstance(command, CmdGroup):
                yield from command.walk_commands()

    @property
    def root_parent(self) -> Union[Command, 'CmdGroup']:
        """Return the root parent of this group."""
        if self.parent is None:
            return self
        else:
            return self.parent.root_parent

    @property
    def is_root(self) -> bool:
        return self.parent is None

    @property
    def commands(self) -> List[Union[Command, 'CmdGroup']]:
        """List[Union[:class:`Command`, :class:`CmdGroup`]]: The commands that this group contains."""
        return list(self._children.values())

    def command(self,
                    _func=None,
                    *,
                    name: Optional[str] = None,
                    description: Optional[str] = None,
                    alias: Optional[str] = None) -> Callable[[CallbackT], CallbackT]:
        """Decorator that registers a function as a command in a CommandGroup."""

        def decorator(callback: CallbackT) -> Any:
            command_name = name or callback.__name__
            command_desc = description or callback.__doc__
            command_alias = alias
            if command_desc is None:
                raise CommandError(f"Command {command_name} needs a description")

            self.add_command(Command(command_name,
                                     callback,
                                     command_desc,
                                     alias=command_alias))

            @wraps(callback)
            def wrapper(*args, **kwargs):
                return callback(*args, **kwargs)

            return wrapper

        if _func is None:
            return decorator
        else:
            return decorator(_func)


    # class decorator to register a group
    # the group methods are registered as commands
    # the method name must start with cmd_ to be regsitered as a command on the group
    # the group class should inherit the CmdGroup class
    #TODO: handle aliases for class style group commands
    def group(self, _cls=None, *,
              name: str = MISSING,
              description: str = MISSING) -> Callable[..., Any]:
        """Decorator that registers a class as a command group."""

        def decorator(group_cls: F) -> Any:

            group_name = name
            group_desc = description

            if name is MISSING:
                group_name = group_cls.__name__.lower()

            if description is MISSING:
                if group_cls.__doc__:
                    group_desc = group_cls.__doc__.splitlines()[0]
                else:
                    raise CommandGroupError("Group needs a description")

            group = CmdGroup(group_name, group_desc, parent=self)

            # add all the methods that start with cmd_ as commands
            for attribute_name in dir(group_cls):
                if attribute_name.startswith("cmd_"):
                    attribute = getattr(group_cls, attribute_name)
                    if callable(attribute):
                        command_name = attribute_name[4:]
                        command_desc = attribute.__doc__
                        if command_desc is None:
                            raise CommandError(f"Command {command_name} needs a description")
                        command = Command(command_name, attribute, command_desc)
                        group.add_command(command)


            self.add_command(group)

            return group_cls

        if _cls is None:
            return decorator
        else:
            return decorator(_cls)


    #TODO!: use contextvars to pass context to commands
    async def execute(self, ctx: Context, command_string: Optional[str] = None, **kwargs) -> AnyOrAwaitable:
        """Execute a command given a string.

        Parses the command string recursively and executes the leaf command.
        """
        if not isinstance(ctx, Context):
            raise TypeError("ctx must be a Context")

        if command_string is None:
            if len(self.commands) == 0:
                raise NoCommandsRegistered()
            else:
                return self.help()

        if command_string == '':
            return self.help()

        split_command = command_string.split(" ")
        command_name = split_command[0]
        args = split_command[1:]

        command = self.get_command(command_name)

        if command is None:
            raise CommandNotFound(command_name)

        if isinstance(command, Command):
            return await command.execute(ctx, *args, **kwargs)
        elif isinstance(command, CmdGroup):
            return await command.execute(ctx, " ".join(args), **kwargs)
        else:
            raise CommandError(f"Command {command} is not a valid command or group.")


# def command(_func=None,
#             *,
#             name: Optional[str] = None,
#             desc: Optional[str] = None) -> Callable[[F], F]:
#     """Decorator to register a command on a group."""
#
#     def decorator(callback: F) -> Any:
#         command_name = name or callback.__name__
#         command_desc = desc or "DESCRIPTION PLACEHOLDER"
#         CmdGroup.commands[command_name] = Command(command_name, callback,
#                                                command_desc)
#
#         @wraps(callback)
#         def wrapper(*args, **kwargs):
#             notify("cmd decorater wrap !")
#             return callback(*args, **kwargs)
#
#         return wrapper
#
#     if _func is None:
#         return decorator
#     else:
#         return decorator(_func)
#
