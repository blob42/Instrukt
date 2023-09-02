# Installation Guide

## Minimum requirements

- Python 3.9 or newer
- g++ (required for building chroma-hnswlib)
- a modern terminal emulator (e.g. alacritty, kitty, st, urxvt, xterm)

## Install from pip repository

`pip install instrukt[all]`

## Installing from source

- Clone the repository

- **Make sure you are using the latest pip** `pip install -U pip`
If the installation fails with the package `chromadb` it means
your pip version is old.

- Install poetry with `pip install poetry`
- To do a comprehensive install with all features use:

```sh
    poetry install -E all
```

## Using textual dev console to troubleshoot the app

- If you did not install the dependencies using poetry make sure to install textual dev
  dependencies with: `pip install textual[dev]`

- From the project's root directory run: `textual run instrukt.app:InstruktApp`

## Dependencies

- libmagic: scanning and file type detection
- sqlite: caching
- fzf for fuzzy selecting.
- xsel or xclip for copying messages to the clipboard.
- docker: [optional] for Patreons with access to the docker based agents.

