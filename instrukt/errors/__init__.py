"""Instrukt errors"""

# custom error class for command errors
class InstruktError(Exception):
    """An error class representing an error that occurred in a command.

    Errors shoudl be rich renderables.
    """
    pass

class CommandError(InstruktError):
    pass

class CommandGroupError(CommandError):
    pass

class CommandHandlerError(CommandError):
    pass

class CommandNotFound(CommandError):
    pass

class NoCommandsRegistered(CommandError):
    pass

class UnknownCommand(CommandError):
    pass

class InvalidArguments(CommandError):
    pass

class CommandAlreadyRegistered(CommandError):
    pass

class AgentError(InstruktError):
    """Agents errors."""
    pass

class IndexError(InstruktError):
    pass

class ToolError(InstruktError):
    pass

class LoaderError(InstruktError):
    pass

class ConfigError(InstruktError):
    pass
