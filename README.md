#  Instrukt

 **An AI Commander at your fingertips**

<p align="center">
    <a href="https://www.youtube.com/watch?v=_mkIoqiY0dE" rel="nofollow">
        <img src="https://camo.githubusercontent.com/e5ad6a03ceca6336a57e6da345659ca34ab7fff5d36eec88f986ea56e66aa8f5/68747470733a2f2f696d672e796f75747562652e636f6d2f76692f6a674c4d4b6f695f3364382f302e6a7067" alt="Instrukt v0.4.0 Demo" width="500">
    </a>
</p>

**NOTE**: This is an alpha release, expect bugs and API changes.

## Introduction

Instrukt is a terminal-based tool for AI productivity and development. It offers a platform where users can:

- :robot: Create and instruct modular AI agents
- :card_file_box: Generate document indexes for question-answering with AI agents
- :toolbox: Create or use tools and attach them to any agent

Instrukt is designed with with an easy interface and API for composing and using AI agents. It plays nicely with [LangChain](https://github.com/hwchase17/langchain), extending its base agents and tools. 

Instrukt agents are simple **drop-in Python packages** that can be extended, shared with others, attached to tools, and augmented with document indexes. Instruct them in natural language and, for safety, attach them to inside secure containers (currently implemented with Docker) to perform tasks in their dedicated, sandboxed space :shield:.

For agent developers, it offers a **builtin IPython console** :microscope: for on-the-go debugging and introspection and allows for quick development and testing of `Langchain` agents in an interactive environment.


## TOC

- [Usage](#usage)
- [Features](#features)
- [Supported Platforms](#supported-platforms)
- [LLM Models](#llm-models)
- [Document Indexes and Question-Answering](#document-indexes-and-question-answering)
- [Patreon](#patreon)
- [Social](#social)
- [Roadmap](#roadmap)
- [Vision](#vision)
- [License](#license)

## Usage

### Setup

**From pre-built package**:

- download and install the released package with `pip package_name[tools]`.

#### From source:
- Make sure the latest version of `poetry` is installed.
- Set your virtualenv
- Clone the repository
- Run `poetry install -E tools`
- This will install Instrukt including extra tools for agents. 

[See the installation guide for more details](docs/install.md)

### Requirements:

- Export `OPENAI_API_KEY` environment variable with your OpenAI API key.
- Use a modern terminal that supports 24-bit color.

### Running:

- type `instrukt`.

### Default Agents:

**Chat Q&A**: A simple conversational agent. Attach it to indexes and tools to create a question-answering agent. It also serves as an example of how to create an agent.

## Features 

#### :computer: Keyboard and Mouse Terminal Interface:
A terminal-based interface that prioritizes ease-of-use, keeping you focused on the task at hand. Run Instrukt in bare metal and access it remotely via SSH.

#### :robot: Custom Agents:
Design your own AI agents and custom tools. Agents are simple python packages can be shared and loaded by other users.

#### :wrench: Tools:
Use the pre-defined toolset or design your own. Connect or disconnect tools to agents on-the-go, tailoring your AI workflows to your needs.

#### :books: Vectorstore Indexes:
Create indexes over your data, attach them to agents, and use them for question-answering.

#### :zap: Fast Feedback:
Integrated REPL-Prompt for quick interaction with agents, and a fast feedback loop for development and testing.

#### :bird: LangChain:
Built to work seamlessly with the LangChain with an extensible API for integrating with other frameworks.

#### :microscope: Developer Console:
Debug and introspect agents using an in-built IPython console.


## Document Indexes and Question-Answering

- Indexes are created using OpenAI embeddings.
- They are stored locally using the [Chroma](https://github.com/chroma-core/chroma)
embedding database.
- You create and manage indexes using the **Index Management** UI press capital `I`
- An index can be attached to any agent as a **retrieval** tool using the `index` menu
  from the agent's window.
- Once an index is attached you can do question-answering with your agent and it will
  automatically lookup your index whenever its name is mentioned.

**note**: This currently using naive document chunking/splitting heuristics without
any optimizations. The quality of document retrieval will be greatly improved in future
iterations.

## Supported platforms:

- Linux/Mac.
- Windows tested under WSL2.

### LLM Models

Currently only **OpenAI** supported, fully private local models is the next priority.


## Patreon

By becoming a patron, you will help me continue committing time to the development of Instrukt and bring to life all the planned features. Check out the [Patreon page](https://www.patreon.com/Instrukt) for more details on the rewards for early supporters.

## Social

Join the [Discord](https://discord.gg/wxRwRcJ7) server to keep updated. 

## Roadmap

Here are the next top priorities.

- [ ] documentation
    - [ ] creating agents
    - [ ] creating tools
- [ ] run local private models
    - [ ] local llm models
    - [ ] local embeddings model

## Vision

I believe that AI should be accessible to everyone and not a walled garden for big corporations and SaaS services. 

I hope my contributions will help create tools that empower users without compromising their freedoms. The long-term goal for Instrukt is to make it usable with minimal reliance on external services, giving users the choice to opt for local models and self-hosted services.

# License

Copyright (c) 2023 Chakib Ben Ziane. All Rights Reserved.

Instrukt is licensed with a AGPL license, in short this means that it can be used by anyone for any purpose. However, if you decide to make a publicly available instance your users are entitled to a copy of the source code including all modifications that you have made (which needs to be available trough an interface such as a button on your website), you may also not distribute this project in a form that does not contain the source code (Such as compiling / encrypting the code and distributing this version without also distributing the source code that includes the changes that you made. You are allowed to distribute this in a closed form if you also provide a separate archive with the source code.).
