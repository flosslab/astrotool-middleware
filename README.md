# AstroTool Middleware

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
