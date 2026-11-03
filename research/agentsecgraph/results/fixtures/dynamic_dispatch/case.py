import subprocess

def run(command):
    execute = getattr(subprocess, "run")
    return execute(command)
