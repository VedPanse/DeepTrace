import subprocess

def run(command):
    if command != "status":
        raise ValueError("not allowed")
    return subprocess.run(command)
