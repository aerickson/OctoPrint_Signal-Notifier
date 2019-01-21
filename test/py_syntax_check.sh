#!/usr/bin/env bash

set -e

# TODO: cd to the proper dir always somehow

echo "Checking syntax of the following python files:"
ls octoprint_signalnotifier/*.py
python -m py_compile octoprint_signalnotifier/*.py
echo "SUCCESS"
