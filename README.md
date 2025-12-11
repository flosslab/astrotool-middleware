# AstroTool Middleware

> CN ICSC Program Code CN00000013 (PNRR) Mission 4, "Istruzione e Ricerca" – Component 2, "Dalla Ricerca all’Impresa"
> – Investment Line 1.4, Funded by the European Union – NEXTGENERATIONEU – Spoke 3, CUP C53C22000350006

**Midleware Paraview**

This middleware provides the communication layer between the **AstroTool Client (Web/Electron)** and the **HPC remote
environment**.
It enables high-performance visualization workflows by exposing a Python API that manages wslink connections to
ParaView, allowing the client to interactively render VTI / VTP preprocessed datasets

## Description

It is a middleware based on VTK libraries.
The main goal is render a VTI object remotely.

## Requirements

- python 3.10.4
- pyenv (Optional)

## Install

### Standar way:

```bash
python -m venv venv
source venv/bin/activate
pip install 
```

### Pyenv way:

```bash
pyenv install
pyenv local
python -m venv venv
source venv/bin/activate
pip install 
```

## Usage

Current default params are:

- HOST: 0.0.0.0
- PORT: 1234

```bash
python middlware.py --host 0.0.0.0 --port 1234
```
