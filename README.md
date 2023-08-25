#  Instrukt

 **An AI Commander at your fingertips**

<p align="center">
    <a href="https://www.youtube.com/watch?v=_mkIoqiY0dE" rel="nofollow">
        <img src="https://camo.githubusercontent.com/e5ad6a03ceca6336a57e6da345659ca34ab7fff5d36eec88f986ea56e66aa8f5/68747470733a2f2f696d672e796f75747562652e636f6d2f76692f6a674c4d4b6f695f3364382f302e6a7067" alt="Instrukt v0.4.0 Demo" width="500">
    </a>
</p>

**NOTE**: This is an alpha release, expect bugs and API changes.

## Introduction

Instrukt is a terminal-based environment for AI productivity and development. It offers a platform where users can:

- :robot: Create and instruct modular AI agents
- :card_file_box: Generate document indexes for question-answering
- :toolbox: Create and attach tools to any agent

Instrukt agents are simple **drop-in Python packages** that can be extended, shared with others, attached to tools, and augmented with document indexes. Instruct them in natural language and, for safety, attach them to inside secure containers (currently implemented with Docker) to perform tasks in their dedicated, sandboxed space :shield:.

Instrukt is designed with with an easy interface and API for composing and using agents. It is built with [LangChain](https://github.com/hwchase17/langchain), extending its base agents and tools. 

For agent developers, it offers a **builtin IPython console** for on-the-go debugging and introspection and allows for quick development and testing of `Langchain` agents in an interactive environment.

Built with: [Langchain](https://github.com/hwchase17/langchain), [Textual](https://github.com/Textualize/textual), [Chroma](https://github.com/chroma-core/chroma)

**Consulting Services**: Need help with Langchain or AI development/deployment ? You can reach out to me at [contact@blob42.xyz](mailto://contact@blob42.xyz)

## TOC

- [Usage](#usage)
- [Features](#features)
- [Supported Platforms](#supported-platforms)
- [LLM Models](#llm-models)
- [Document Indexes and Question-Answering](#document-indexes-and-question-answering)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Patreon](#patreon)
- [Social](#social)
- [Vision](#vision)
- [License](#license)

## Usage

### Setup

**note**: the package is not yet released on PyPi

**From pre-built package**:

- download and install the released package with `pip install package_name[tools]`.

#### From source:

- Make sure the latest version of `poetry` is installed.
- Set your virtualenv
- Clone the repository
- Run `poetry install -E tools --with dev` 
- This will install Instrukt including extra tools for agents. 

[See the installation guide for more details](docs/install.md)

### Requirements:

- Export `OPENAI_API_KEY` environment variable with your OpenAI API key.
- Use a modern terminal that supports 24-bit color and mouse input.

### Running:

- Type `instrukt`.
- On the first run, it will create a config file in
  `~/.config/instrukt/instrukt.yml`

#### From source

- If you did not install the dependencies using poetry make sure to install textual dev dependencies with: `pip install textual[dev]`

- From the project's root run: `textual run instrukt.app:InstruktApp`

### Default Agents:

**Chat Q&A**: A simple conversational agent. Attach document indexes and tools to create a question-answering agent. It also serves as an example for making custom agents.

**Demo**: The same agent used in the demo video.

## Features 

#### :computer: Keyboard and Mouse Terminal Interface:

- A terminal-based interface for power keyboard users to instruct AI agents without ever leaving the keyboard.
- Mouse support and [Rich](https://github.com/Textualize/rich) colorful agent outputs such as markdown and source
  code thanks to the [Textual](https://github.com/Textualize/textual) TUI library.
- Run Instrukt in bare metal and access it remotely via SSH and/or terminal
  multiplexer.

#### :robot: Custom AI Agents:
- Design your [own agents](docs/quickstart.md#custom-agents) and custom tools. 
- Agents are simple python packages can be shared and loaded by other users.

#### :wrench: Tools:
- Use the pre-defined toolset or design your own tools.
- Attach or detach tools to agents on-the-go, tailoring your AI workflows to your needs.

#### :books: Chat with your code and documents:
- Index your data and let agents retrieve it for question-answering. 
- Create and organize your indexes with an easy UI.
- Index creation will **auto detect programming languages** and optimize the splitting/chunking
  strategy accordingly.

#### :zap: Prompt Console :
- Integrated REPL-Prompt for quick interaction with agents, and a fast feedback loop for development and testing.
- Add your own custom commands to automate repetitive tasks.
- Builtin prompt/chat history to quickly edit/correct messages.
- Use an external editor for editing messages (e.g. vim). `ctrl+e`

#### :bird: LangChain:

- Leverage the LangChain ecosystem to automate anything.
- Extensible API for integrating with other frameworks.

#### :microscope: Developer Console:
Debug and introspect agents using an in-built IPython console. `ctrl+d`

#### :shield: Secure Containers:

- Run agents inside secure docker containers for safety and privacy.
- Use [gVisor](https://gvisor.dev/) runtime for a full isolation of the agent.

**note**: The docker agent is only available to [Patreon](#patreon) supporters as an early preview.


## Document Indexes and Question-Answering

- Indexes can be  created using OpenAI or locally hosted embedding models.
- They are stored locally using the [Chroma](https://github.com/chroma-core/chroma) embedding database.
- You create and manage indexes using the **Index Management** UI (press `i`)
- Indexing a directory will auto detect programming languages and use an appropriate
  splitting strategy optimized for the target language.
- Indexes can be attached to any agent as a **retrieval** tool using the `index` menu
  in the top of the agent's window.
- Once an index is attached you can do question-answering and the agent will
  lookup your indexed documents whenever they are mentioned or needed.

## Supported platforms:

- Linux/Mac.
- Windows tested under WSL2.

### LLM Models

- Currently only **OpenAI** supported.
- Using private local models is the **next priority**.

## Roadmap

- [ ] Private local models
    - [ ] Use text-generation-webui API
    - [ ] Emulate [PrivateGPT](https://github.com/imartinez/privateGPT)
    - [ ] Use a self hosted [go-skynet/LocalAI](https://github.com/go-skynet/LocalAI)
    - [x] Local embeddings
        - [x] HF SetenceTransformers or other embeddings models.
        - [x] [Instructor Embeddings](https://instructor-embedding.github.io/)
- Indexing and embeddings
    - [x] Index directories and auto detect content. ( see `AutoDirLoader`)
    - [x] Detect programming languages and use the appropriate splitter.
    - [ ] Load a git repository from URL
    - [ ] Load any webpage / website.

- [ ] Documentation
    - [ ] Creating agents
    - [ ] Creating tools
    - [ ] Indexing and chat with documents and source code.
    - [ ] Example use cases  
    - [ ] Tutorials for users non familiar with AI/LLM terms.

## Contributing

Any contribution, feedback and PR is welcome !

You can help with:

- Testing and creating Issues for bugs or features that would be useful.
- If you have technical skills, you are welcome to create a PR.
- If you don't have technical skills you can help with documentation, adding examples
  and tutorials or create new user stories.

## Patreon

By becoming a patron, you will help me continue committing time to the development of Instrukt and bring to life all the planned features. Check out the [Patreon page](https://www.patreon.com/Instrukt) for more details on the rewards for early supporters.

## Social

Join the [Discord](https://discord.gg/wxRwRcJ7) server to keep updated on the progress or ask for help.

## Vision

I believe that AI should be accessible to everyone and not a walled garden for big corporations and SaaS services. 

I hope my contributions will help create tools that empower users without compromising their freedoms. The long-term goal for Instrukt is to make it usable with minimal reliance on external services, giving users the choice to opt for local models and self-hosted services.

# License

Copyright (c) 2023 Chakib Ben Ziane. All Rights Reserved.

Instrukt is licensed with a AGPL license, in short this means that it can be used by anyone for any purpose. However, if you decide to make a publicly available instance your users are entitled to a copy of the source code including all modifications that you have made (which needs to be available trough an interface such as a button on your website), you may also not distribute this project in a form that does not contain the source code (Such as compiling / encrypting the code and distributing this version without also distributing the source code that includes the changes that you made. You are allowed to distribute this in a closed form if you also provide a separate archive with the source code.).
