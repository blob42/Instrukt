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
import os
import platform
import sys
import typing as t
from glob import glob

import nest_asyncio as _nest_asyncio  # type: ignore
from IPython.terminal.embed import InteractiveShellEmbed
from rich.text import Text
from textual import events, on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.css.query import NoMatches
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static
from textual.worker import Worker, WorkerState

from ._logging import setup_logging
from .agent import AgentEvents
from .agent.base import InstruktAgent
from .agent.manager import AgentManager
from .commands.command import CmdLog
from .commands.root_cmd import ROOT as root_cmd
from .context import context_var, init_context
from .messages.agents import AgentLoaded, AgentMessage, FutureAgentTask
from .messages.base import RetrievalLLM
from .messages.indexes import IndexAttached, IndexProgress
from .messages.log import LogMessage
from .tuilib.conversation import ChatBubble
from .tuilib.modals.index_menu import IndexMenuScreen
from .tuilib.modals.tools_menu import ToolsMenuScreen
from .tuilib.repl_prompt import REPLPrompt
from .tuilib.strings import ICONS, IPYTHON_SHELL_INTRO
from .tuilib.widgets.header import InstruktHeader
from .tuilib.windows import AgentConversation, ConsoleWindow, RealmWindow
from .utils.misc import _version
from .views.index import IndexScreen
from .views.keybindings import KeyBindingsScreen
from .views.man import ManualScreen

_loop = _asyncio.get_event_loop()
_nest_asyncio.apply(_loop)

if t.TYPE_CHECKING:
    from textual.drivers.linux_driver import LinuxDriver

    from .types import AnyMessage

PLATFORM = platform.system()
WINDOWS = PLATFORM == "Windows"

setup_logging()


class SettingsScreen(Screen[None]):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    def compose(self) -> ComposeResult:
        yield Header(id="header")
        # yield Placeholder()
        yield Static("Press any key to continue [blink]_[/]", id="any-key")

    async def on_key(self, event: events.Key) -> None:
        self.app.pop_screen()


class InstruktApp(App[None]):
    """Textual TUI for Instrukt.

    The default layout is horizontal."""

    BINDINGS = [
        Binding("d", "toggle_dark", "dark mode", show=False),
        Binding("c", "toggle_console", ICONS.console_action, key_display="c"),
        Binding("Q", "quit", "exit", show=False),
        Binding("I", "uniq_screen('index_mgmt')", "index"),
        Binding("slash", "focus_instruct_prompt", "goto prompt"),
        Binding("i", "focus_instruct_prompt", "goto prompt", show=False),

        #TODO: settings screen
        # ("S", "push_screen('settings_screen')", "Settings"),
        Binding("ctrl+d",
                "dev_console",
                ICONS.dev_console_action,
                priority=True,
                key_display="C-d"),
        Binding("h", "push_screen('manual_screen')", "help", key_display="h"),

        #TODO: set priority binding but allow in inputs
        Binding("?", "uniq_screen('keybindings')", ICONS.keys_action),
        Binding("k", "focus_next_msg", "next msg", key_display="j|k"),
        Binding("j", "focus_previous_msg", "prev msg" , show=False),
    ]

    CSS_PATH = [
        "instrukt.css",
        *glob("{}/tuilib/css/*.css".format(os.path.dirname(__file__)))
    ]
    TITLE = f"ﲵ⚡Instrukt v{_version()}"
    SCREENS = {
        "settings_screen": SettingsScreen(),
        "index_menu": IndexMenuScreen(),  #modal
        "tools_menu": ToolsMenuScreen(),  #modal
        "index_mgmt": IndexScreen(name="index"),
        "manual_screen": ManualScreen(),  #modal
        "keybindings": KeyBindingsScreen(),
    }

    AUTO_FOCUS = "StartupMenu ListView"

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
        #WIP: is this the right way to store a global context ?
        self.context = context_var.get()
        assert self.context is not None
        self.context.app = self
        self.agent_manager: AgentManager = AgentManager(self.context)
        self._ishell: InteractiveShellEmbed | None = None
        self._alock = _asyncio.Lock()

        self.add_class("--console-enabled")


    async def on_mount(self):
        #DEBUG:
        # from .tuilib.modals.path_browser import PathBrowserModal
        # self.push_screen(PathBrowserModal())
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
        if self.active_agent.realm is None:  # type: ignore
            return
        try:
            self.query_one(RealmWindow).post_message(message)
        except NoMatches:
            self.log.warning("RealmWindow not found")

    @on(AgentLoaded)
    async def handle_agent_loaded(self, message: AgentLoaded) -> None:
        if message.agent is not None:
            self.notify_agent_window(message)
            self.screen.remove_class("-no-agent")
            self.screen.remove_class("-show-new-agent")
        else:
            self.post_message(LogMessage.warning("agent was not loaded !"))

    @on(IndexProgress)
    def index_progress_event(self, event: IndexProgress) -> None:
        """Notify index console"""
        try:
            ic = self.query_one("IndexConsole")
            ic.set_msg(event.msg)   # type: ignore
        except NoMatches:
            self.log.info(event.msg)

    @on(IndexAttached)
    def index_attached(self, ev: IndexAttached) -> None:
        # update the repl suggester
        try:
            repl = self.query_one(REPLPrompt)
            repl.suggester.add(ev.index_name)
        except NoMatches:
            self.log.warning("REPLPrompt not found")


    @on(FutureAgentTask)
    def future_agent_task_handler(self, ev: FutureAgentTask) -> None:
        """Future events that should update the agent window."""
        try:
            self.log.debug("notifying agent header progress")
            progress = self.query_one("AgentWindowHeader #progress")
            progress.track_future(ev.future)
        except NoMatches:
            self.log.warning("agent window header not found")


    @on(Worker.StateChanged)
    def _catch_failed_work(self, event: Worker.StateChanged) -> None:
        if event.worker.state == WorkerState.ERROR:
            # pass back the worker error to index screen
            if self.screen.name == "index":
                try:
                    self.screen.query_one("CreateIndex")._on_work_change(event)
                except NoMatches:
                    pass

    @on(Button.Pressed, "#toggle_console")
    def toggle_console(self, event: events.Click) -> None:
        """Toggle console window."""
        self.toggle_class("--console-enabled")

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
        # TODO: using textual notificaion system instead of console window
        # self.notify(str(message.msg), timeout=2)

        try:
            console = self.query_one(ConsoleWindow)
            self.call_after_refresh(console.write, " \n")
            self.call_after_refresh(console.write, message)
        except NoMatches:
            self.log.info(message)

    @on(AgentMessage)
    async def handle_agent_message(self, message: AgentMessage) -> None:
        """Events coming from agents."""
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

    @on(RetrievalLLM)
    def change_retrieval_llm(self, ev: RetrievalLLM) -> None:
        """Change the retrieval LLM mode."""
        from langchain.chains.retrieval_qa.base import BaseRetrievalQA
        if self.active_agent is not None and self.active_agent.toolset is not None:
            # find all retrival tool
            ret_tools = [
                tool for tool in self.active_agent.toolset if tool.is_retrieval
            ]

            for tool in ret_tools:
                if isinstance(tool.retrieval_runner, BaseRetrievalQA):
                    r = t.cast(BaseRetrievalQA, tool.retrieval_runner)
                    r.combine_documents_chain.llm_chain.llm.model_name=ev.model
                    self.app.context.info(f"using {ev.model} with {tool.name}")   # type: ignore

            #HACK: for demo purposes use same model on front agent
            self.active_agent.llm.model_name = ev.model


    def compose(self) -> ComposeResult:
        """Create child widgets"""
        from .tuilib.panels import MainConsole, MonitorPane
        from .tuilib.repl_prompt import REPLPrompt
        from .tuilib.startup_menu import StartupMenu
        yield InstruktHeader(id="app-header")
        # yield Header(show_clock=True)

        with Horizontal():
            with Vertical(id="main-menu"):
                yield Button(ICONS.main_menu, id="toggle_console")
            yield MainConsole()
            yield MonitorPane(id="monitor-pane")
            yield StartupMenu()
            with Container(id="instrukt-prompt"):
                yield Static("mode", id="repl-mode")
                yield REPLPrompt()

        yield Footer()

    @on(events.Ready)
    async def notify_windows(self, event: events.Ready) -> None:
        """Notify all windows that the app is ready"""
        for w in self.query(".window"):
            w.post_message(self.Ready())

    def on_replprompt_cmd_event(self):
        """User entered a command in the REPL prompt."""
        if not self.has_class("--console-enabled"):
            self.add_class("--console-enabled")


    async def key_exclamation_mark(self, ev: events.Key) -> None:
        if self.context.config_manager.config.debug:
            ev.stop()
            from .utils.debug import dap_listen
            if dap_listen():
                self.post_message( LogMessage.info("started DAP"))
            else:
                self.post_message( LogMessage.info("DAP already listening"))



    def action_focus_instruct_prompt(self) -> None:
        try:
            self.query_one(REPLPrompt).focus()
        except NoMatches:
            pass

    def action_toggle_console(self) -> None:
        self.toggle_class("--console-enabled")
        

    def action_focus_next_msg(self) -> None:
        try:
            conv = self.query_one("AgentConversation")
        except NoMatches:
            return
        focused = self.focused
        if isinstance(focused, ChatBubble):
            if conv.children[-1] != focused:
                self.action_focus_next()
        else:
            try:
                messages = self.query("ChatBubble")
                messages.last().focus()
            except NoMatches:
                return

    def action_focus_previous_msg(self) -> None:
        try:
            conv = self.query_one("AgentConversation")
        except NoMatches:
            return
        focused = self.focused
        if isinstance(focused, ChatBubble):
            # pos 0 is user msg normally
            if conv.children[1] != focused:
                self.action_focus_previous()
        else:
            try:
                messages = self.query("ChatBubble")
                messages.last().focus()
            except NoMatches:
                return

    def action_uniq_screen(self, screen_name: str) -> None:
        screen = self.SCREENS.get(screen_name)
        if len(self.screen_stack) > 0 and not isinstance(
                self.screen_stack[-1], type(screen)):
            self.push_screen(screen)

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

        with self.console.capture() as c_capture:
            self.console.print(Text.from_markup(IPYTHON_SHELL_INTRO))
        banner1 = c_capture.get()

        def print_banner():
            return Text.from_markup(IPYTHON_SHELL_INTRO)

        def get_memory():
            def get_agent_memory():
                if agent is not None:
                    return agent.memory
                else:
                    return None
            return get_agent_memory()


        user_ns = {
            "app": self,
            "agent": agent,
            "intro": print_banner(),
            "memory": get_memory(),
            "im": self.context.index_manager,
        }

        frame = sys._getframe(1)
        if self._ishell is None:
            shell_kwargs = {
                "colors": "neutral",
                "loop_runner": "asyncio",
                "banner1": banner1,
            }
            self._ishell = InteractiveShellEmbed.instance(
                _init_location_id='%s:%s' %
                (frame.f_code.co_filename, frame.f_lineno),
                **shell_kwargs)

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

        with self.batch_update():
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

init_context()
