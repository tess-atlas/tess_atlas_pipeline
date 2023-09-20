import subprocess
import time
import os
from datetime import datetime
from pathlib import Path

CWD = Path(__file__).parent.absolute()

UNFINISHED_STATES = ["PENDING", "RUNNING", "REQUEUED", "RESIZING", "SUSPENDED"]

SSH_CONFIG = CWD / "ssh" / "ssh-config"
CMD = f"ssh -F {SSH_CONFIG} jc {{}}"
RSYNC = f'rsync -e "ssh -F {SSH_CONFIG}" -avzP jc-copy:{{}} {{}}'


def log(*args):
    line = '-' * os.get_terminal_size().columns
    tstring = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{line}\n[{tstring}]", *args, f"\n{line}")


def shell(cmd, failfast=False):
    log('Running:', cmd)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    result.stdout = result.stdout.strip()
    result.stderr = result.stderr.strip()
    print(result.stdout)
    print(result.stderr)
    if failfast:
        result.check_returncode()
    return result


def jcrun(command):
    cmd = CMD.format(command)
    return shell(cmd)


def rsync(from_path, to_path="."):
    cmd = RSYNC.format(from_path, to_path)
    return shell(cmd)


def get_job_ids(jobname):
    result = jcrun(f"get-job-ids {jobname}")
    job_ids = result.stdout.split("\n")
    return job_ids


def get_job_status(jobid):
    result = jcrun(f"status {jobid}")
    return result.stdout


def generate_tess_job(jobname):
    result = jcrun(f"generate {jobname}")
    result.check_returncode()


def submit_script(jobname):
    result = jcrun(f"submit {jobname}")
    result.check_returncode()


def wait_for_jobs(job_ids, wait=5):
    if type(job_ids) == int:
        jobids = [job_ids]
    elif job_ids is None:
        jobids = []
    else:
        jobids = list(job_ids)

    log("Waiting for the following job IDs to finish:")
    for id in jobids:
        print(id)
    print()

    njobs = len(jobids)
    finished = [False] * njobs
    states = [None] * njobs

    while not all(finished):
        for i, id in enumerate(jobids):
            status = get_job_status(id)
            if status not in UNFINISHED_STATES:
                finished[i] = True
                states[i] = status
        if not all(finished):
            time.sleep(wait)

    log("All jobs finished.")
    return states


def get_results(jobname):
    log("Getting results from:", jobname)
    # result = rsync()
