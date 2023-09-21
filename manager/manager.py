import subprocess
import time
import os
from datetime import datetime
from pathlib import Path

CWD = Path(__file__).parent.absolute()

UNFINISHED_STATES = ["PENDING", "RUNNING", "REQUEUED", "RESIZING", "SUSPENDED"]

SSH_CONFIG = CWD / "ssh" / "ssh-config"
CMD = f"ssh -F {SSH_CONFIG} worker {{}}"
RSYNC = f'rsync -e "ssh -F {SSH_CONFIG}" -avzP datamover:{{}} {{}}'


def log(*args):
    line = "-" * os.get_terminal_size().columns
    tstring = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{line}\n[{tstring}]", *args, f"\n{line}")


def _shell(cmd, failfast=True):
    log("Running:", cmd)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    result.stdout = result.stdout.strip()
    result.stderr = result.stderr.strip()
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if failfast:
        result.check_returncode()
    return result


def worker_run(command, failfast=True):
    return _shell(CMD.format(command), failfast=failfast)


def rsync(from_path, to_path="."):
    return _shell(RSYNC.format(from_path, to_path))


def get_job_ids(jobname):
    result = worker_run(f"get-job-ids {jobname}")
    job_ids = result.stdout.split("\n")
    return job_ids


def get_job_status(jobid):
    result = worker_run(f"status {jobid}")
    return result.stdout


def generate_tess_job(jobname):
    worker_run(f"generate {jobname}")


def submit_tess_job(jobname):
    worker_run(f"submit {jobname}")


def wait_for_jobs(job_ids, wait=5):
    if type(job_ids) == int:
        jobids = [job_ids]
    elif job_ids is None:
        jobids = []
    else:
        jobids = list(job_ids)
    del job_ids

    njobs = len(jobids)
    finished = [False] * njobs
    states = [None] * njobs

    while True:
        log("Waiting for the following job IDs to finish:")
        for i, id in enumerate(jobids):
            if not finished[i]:
                print(id)
        for i, id in enumerate(jobids):
            if not finished[i]:
                status = get_job_status(id)
                if status not in UNFINISHED_STATES:
                    finished[i] = True
                    states[i] = status
        if all(finished):
            break
        else:
            time.sleep(wait)

    log("All jobs finished.")
    return states


def rsync_tess_results(jobname, save_path):
    log("Getting results from:", jobname, "rsync-ing them to:", save_path)
    print("Not implemented")
    # result = rsync()
