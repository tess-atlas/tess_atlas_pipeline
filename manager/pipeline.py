#!/usr/bin/env python

import sys
import subprocess
import argparse
from pathlib import Path
from manager import (
    wait_for_jobs,
    generate_tess_job,
    submit_tess_job,
    rsync_tess_results,
    log,
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Workflow to generate and run TESS analysis on OzSTAR, and copy back the results"
    )

    # Add command-line arguments for jobname and tess_catalgoue_path
    parser.add_argument("jobname", help="Name of the job")
    parser.add_argument(
        "tess_catalgoue_path", help="Path to where you want to rsync the TESS catalogue", type=Path
    )
    parser.add_argument(
        "--web-build-dir", help="Path to TESS Atlas web builder", type=Path
    )
    args = parser.parse_args()

    jobname = args.jobname
    tess_catalgoue_path = args.tess_catalgoue_path
    web_build_dir = args.web_build_dir
    if web_build_dir and not web_build_dir.is_dir():
        raise FileNotFoundError(f"web_build_dir '{web_build_dir}' does not exists")
    if not tess_catalgoue_path.is_dir():
        raise FileNotFoundError(f"tess_catalgoue_path '{tess_catalgoue_path}' does not exists")

    # Steps:
    # 1) generate job dir + scripts
    # 2) submit jobs
    # 3) wait for jobs to finish
    # 4) copy back job results if successful

    generate_tess_job(jobname)
    jobids = submit_tess_job(jobname)
    states = wait_for_jobs(jobids)

    print("Final states:")
    fstring = "{: >10} {: >10}"
    print(fstring.format("Job ID", "State"))
    for jobid, state in zip(jobids, states):
        print(fstring.format(jobid, state))

    if set(states) == set(["COMPLETED"]):
        rsync_tess_results(jobname, tess_catalgoue_path)
    else:
        log("ERROR: some jobs failed.", level='ERROR')
        sys.exit(1)

    if web_build_dir:
        log(f"Building web site in {web_build_dir}")
        subprocess.run(['make'], cwd=web_build_dir, shell=True, text=True)
    else:
        print("Web build dir not provided. Skipping...")
