# Quickstart

## Introduction

Welcome to Instrukt ! This is your handy terminal-based interface for running and prototyping AI agents. Instrukt provides chat-like interface serving as a prompt and REPL at the same time, helping you conveniently develop, instruct, and debug your AI agents. 

It leverages LangChain and provides extra utilities with a simple interface to add vectorstore indexes and tools, which can be attached to any agent on the fly.

By default, Instrukt features a Q&A agent that is tailored for conversations with question/answering over document indexes.

Patreon supporters have access to an early preview of the **Docker Agent**. It provides a safe, sandboxed environment for agents to perform their tasks on any existing container or image. 

Instrukt encourages you to create custom workflows with a quick feedback loop while testing agents. The developer console `press D` gives you access to a live IPython console in the running namespace to introspect and debug agents and tools.

## Custom Agents

Instrukt agents are simple python packages stored under the path `$HOME/.config/instrukt/agents`.

You can create your own agents and share them with others. You can also set a custom path in the configuration file `~/.config/instrukt/instrukt.yml`. 

### Creating a custom agent

To define a custom agent you need to:

1. Setup a python package under the configured path. (don't forget the __init__.py file)

2. Create a `manifest.json`:

The manifest file must define the following:
- name: the name of the agent without spaces. Must be same as the package name.
- description: a description that will be displayed in the agents selection menu.
- version

3. Create an entry point named `main.py`

You must create a class that implements the `InstruktAgent` base class.


Take a look at the builtin agents `demo` and `chat_qa` found in the source code under `instrukt/agent_modules` for examples of how to create your own.

## User Interface

The interface is divided in two main parts: *The Console Panel* and the *Monitor Panel*

### Console-Prompt Panel

Located on the left side of the interface, this is where you interact with the AI agents. It provides a prompt where you can input queries and instructions for the agents to execute.
Additionally, the prompt serves as a command line REPL to interact with the *Instrukt* environment.

#### Using an External Editor

When the prompt input is focused you can spawn an external editor to edit the input with `ctrl-e`.

If the environment variable `EDITOR` is set, it will be used, otherwise a `vim` is used.

### Monitor Panel
On the right side of the interface is the Monitor Panel where you will find the agent output alongside the user messages.

### Agent Output

The agent output window shows the thought process and the final output of the AI agents. It provides a detailed view of the agent's activities and can be used to understand how the agent is processing the tasks and commands.

### Realm Window

The _realm window_ is an optional component that can be displayed for agents using a sandbox environment. This window shows the live terminal where the agent is attached to and displays the input sent by the agent and output from the container.

## Index Management

The index management window allows you to manage and create new vectorstore indexes. These indexes can be used to provide more context to the agent's underlying LLM. You can create indexes and attach them to active agents at any time during the agent's lifecycle. 

## FAQ

### Terminal Colors

If the colors seem off make sure to:

- Try to set the `TERM=xterm-256color`.

- Try on a different and modern terminal.
- Make sure your terminal that supports 256 color palette.


### Select And Copy

#### Copy Agent Replies

**Click** on a reply from an agent to copy its content to the clipboard.
Make sure to install a clipboard utility like xsel or xclip if you're on Linux.

#### Terminal Select/Copy

Running a Textual app puts your terminal in to *application mode* which disables clicking and dragging to select text.
Most terminal emulators offer a modifier key which you can hold while you click and drag to restore the behavior you
may expect from the command line. The exact modifier key depends on the terminal and platform you are running on.

- **iTerm** Hold the OPTION key.
- **Gnome Terminal** Hold the SHIFT key.
- **Windows Terminal** Hold the SHIFT key.

Refer to the documentation for your terminal emulator, if it is not listed above.

## Nerdfonts Icons

You can activate nerdfont icons for a compact interface by setting the appropriate
setting in: `~/.config/instrukt/instrukt.yml`:

```yaml
interface:
  nerd_fonts: true

```

## Debug mode

You can quickly activate debug mode with the command `%debug` in the prompt.

Currently mostly useful for index creation, it will enable more verbose output in the
index management log console.
