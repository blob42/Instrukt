# Quickstart

## Introduction

Instrukt is terminal-based environment for prototyping and using AI agents. It provides
a chat-like interface serving as a prompt and command line REPL at the same time,
helping you conveniently develop, instruct, and debug your AI agents. 

Instrukt features a simple interface and library for creating agents, indexes and tools.

By default, Instrukt features a Q&A agent that is tailored for conversations with
question/answering over document indexes.

Patreon supporters have access to the `alpha` version of **Docker Isolated Agents**. It
provides a safe, sandboxed environment for agents to perform their tasks on any existing
container or image. 

Instrukt was designed to allow you create custom workflows with quick feedback loops.
The inbuilt debug shell `ctrl+d` gives you access to a live IPython console in the
running app namespace. Use it to introspect and debug agents and tools.

## Custom Agents

Instrukt agents are simple python packages stored under the path `$HOME/.local/share/instrukt/agents`.

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


Take a look at the builtin agents `demo` and `chat_qa` found in the source code under
`instrukt/agent_modules` for examples of how to create your own.

## User Interface

The interface is divided in 3 main panes:

- the console: left pane
- the agent output: right pane
- the prompt-repl input: bottom

### Console Pane

The left pane serves as the main console for the app. It displays the output of system
REPL commands that start with `.` or `/`.


### Prompt Input
This is where you interact with the AI agents and app. It provides a prompt where you
can input queries and instructions for the agents to execute. Additionally, the prompt
serves as a command line REPL to interact with the *Instrukt* environment.

#### Editing with an external editor

When the prompt input is focused you can spawn an external editor to edit the input with
`ctrl-e`.

If the environment variable `EDITOR` is set, it will be used, otherwise `vim` is used.

### Monitor Pane
The right pane is dedicated the agent output alongside the user messages.

#### Agent Output

The agent output window shows the thought process and the final output of the AI agents.
It displays the conversation with agents and provides a detailed view of the agent's
activities.


#### Realm Window

This is an optional component that will be shown for agents using a certain tools such
as sandbox environment. For `docker` isolated agents, this window shows the live
terminal where the agent is attached to and displays the input sent by the agent and
output from the container.

## Index Management

The index management window allows you to manage your collections of documents that can
be used by agents for question-answering scenarios. 

Indexes are used to provide more context to the agent. You can create indexes and attach
them to active agents at any time.

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
