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


def get_job_states(jobid):
    # Returns a list of states, since jobid can be a jobarray id.
    # (JobArrays contain multiple jobs, and thus multiple states)
    result = worker_run(f"status {jobid}", print_output=False)
    job_states = result.stdout.split("\n")
    return job_states


def generate_tess_job(jobname):
    worker_run(f"generate {jobname}")


def submit_tess_job(jobname):
    result = worker_run(f"submit {jobname}", print_output=False)
    submitted_ids = result.stdout.split("\n")
    return submitted_ids


def wait_for_jobs(ids, wait=10):
    # Always work with a list
    if type(ids) == int:
        jobarray_ids = [ids]
    elif ids is None:
        jobarray_ids = []
    else:
        jobarray_ids = list(ids)
    del ids

    # Wait for batches to enter sacct
    wait_for_sacct(jobarray_ids)

    nbatches = len(jobarray_ids)
    finished = [False] * nbatches
    states = [None] * nbatches
    fstring = "{: >20} {: >20}"

    log("===> Waiting for jobs to finish:")
    while True:
        for i, jobarray in enumerate(jobarray_ids):

            if not finished[i]:
                job_states = get_job_states(jobarray)

                print(fstring.format("Job ID", "State"))
                for idx, jstate in enumerate(job_states):
                    print(fstring.format(f"{jobarray}_{idx}", jstate))

                if any([ state not in UNFINISHED_STATES for state in job_states ]):
                    finished[i] = True
                    states[i] = job_states

        if all(finished):
            break
        else:
            log("Jobs IDs remaining:", [jobarray_ids[i] for i in range(nbatches) if not finished[i]])
            log(f"<--- Waiting {wait} seconds before checking again...")
            time.sleep(wait)

    log("<=== All jobs finished")
    return states


def rsync_tess_results(jobname, save_path):
    log("Getting results from:", jobname, "rsync-ing them to:", save_path)
    rsync(Path(jobname) / "toi*", save_path)
    rsync(Path(jobname) / "run_stats.csv", save_path)


def wait_for_sacct(jobarray_ids, wait=5, max_retries=10):

    in_sacct = [False] * len(jobarray_ids)
    nretries = 0

    while not all(in_sacct):
        nretries += 1

        time.sleep(wait)

        if nretries == max_retries:
            log(f"ERROR: reached max number of retries: {max_retries}", level="ERROR")
            sys.exit(1)

        for i, jobarray in enumerate(jobarray_ids):
            if in_sacct[i]:
                continue
            else:
                job_states = get_job_states(jobarray)
                if job_states != "":
                    in_sacct[i] = True

        if not all(in_sacct):
            log(f"Some jobs not found in sacct yet, retrying in {wait} seconds...")
