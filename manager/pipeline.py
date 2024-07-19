#!/usr/bin/env python

import sys
import subprocess
import argparse
from pathlib import Path
from manager import (
    wait_for_sacct,
    wait_for_jobs,
    generate_tess_job,
    submit_tess_job,
    rsync_tess_results,
    log,
)
from job import Job

WAIT_BETWEEN_CHECKS = 60  # s
WAIT_FOR_SACCT = 5  # s


def parse_args():
    parser = argparse.ArgumentParser(
        description="Workflow to generate and run TESS analysis on OzSTAR, and copy back the results"
    )

    # Add command-line arguments for jobname and tess_catalgoue_path
    parser.add_argument("jobname", help="Name of the job (this will also set the dir name for the runs)")
    parser.add_argument(
        "tess_catalog_path",
        help="Path to where you want to rsync the TESS catalogue",
        type=Path,
    )
    parser.add_argument(
        "--web-build-dir", help="Path to TESS Atlas web builder", type=Path
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Run in test mode (used for testing the pipeline)")
    parser.add_argument(
        "--just-webbuild", action="store_true",
        help="Only run the web-builder"
    )
    args = parser.parse_args()

    # validate args
    if args.web_build_dir and not args.web_build_dir.is_dir():
        raise FileNotFoundError(f"web_build_dir '{args.web_build_dir}' does not exists")
    if not args.tess_catalog_path.is_dir():
        raise FileNotFoundError(
            f"tess_catalog_path '{args.tess_catalog_path}' does not exists"
        )

    return args


def queue_and_run_jobs_on_runner(jobname: str, test_mode: bool) -> None:
    """
    1. Generate slurm+submit  
    2. Watch job progress
    """
    generate_tess_job(jobname, test_mode)
    jobarray_ids = submit_tess_job(jobname)

    if jobarray_ids == []:
        raise RuntimeError("ERROR: no jobs on runner!")
    log("Successfully submitted jobs:", jobarray_ids)

    # Wait for jobs to enter sacct
    wait_for_sacct(jobarray_ids, wait=WAIT_FOR_SACCT)

    # Construct a list of jobs
    _jobs = [Job(i) for i in jobarray_ids]

    # Wait for them to all to finish
    jobs = wait_for_jobs(_jobs, wait=WAIT_BETWEEN_CHECKS)
    # Quit if any jobs failed
    if not all([job.successful_completion for job in jobs]):
        raise RuntimeError("ERROR: some jobs failed.")


def local_post_processing(jobname: str, tess_catalog_path: Path, web_build_dir: Path) -> None:
    """
    Copy results from remote + build website
    """
    # Copy results if all were successful
    rsync_tess_results(jobname, tess_catalog_path)

    if web_build_dir:
        log(f"Building web site in {web_build_dir}")
        subprocess.run(["make"], cwd=web_build_dir, shell=True, text=True)
    else:
        print("Web build dir not provided. Skipping...")


def main():
    """
    Steps:
    1) generate job dir + scripts
    2) submit jobs
    3) wait for jobs to finish
    4) copy back job results if successful
    """
    args = parse_args()
    if not args.just_webbuild:
        queue_and_run_jobs_on_runner(args.jobname, args.test)
    local_post_processing(args.jobname, args.tess_catalog_path, args.web_build_dir)


if __name__ == "__main__":
    main()
