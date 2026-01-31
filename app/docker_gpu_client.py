import subprocess
import os

GPU_DOCKER_HOST = os.getenv("GPU_DOCKER_HOST_SSH")  # user@GPU_VPS_IP

def gpu_docker_run(container_name: str):
    cmd = [
        "ssh", GPU_DOCKER_HOST,
        "docker", "run", "-d",
        "--gpus", "all",
        "--name", container_name,
        "--memory=4g",
        "nvidia/cuda:12.1-base",
        "sleep", "infinity"
    ]
    subprocess.run(cmd, check=True)

def gpu_docker_stop(container_name: str):
    cmd = ["ssh", GPU_DOCKER_HOST, "docker", "rm", "-f", container_name]
    subprocess.run(cmd, check=True)
