import pytest
from unittest import mock
from instrukt.commands.command import (
        CmdGroup,
        Command,
        CallbackOutput,
        CmdLog,
        )

from instrukt.commands.history import CommandHistory

from instrukt.context import Context


from instrukt.errors import (
        CommandNotFound,
        CommandGroupError,
        CommandError,
        CommandHandlerError,
        CommandAlreadyRegistered,
        NoCommandsRegistered,
        InvalidArguments
        )



@pytest.fixture
def group():
    return CmdGroup("test_root", "root group")


@pytest.fixture(name="ctx")
def context():
    # mock app
    return Context(app=mock.Mock())


class TestCommand:


    def test_command_instance(self):
        cmd = Command("cmd_name", lambda ctx : "return", "cmd_desc")
        with pytest.raises(CommandError):
            cmd2 = Command("cmd_name", lambda ctx: "return")

    def test_command_docstring(self):
        """command docstring should be used for description and help"""

        def test_cmd(ctx):
            """test command description.
            help text should be here"""
            pass

        cmd = Command("cmd_name", test_cmd)
        assert cmd.description == "test command description."
        assert cmd.help.find("help text should be here")

    def test_command_alias(self):
        """command alias should be settable"""

        def test_cmd(ctx):
            """test command description."""
            pass

        cmd = Command("cmd_name", test_cmd, alias="cmd_alias")
        assert cmd.alias == "cmd_alias"


    @pytest.mark.asyncio
    async def test_command_execute(self, ctx):

        async def test_run_cmd(ctx, arg1):
            return f"test_run_cmd {arg1}"

        run_cmd = Command("run_cmd", test_run_cmd, description="test run command")
        assert await run_cmd.execute(ctx, 1) == "test_run_cmd 1"



    def test_command_handler_return(self, ctx):
        """command handlers should return Optional[Any]"""

        def ok_cmd(ctx, arg1):
            return True
        cmd = Command("ok_cmd", ok_cmd, description="test")

        def ok2_cmd(ctx, arg1):
            return True, CmdLog("ok2_cmd")
        cmd = Command("ok_cmd", ok_cmd, description="test")

    @pytest.mark.asyncio
    async def test_async_cmd_handler(self, ctx):

        async def async_cmd(ctx):
            return "return"

        cmd = Command("async_cmd", async_cmd, description="test")
        assert await cmd.execute(ctx) == "return"




@pytest.fixture
def cmd_1_arg():
    def cmd_1_arg(ctx, arg1):
        return f"cmd_1_arg {arg1}"

@pytest.fixture
def cmd_2_args():
    def cmd_2_args(ctx, arg1, arg2):
        return f"cmd_2_args {arg1} {arg2}"

class TestGroup:

    def test_group_instance(self):
        group = CmdGroup("group_name", "group")

    @pytest.mark.asyncio
    async def test_add_command(self, ctx, group):

        async def cmd1_func(ctx):
            return "return"

        cmd1 = Command("lambda", cmd1_func, description="test")
        group.add_command(cmd1)

        assert cmd1.parent == group
        with pytest.raises(CommandAlreadyRegistered):
            group.add_command(cmd1)

        assert group.get_command("lambda") == cmd1

        async def cmd2():
            # this should fail since it does not take a ctx as first argument
            pass

        # test that the callback should take at least one argument
        with pytest.raises(CommandError):
            group.add_command(Command("cmd2", cmd2, description="test"))

    def test_group_command_tree(self, group):

        def cmd1(ctx):
            pass

        def cmd2(ctx):
            pass

        group2 = CmdGroup("group2", "group")
        group2.add_command(Command("cmd1", cmd1, description="test"))
        group2.add_command(Command("cmd2", cmd2, description="test"))

        group.add_command(group2)

        assert group.get_command("group2").get_command("cmd1") == group2.get_command("cmd1")

    def test_command_alias(self, group):

        def cmd1(ctx):
            pass

        cmd = Command("cmd1", cmd1, description="test", alias="cmd1_alias")
        group.add_command(cmd)

        assert group.get_command("cmd1_alias") == cmd

    def test_walk_command_tree(self, group):
        """walks all commands from the roo command

        walk_commands is a generator
        """
        def cmd1(ctx):
            return None

        def cmd2(ctx):
            return None

        def cmd3(ctx):
            return None

        group2 = CmdGroup("group2", "desc")
        cmd_1 = Command("cmd1", cmd1, description="test")
        cmd_2 = Command("cmd2", cmd2, description="test")
        group2.add_command(cmd_1)
        group2.add_command(cmd_2)

        assert cmd_1.parent == group2
        assert cmd_1.root_parent == group2

        assert len(group2.commands) == 2 

        group.add_command(group2)
        cmd_3 = Command("cmd3", cmd3, description="test")
        group.add_command(cmd_3)
        assert cmd_3.parent == group
        assert cmd_3.root_parent == group

        assert cmd_1.root_parent == group

        commands = [cmd for cmd in group.walk_commands()]
        assert len(commands) == 4




    @pytest.mark.asyncio
    async def test_execute_no_cmd_empty_group(self, ctx, group):
        with pytest.raises(NoCommandsRegistered):
            await group.execute(ctx)

    @pytest.mark.asyncio
    async def test_execute_no_cmd_non_empty_group(self, ctx, group):
        async def cmd1_func(ctx):
            pass
        cmd1 = Command("cmd1", cmd1_func, description="test")
        group.add_command(cmd1)
        result = await group.execute(ctx)
        assert result.find("cmd1") != -1


    @pytest.mark.asyncio
    async def test_execute_group(self, ctx, group):
        # add multiple commands and subcommands
        # commands with variable number of args
        # test execute with different args
        async def cmd1_func(ctx):
            return "return"
        cmd1 = Command("cmd1", cmd1_func, description="test")

        group.add_command(cmd1)

        async def cmd2(ctx):
            return "cmd2"

        cmd2 = Command("cmd2", cmd2, description="test")  # type: ignore

        async def cmd3(ctx, arg1):
            return f"cmd3 {arg1}"

        cmd3 = Command("cmd3", cmd3, description="test")  # type: ignore

        async def cmd4(ctx, arg1, arg2):
            return f"cmd4 {arg1} {arg2}"

        cmd4 = Command("cmd4", cmd4, description="test")  # type: ignore

        sub_group = CmdGroup("sub_group", "sub group")
        sub_group.add_command(cmd2)  # type: ignore

        group.add_command(sub_group)

        sub_group2 = CmdGroup("sub_group2", "sub group2")
        sub_group2.add_command(cmd3)  # type: ignore
        group.add_command(sub_group2)


        sub_sub_group = CmdGroup("sub_sub_group", "sub sub group")
        sub_sub_group.add_command(cmd4)  # type: ignore
        sub_group2.add_command(sub_sub_group)

        assert cmd1.parent == group 
        assert cmd2.parent == sub_group  # type: ignore
        assert cmd3.parent == sub_group2  # type: ignore
        assert cmd4.parent == sub_sub_group  # type: ignore

        assert len(list(group.walk_commands())) == 7

        # executions
        # print(group.execute(ctx))
        with pytest.raises(CommandNotFound):
            await group.execute(ctx, "non_existing")
        
        # assert group.get_command("sub_group").execute(ctx, "cmd2") == "cmd2"
        assert await group.execute(ctx, "sub_group cmd2") == "cmd2"
        assert await group.execute(ctx, "sub_group2 cmd3 1") == "cmd3 1"
        assert await group.execute(ctx, "sub_group2 sub_sub_group cmd4 1 2") == "cmd4 1 2"
        assert await group.execute(ctx, "cmd1") == "return"
        assert await group.execute(ctx, "sub_group2 sub_sub_group cmd4 1 2") == "cmd4 1 2"


    @pytest.mark.asyncio
    async def test_group_class_wrapper(self, ctx, group):

        @group.group
        class TestGroup(CmdGroup):
            """Test group description"""
            pass

        assert isinstance(group.get_command("testgroup"), CmdGroup)
        assert group.get_command("testgroup").description == "Test group description"


        with pytest.raises(CommandGroupError):
            @group.group
            class TestGroup(CmdGroup):  # type: ignore
                pass

        # test custom name
        @group.group(name="custom_group_name")
        class TestGroupName:
            """Test group desc"""
            pass

        assert isinstance(group.get_command("custom_group_name"), CmdGroup)

        # test methods as commands
        @group.group
        class TestGroup2(CmdGroup):
            """Test group description"""

            def should_not_register(self, ctx):
                """desc"""
                return "failing" 

            @staticmethod
            async def cmd_cmd1(ctx):
                """cmd1 description"""
                return "cmd1_return"

            @staticmethod
            async def cmd_cmd2(ctx, arg1):
                """cmd2 description"""
                return f"cmd2_return {arg1}"

            @staticmethod
            async def cmd_cmd3(ctx, arg1, arg2):
                """cmd3 description"""
                return f"cmd3_return {arg1} {arg2}"

        assert isinstance(group.get_command("testgroup2"), CmdGroup)
        assert group.get_command("testgroup2").description == "Test group description"

        assert await group.execute(ctx, "testgroup2 cmd1") == "cmd1_return"
        assert await group.execute(ctx, "testgroup2 cmd2 1") == "cmd2_return 1"
        assert await group.execute(ctx, "testgroup2 cmd3 1 2") == "cmd3_return 1 2"

        assert group.get_command("testgroup2").get_command("cmd1").description == "cmd1 description"



class TestCommandWrapper:
    """ Tests the Group.command decorator

    It should be able to register a function as a command
    It should be usable with or without arguments
    It should make sure the wrapped function takes a Context as first arg
    """
    
    @pytest.mark.asyncio
    async def test_register_func(self, ctx, group):

        # docstring description
        @group.command
        async def cmd1(ctx):
            """cmd1 description"""
            return "cmd1_return"

        # param description
        @group.command(description="test cmd")
        async def cmd2(ctx):
            return "cmd2_return"

        # custom name
        @group.command(name="custom_cmd")
        async def cmd3(ctx):
            """desc"""
            return "cmd3_return"


        #custom alias
        @group.command(alias="alias4")
        async def cmd4(ctx):
            """desc"""
            return "cmd4_return"


        assert isinstance(group.get_command('cmd1'), Command)
        assert isinstance(group.get_command('cmd2'), Command)
        assert isinstance(group.get_command('custom_cmd'), Command)
        assert isinstance(group.get_command('cmd4'), Command)
        assert group.get_command('cmd1').description == "cmd1 description"
        assert group.get_command('cmd2').description == "test cmd"
        assert await group.execute(ctx, "cmd1") == "cmd1_return"
        assert await group.execute(ctx, "cmd2") == "cmd2_return"
        assert await group.execute(ctx, "custom_cmd") == "cmd3_return"
        assert await group.execute(ctx, "alias4") == "cmd4_return"



@pytest.fixture
def history(config):
    return CommandHistory()

@pytest.fixture
def config(tmp_path):
    # mock a config object with a history_file path for testing
    return mock.Mock(history_file=str(tmp_path) + "/history")


class TestCommandHistory:
    """Tests for CommandHistory """

    def test_add(self, history):
        history.add("cmd1")
        history.add("cmd2")
        history.add("cmd3")
        assert len(history._history) == 3
        assert history._current_index == 3
        assert history._history[0].entry == "cmd1"
        assert history._history[1].entry == "cmd2"
        assert history._history[2].entry == "cmd3"

    def test_get_previous(self, history):
        history.add("cmd1")
        history.add("cmd2")
        history.add("cmd3")
        assert history.get_previous().entry == "cmd3"
        assert history.get_previous().entry == "cmd2"
        assert history.get_previous().entry == "cmd1"
        assert history.get_previous().entry == "cmd1"   

    def test_get_next(self, history):
        history.add("cmd1")
        history.add("cmd2")
        history.add("cmd3")
        assert history.get_previous().entry == "cmd3"
        assert history.get_previous().entry == "cmd2"
        assert history.get_next().entry == "cmd3"
        assert history.get_next().entry == "cmd3"

    def test_get_match(self, history):
        history.add("cmd1")
        history.add("find this command")
        history.add("cmd3")
        assert history.get_match("find").entry == "find this command"
        assert history.get_match("non existing") == ""

    #test save/load
    def test_save(self, history, config):
        history.config = config
        history.add("cmd1")
        history.add("cmd2")
        history.add("cmd3")
        history.save()
        history.clear()
        history.load()
        assert len(history._history) == 3


class _TestCommandHistory:
    """ Tests the CommandHistory class."""


    def test_add(self, history):
        history.add("cmd1")
        history.add("cmd2")
        history.add("cmd3")
        assert len(history._history) == 3
        assert history._current_index == 3
        assert history._history[0] == "cmd1"
        assert history._history[1] == "cmd2"
        assert history._history[2] == "cmd3"

    def test_get_previous(self, history):
        history.add("cmd1")
        history.add("cmd2")
        history.add("cmd3")
        assert history.get_previous().entry == "cmd3"
        assert history.get_previous().entry == "cmd2"
        assert history.get_previous().entry == "cmd1"
        assert history.get_previous().entry == "cmd1"

    def test_get_next(self, history):
        history.add("cmd1")
        history.add("cmd2")
        history.add("cmd3")
        assert history.get_previous().entry == "cmd3"
        assert history.get_previous().entry == "cmd2"
        assert history.get_next().entry == "cmd3"
        assert history.get_next().entry == "cmd3"

    def test_get_match(self, history):
        history.add("cmd1")
        history.add("find this command")
        history.add("cmd3")
        assert history.get_match("find") == "find this command"
        assert history.get_match("non existing") == ""
