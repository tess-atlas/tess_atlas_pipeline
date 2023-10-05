import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Union, List
from subprocess import CompletedProcess
from job import JobState, Job

CWD = Path(__file__).parent.absolute()

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


def _log_run_cmd(cmd):
    if " -- " not in cmd:
        log("Running:", cmd)
    else:
        cmd_start, end = cmd.split(" -- ")
        log("Running:", cmd_start, " -- ", "\033[1;35m", end, "\033[0m")


def _shell(cmd, capture_output=True, failfast=True, print_output=True) -> Union[CompletedProcess, None]:
    """
    Run a shell command, and optionally capture the output as a CompletedProcess object.
    """
    _log_run_cmd(cmd)
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


def worker_run(command, capture_output=True, print_output=True) -> Union[CompletedProcess, None]:
    return _shell(CMD.format(command), capture_output=capture_output, print_output=print_output)


def rsync(from_path, to_path=".") -> Union[CompletedProcess, None]:
    return _shell(RSYNC.format(from_path, to_path), capture_output=False)


def get_job_states(jobid: str) -> List[JobState]:
    # Returns a list of states, since jobid can be a jobarray id.
    # (JobArrays contain multiple jobs, and thus multiple states)
    result = worker_run(f"status {jobid}", print_output=False)
    job_states = [JobState.from_str(s) for s in result.stdout.split("\n")]
    return job_states


def generate_tess_job(jobname: str, test_mode=False):
    worker_run(f"generate {jobname} " + "--test" if test_mode else "")


def submit_tess_job(jobname) -> List[str]:
    result = worker_run(f"submit {jobname}", print_output=False)
    submitted_ids = result.stdout.split("\n")
    return submitted_ids


def __print_final_job_states(jobs: List[Job]):
    print("Final states:")
    fstring = "{: >20} {: >20}"
    print(fstring.format("Job ID", "State"))
    for job in jobs:
        for i, state in enumerate(job.states):
            print(fstring.format(f"{job.id}_{i}", str(state)))


def wait_for_jobs(jobs: List[Job], wait):
    """Waits for "jobs" ids to all return a finished state (for wait seconds)"""
    log("===> Waiting for jobs to finish")
    all_jobs_finished = False
    while not all_jobs_finished:
        log(f"--> Waiting {wait}s before querying job states...")
        time.sleep(wait)
        for job in jobs:
            if not job.is_finished:
                job.states = get_job_states(job.id)
                log("States:", job.unique_states)
        all_jobs_finished = all([job.is_finished for job in jobs])
    log("<=== All jobs finished")
    __print_final_job_states(jobs)
    return jobs


def rsync_tess_results(jobname, save_path):
    log("Getting results from:", jobname, "rsync-ing them to:", save_path)
    rsync(Path(jobname) / "toi*", save_path)


def wait_for_sacct(jobarray_ids: List[str], wait, max_retries=10):
    """Checks if the jobarray_ids are in sacct (ie. in registered by SLURM manager)"""
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
