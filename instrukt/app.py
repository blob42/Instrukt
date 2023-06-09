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
"""Instrukt TUI App."""

import asyncio as _asyncio
import logging
import os
import platform
import sys
import typing as t
from glob import glob

import nest_asyncio as _nest_asyncio  # type: ignore
from IPython.terminal.embed import InteractiveShellEmbed
from textual import events, on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.css.query import NoMatches
from textual.logging import TextualHandler
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from .utils import debug
from .agent import AgentEvents
from .agent.base import InstruktAgent
from .agent.manager import AgentManager
from .commands.command import CmdLog
from .commands.root_cmd import ROOT as root_cmd
from .context import Context
from .messages.agents import AgentLoaded, AgentMessage
from .messages.log import LogMessage
from .tuilib.modals.index_menu import IndexMenuScreen
from .tuilib.modals.tools_menu import ToolsMenuScreen
from .tuilib.widgets.header import InstruktHeader
from .tuilib.repl_prompt import REPLPrompt
from .tuilib.windows import AgentConversation, ConsoleWindow, RealmWindow
from .views.index import IndexScreen
from .views.man import ManualScreen


_loop = _asyncio.get_event_loop()
_nest_asyncio.apply(_loop)

logging.basicConfig(
    level="DEBUG",
    handlers=[TextualHandler()],
)

if t.TYPE_CHECKING:
    from textual.drivers.linux_driver import LinuxDriver

    from .types import AnyMessage

PLATFORM = platform.system()
WINDOWS = PLATFORM == "Windows"


class SettingsScreen(Screen[None]):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    def compose(self) -> ComposeResult:
        yield Header(id="header")
        # yield Placeholder()
        yield Static("Press any key to continue [blink]_[/]", id="any-key")

    async def on_key(self, event: events.Key) -> None:
        self.app.pop_screen()


# class SettingsScreen(ModalScreen):
#     BINDINGS = [("escape", "dismiss", "Dismiss")]
#     def compose(self) -> ComposeResult:
#         yield SettingsDialogue()
#     def action_dismiss(self) -> None:
#         self.app.pop_screen()


class InstruktApp(App[None]):
    """Textual TUI for Instrukt.

    The default layout is horizontal."""

    BINDINGS = [
        Binding("d", "toggle_dark", "Toggle dark mode", show=False),
        ("q", "quit", "Quit Application"),
        ("I", "push_screen('index_mgmt_screen')", "Indexes"),
        ("slash", "focus_instruct_prompt", "Focus Prompt"),

        #TODO: settings screen
        # ("S", "push_screen('settings_screen')", "Settings"),
        ("D", "dev_console", "Developer Console"),
        ("M", "push_screen('manual_screen')", "Manual"),
    ]

    CSS_PATH = [
        "instrukt.css",
        *glob("{}/tuilib/css/*.css".format(os.path.dirname(__file__)))
    ]
    TITLE = "Instrukt"
    SCREENS = {
        "settings_screen": SettingsScreen(),
        "index_menu": IndexMenuScreen(),
        "tools_menu": ToolsMenuScreen(),
        "index_mgmt_screen": IndexScreen(),
        "manual_screen": ManualScreen(),
    }

    AUTO_FOCUS = "StartupMenu ListView"


    context: Context = Context()

    class Ready(Message):
        pass

    @property
    def active_agent(self) -> InstruktAgent | None:
        if self.agent_manager is not None:
            return self.agent_manager.active_agent
        return None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cmd_handler = root_cmd
        #HACK: is this the right way to store a global context ?
        self.context.app = self
        self.agent_manager: AgentManager = AgentManager(self.context)
        self._ishell: InteractiveShellEmbed = None

    async def on_mount(self):
        #DEBUG:
        # self.push_screen("index_mgmt_screen")
        # await self.agent_manager.load_agent("demo")
        self.screen.add_class("-no-agent")


    def notify_console_window(self, message: "AnyMessage") -> None:
        self.query_one(ConsoleWindow).post_message(message)

    def notify_agent_window(self, message: "AnyMessage") -> None:
        try:
            self.query_one(AgentConversation).post_message(message)
        except NoMatches:
            self.log.error("AgentConversation window not found")

    def notify_realm_buffer(self, message: "AnyMessage") -> None:
        try:
            self.query_one(RealmWindow).post_message(message)
        except NoMatches:
            self.log.error("RealmWindow not found")

    @on(AgentLoaded)
    async def handle_agent_loaded(self, message: AgentLoaded) -> None:
        if message.agent is not None:
            self.notify_agent_window(message)
            self.screen.remove_class("-no-agent")
            self.screen.remove_class("-show-new-agent")
        else:
            self.post_message(LogMessage.warning("agent was not loaded !"))

    @on(CmdLog)
    async def cmd_log(self, message: CmdLog) -> None:
        chat = self.query_one(ConsoleWindow)
        self.call_after_refresh(chat.write, message.msg)
        message.stop()

    # WIP: handle all message in one place using LogMessage class
    #NOTE: this should be handler with a message logging router when the ConsoleWindow
    # is not available
    @on(LogMessage)
    async def log_message(self, message: LogMessage) -> None:
        try:
            chat = self.query_one(ConsoleWindow)
            self.call_after_refresh(chat.write, message)
        except NoMatches:
            self.log.info(message)

    @on(AgentMessage)
    async def handle_agent_message(self, message: AgentMessage) -> None:
        # what goes to the realm buffer
        if message.event in [AgentEvents.ToolStart, AgentEvents.ToolEnd]:
            self.notify_realm_buffer(message)
            self.notify_agent_window(message)
        # elif message.event in [AgentEvents.AgentAction,
        #                        AgentEvents.AgentFinish,
        #                        AgentEvents.ChainStart,
        #                        AgentEvents.ChainError]:
        #     await self.notify_agent_window(message)
        else:
            self.notify_agent_window(message)
            # notify(message.event.value)
        message.stop()

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        from .tuilib.panels import InstPanel, MonitorPanel
        from .tuilib.startup_menu import StartupMenu
        yield InstruktHeader(id="app-header")
        # yield Header(show_clock=True)

        with Horizontal():
            yield InstPanel(id="instrukt-panel")
            yield MonitorPanel(id="monitor-panel")
            yield StartupMenu()

        yield Footer()

    @on(events.Ready)
    async def notify_windows(self, event: events.Ready) -> None:
        """Notify all windows that the app is ready"""
        for w in self.query(".window"):
            w.post_message(self.Ready())

    def action_focus_instruct_prompt(self) -> None:
        try:
            self.query_one(REPLPrompt).focus()
        except NoMatches:
            pass

    def action_toggle_dark(self) -> None:
        """toggle dark mode"""
        self.dark = not self.dark

    # NOTE: the main render loop is running at the same time as IPython's loop
    # this means terminal state can change while being inside IPython session
    # TODO!: find a way to Textual writing to the terminal when IPython is running.
    # how to give textual a dummy pty while giving full tty control to IPython ?
    #TODO: move to own mod/class 
    def _embed_ipython(self, *args, **kwargs) -> None:

        # export agent to ipython namespace
        agent = self.active_agent

        user_ns = {
            "app": self,
            "agent": agent,
        }

        frame = sys._getframe(1)
        if self._ishell is None:
            shell_kwargs = {
                  "colors":"neutral",
                  "loop_runner":"asyncio",
                  "banner1" : "Instrukt IPython Shell\n",
            }
            self._ishell = InteractiveShellEmbed.instance(
                    _init_location_id='%s:%s' % (
                        frame.f_code.co_filename, frame.f_lineno), **shell_kwargs)

            def pre_execute():
                self._ishell.ex("pretty.install(max_depth=2)")

            self._ishell.events.register("pre_execute", pre_execute)


        self._ishell.user_ns = user_ns
        self._ishell.ex("from rich import pretty")

        self._ishell(stack_depth=0,
                     local_ns=user_ns,
                     _call_location_id='%s:%s' %
                     (frame.f_code.co_filename, frame.f_lineno))

        #NOTE: simple way to do it, does not work with rich console.
        # embed(*args, **kwargs,
        #           colors="neutral",
        #           loop_runner="asyncio",
        #           banner1 = "Instrukt IPython Shell\n",
        #           )

    async def action_dev_console(self) -> None:
        """Start the dev console"""
        assert self._driver is not None

        if WINDOWS:
            self.post_message(
                LogMessage.warning(
                    "dev console is not working yet in windows."))
            return

        #HACK: need to make sure no input is focused before switching
        self.set_focus(None)
        self.refresh()
        await _asyncio.sleep(0.3)

        self._driver.stop_application_mode()
        self._driver.flush()

        stdout_orig = sys.stdout
        stderr_orig = sys.stderr
        driver = t.cast('LinuxDriver', self._driver)
        sys.stdout = sys.stderr = driver._file

        self._embed_ipython()

        sys.stdout = stdout_orig
        sys.stderr = stderr_orig
        driver.start_application_mode()

    def action_quit(self):
        if self.active_agent is not None:
            if self.active_agent.realm is not None:
                self.active_agent.realm.stop_session()
        # save command history
        try:
            self.query_one(REPLPrompt).cmd_history.save()
        except NoMatches:
            pass
        self.exit()


# TODO: add auto restart logic ?
def run():
    """run script entry"""
    app = InstruktApp()
    app.run()


if __name__ == "__main__":
    run()
