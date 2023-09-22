#!/usr/bin/env python

import sys
import argparse
from manager import (
    wait_for_jobs,
    generate_tess_job,
    submit_tess_job,
    rsync_tess_results,
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Workflow to generate and run TESS analysis on OzSTAR, and copy back the results"
    )

    # Add command-line arguments for jobname and tess_catalgoue_path
    parser.add_argument("jobname", help="Name of the job")
    parser.add_argument(
        "tess_catalgoue_path", help="Path to where you want to rsync the TESS catalogue"
    )
    args = parser.parse_args()

    jobname = args.jobname
    tess_catalgoue_path = args.tess_catalgoue_path

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

    if set(states) == set(["COMPLETE"]):
        rsync_tess_results(jobname, tess_catalgoue_path)
    else:
        print("\nERROR: some jobs failed.")
        sys.exit(1)
