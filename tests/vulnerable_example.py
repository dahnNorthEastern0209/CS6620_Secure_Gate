import subprocess

def execute_command(user_input):
    subprocess.run(user_input, shell=True)