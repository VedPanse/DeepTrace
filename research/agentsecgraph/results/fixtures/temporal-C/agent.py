from config import allowed
import subprocess

def run(command):
    if allowed(command):
        return subprocess.run(command, shell=False)
