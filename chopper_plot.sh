#!/bin/bash
script_path=$(realpath $(echo $0))
repo_path=$(dirname ${script_path})
exec python3 ${repo_path}/chopper_plot.py "$@"
