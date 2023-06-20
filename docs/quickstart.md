# Overview

## Introduction

Welcome to Instrukt! This is your handy terminal-based interface for running and prototyping AI agents. Instrukt provides chat-like interface serving as a prompt and REPL at the same time, helping you conveniently develop, instruct, and debug your AI agents. 

Instrukt leverages LangChain and provides extra utilities with a simple interface to add vectorstore indexes `press I` and tools, which can be attached to an agent in real time.

By default, Instrukt features a Q&A agent that is tailored for conversations with question/answering over document indexes.

Patreon supporters have also access to an early preview of the **Docker Agent**. It provides a safe, sandboxed environment for agents to perform their tasks on any existing container or image. 

Instrukt encourages you to create custom workflows with a quick feedback loop while testing agents. The developer console `press D` gives you access to a live IPython console in the running namespace to introspect and debug agents and tools.

### Custom Agents

Instrukt agents a simple python packages that live in the `agent_modules` folder within
the package. You can create your own agents and share them with others. 

Take a look at the `demo` and `chat_qa` agents for examples of how to create your own.

# User Interface

The interface is divided in two main parts: *The Console Panel* and the *Monitor Panel*

## Console Panel

Located on the left side of the interface, this is where you interact with the AI agents. It provides a prompt where you can input queries and instructions for the agents to execute.
Additionally, the prompt serves as a command line REPL to interact with the *Instrukt* environment.

## Monitor Panel
On the right side of the interface is the Monitor Panel where you will find the agent output alongside the user messages.

### Agent Output

The agent output window shows the thought process and the final output of the AI agents. It provides a detailed view of the agent's activities and can be used to understand how the agent is processing the tasks and commands.

### Realm Window

The _realm window_ is an optional component that can be displayed for agents using a sandbox environment. This window shows the live terminal where the agent is attached to and displays the input sent by the agent and output from the container.

## Index Management

The index management window allows you to manage and create new vectorstore indexes. These indexes can be used to provide more context to the agent's underlying LLM. You can create indexes and attach them to active agents at any time during the agent's lifecycle. 

# FAQ

## Terminal Colors

If the colors seem off make sure to:

- Try to set the `TERM=xterm-256color`.

- Try on a different and modern terminal.
- Make sure your terminal that supports 256 color palette.


## Select And Copy

### Copy Agent Replies

**Click** on a reply from an agent to copy its content to the clipboard.
Make sure to install a clipboard utility like xsel or xclip if you're on Linux.

### Terminal Select/Copy

Running a Textual app puts your terminal in to *application mode* which disables clicking and dragging to select text.
Most terminal emulators offer a modifier key which you can hold while you click and drag to restore the behavior you
may expect from the command line. The exact modifier key depends on the terminal and platform you are running on.

- **iTerm** Hold the OPTION key.
- **Gnome Terminal** Hold the SHIFT key.
- **Windows Terminal** Hold the SHIFT key.

Refer to the documentation for your terminal emulator, if it is not listed above.

## Nerdfonts Icons

You can activate nerdfont icons for a compact interface by setting the appropriate
setting in `~/.config/instrukt/instrukt.yml`:


