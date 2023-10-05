#!/usr/bin/env python

"""
This script is the main entrypoint in to the worker.
It handles and sanitizes commands + arguments you wish to run on the remote.
It supports the following commands:
    status: gets the status/state of a SLURM job ID
    generate: generates a batch of TESS Atlas catalogue slurm jobs
    submit: submits a set of TESS Atlas catalogue slurm jobs
"""

import argparse
import subprocess
import re
import shlex
import sys
import os
from pathlib import Path

# Assumed directory structure
# {worker_install_path}/
#   ├── bin/
#   │   ├── entrypoint
#   │   ├── env.rc
#   │   ├── entrypoint.py (this script)
#   │   └── rrsync
#   └── jobs/
#       ├── jobname1/
#       │   └── submit/
#       │       ├── job.IDs
#       │       └── submit.sh
#       └── jobname2/
# etc...

BIN_PATH = Path(__file__).parent.absolute()
WORKER_INSTALL_PATH = BIN_PATH.parent
JOBS_PATH = WORKER_INSTALL_PATH / "jobs"

# Define a regular expression pattern to validate the job ID (numeric characters)
JOB_ID_PATTERN = re.compile(r"^\d+$")


# Function to validate the job ID
def is_valid_job_id(job_id):
    return bool(JOB_ID_PATTERN.match(job_id))


def make_parser():
    # Define the command-line argument parser + subparsers for each command
    parser = argparse.ArgumentParser(description="TESS Job Controller (slurm-side)")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Define a "status" subcommand
    status_parser = subparsers.add_parser("status", help="Get the status of a Slurm job")
    status_parser.add_argument("job_id", help="Slurm job ID to check status for")

    # Define a "generate" subcommand
    generate_parser = subparsers.add_parser("generate", help="Generate slurm catalog job")
    generate_parser.add_argument(
        "job_name", help="Name of the slurm catalog job to generate"
    )
    generate_parser.add_argument(
        "--test", action="store_true", help="Generate a 'test' job (used for testing the pipeline)"
    )

    # Define a "submit" subcommand
    submit_parser = subparsers.add_parser("submit", help="Submit slurm catalog job")
    submit_parser.add_argument("job_name", help="Name of the slurm catalogue job to submit")

    return parser


def parse_args_passed_via_ssh():
    ssh_args = os.getenv("SSH_ORIGINAL_COMMAND", "").split()
    parser = make_parser()
    args = parser.parse_args(args=ssh_args)
    # if args has and argumen 'job_name' check that it is a valid job name
    if hasattr(args, 'job_name'):
        args.job_name = shlex.quote(args.job_name)
    return args


# Function to handle the "status" command
def status_command(args):
    if not is_valid_job_id(args.job_id):
        print("Invalid job ID format. Job ID must be numeric.")
        sys.exit(1)

    result = subprocess.run(
        ["sacct", "--array", "--format=State", "--noheader", "-XP", "-j", args.job_id],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        job_state = result.stdout.strip()
        print(job_state)
    else:
        raise RuntimeError(
            f"Error: Unable to get status for job {args.job_id}:"
            f"{result.stdout}"
            f"{result.stderr}"
        )


# Function to handle the "generate" command
def generate_command(args):
    from tess_atlas_slurm_utils import parse_toi_numbers, setup_jobs

    outdir = JOBS_PATH / args.job_name

    os.makedirs(outdir, exist_ok=True)

    toi_numbers = parse_toi_numbers(outdir=outdir)
    toi_numbers = toi_numbers[:2] if args.test else toi_numbers
    modules = os.getenv("LOADEDMODULES", "").split(':')

    setup_jobs(
        toi_numbers=toi_numbers,
        outdir=outdir,
        module_loads=" ".join(modules),
        submit=False,
        clean=True,
        email="",
        quickrun=args.test,
    )

    print(f"Job generated successfully: {args.job_name}")


# Function to handle the "submit" command
def submit_command(args):
    submit_script_path = JOBS_PATH / args.job_name / "submit" / "submit.sh"
    result = subprocess.run(
        ["bash", str(submit_script_path)], capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Error: Unable to submit job {args.job_name}:"
            f"{result.stdout}"
            f"{result.stderr}"
        )
    print(result.stdout)


def main():
    # Parse the command-line arguments
    args = parse_args_passed_via_ssh()

    # Call the corresponding function based on the selected command
    if args.command == "status":
        status_command(args)
    elif args.command == "generate":
        generate_command(args)
    elif args.command == "submit":
        submit_command(args)
    else:
        raise ValueError(
            f"Invalid command: {args.command}\n"
            f"All args: {args}\n"
            f"env var SSH_ORIGINAL_COMMAND: {os.getenv('SSH_ORIGINAL_COMMAND', None)}\n"
            "-------------------\n"
            f"Valid usage: {make_parser().format_help()}"
        )


if __name__ == "__main__":
    main()
