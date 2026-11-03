import subprocess

def run(command):
    if command == "status":
        return subprocess.run(command)
