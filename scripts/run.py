"""
Run script for executing pyTAKES. Relies on config file defined according to pytakes/schema.py
"""
from pytakes.run.runner import run_config

if __name__ == '__main__':
    import sys

    run_config(sys.argv[1])
