import subprocess
import os

DOCKER_HOST = os.getenv("DOCKER_HOST_SSH")  # user@VPS_IP

def docker_run(container_name: str):
    cmd = [
        "ssh", DOCKER_HOST,
        "docker", "run", "-d",
        "--name", container_name,
        "--cpus=1.0",
        "--memory=512m",
        "python:3.11-slim",
        "sleep", "infinity"
    ]
    subprocess.run(cmd, check=True)

def docker_stop(container_name: str):
    cmd = ["ssh", DOCKER_HOST, "docker", "rm", "-f", container_name]
    subprocess.run(cmd, check=True)
