from config import get_command
import subprocess

def run():
    command = get_command()
    return subprocess.run(command)
