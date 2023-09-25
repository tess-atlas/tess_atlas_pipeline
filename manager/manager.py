import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path

CWD = Path(__file__).parent.absolute()

UNFINISHED_STATES = ["PENDING", "RUNNING", "REQUEUED", "RESIZING", "SUSPENDED"]

SSH_CONFIG = CWD / "ssh" / "ssh-config"
CMD = f"ssh -F {SSH_CONFIG} worker -- {{}}"
RSYNC = f'rsync -e "ssh -F {SSH_CONFIG}" -avzP datamover:{{}} {{}}'

MAX_RETRIES = 10


def log(*args, level="INFO"):
    tstring = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if level == "ERROR":
        colour = "\033[31m"
    else:
        colour = "\033[92m"
    print(f"{colour}[{tstring}]\033[0m", *args)


def _shell(cmd, capture_output=True, failfast=True, print_output=True):
    log("Running:", cmd)
    result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)

    if capture_output:
        result.stdout = result.stdout.strip()
        result.stderr = result.stderr.strip()
        if print_output:
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)

    if failfast:
        result.check_returncode()
    return result


def worker_run(command, capture_output=True, print_output=True):
    return _shell(CMD.format(command), capture_output=capture_output, print_output=print_output)


def rsync(from_path, to_path="."):
    return _shell(RSYNC.format(from_path, to_path), capture_output=False)


def get_job_status(jobid):
    result = worker_run(f"status {jobid}")
    return result.stdout


def generate_tess_job(jobname):
    worker_run(f"generate {jobname}")


def submit_tess_job(jobname):
    result = worker_run(f"submit {jobname}", print_output=False)
    job_ids = result.stdout.split("\n")
    return job_ids


def wait_for_jobs(job_ids, wait=10):
    if type(job_ids) == int:
        jobids = [job_ids]
    elif job_ids is None:
        jobids = []
    else:
        jobids = list(job_ids)
    del job_ids

    njobs = len(jobids)

    # Wait for jobs to enter sacct

    sacct = [False] * njobs
    nretries = 0
    sacct_lag = 5

    while not all(sacct):
        nretries += 1

        time.sleep(sacct_lag)

        if nretries == MAX_RETRIES:
            log(f"ERROR: reached max number of retries: {MAX_RETRIES}", level="ERROR")
            sys.exit(1)

        for i, j_id in enumerate(jobids):
            if sacct[i]:
                continue
            else:
                status = get_job_status(j_id)
                if status != "":
                    sacct[i] = True

        if not all(sacct):
            log(f"Some jobs not found in sacct yet, retrying in {sacct_lag} seconds...")

    finished = [False] * njobs
    states = [None] * njobs

    while True:
        log("---> Checking jobs:", [jobids[i] for i in range(njobs) if not finished[i]])
        for i, j_id in enumerate(jobids):
            if not finished[i]:
                status = get_job_status(j_id)
                if status not in UNFINISHED_STATES:
                    finished[i] = True
                    states[i] = status
        if all(finished):
            break
        else:
            log("Jobs IDs remaining:", [jobids[i] for i in range(njobs) if not finished[i]])
            log(f"<--- Waiting {wait} seconds before checking again...")
            time.sleep(wait)

    log("All jobs finished!")
    return states


def rsync_tess_results(jobname, save_path):
    log("Getting results from:", jobname, "rsync-ing them to:", save_path)
    print("Not implemented")
    fpath = Path(jobname) / "toi*"
    return rsync(fpath, save_path)
