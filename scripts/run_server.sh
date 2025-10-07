#!/bin/bash

# Activate virtual environment
#source venv/bin/activate
# for cygwin need to change to  ./venv/Scripts/active
source ./venv/Scripts/activate
export PYTHONIOENCODING=utf-8
# Run the server
python ./src/coding_server.py
