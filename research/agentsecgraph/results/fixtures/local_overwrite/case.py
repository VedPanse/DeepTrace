import subprocess

def run(command):
    value = command
    value = "printf synthetic"
    return subprocess.run(value)
