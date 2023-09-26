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

bin_path = Path(__file__).parent.absolute()
worker_install_path = bin_path.parent
jobs_path = worker_install_path / "jobs"

# Define a regular expression pattern to validate the job ID (numeric characters)
job_id_pattern = re.compile(r"^\d+$")


# Function to validate the job ID
def is_valid_job_id(job_id):
    return bool(job_id_pattern.match(job_id))


# Define the command-line argument parser
parser = argparse.ArgumentParser(description="TESS Job Controller (slurm-side)")

# Define subparsers for each task
subparsers = parser.add_subparsers(dest="command", help="Available commands")

# Define a "status" subcommand
status_parser = subparsers.add_parser("status", help="Get the status of a Slurm job")
status_parser.add_argument("job_id", help="Slurm job ID to check status for")

# Define a "generate" subcommand
generate_parser = subparsers.add_parser("generate", help="Generate slurm catalogue job")
generate_parser.add_argument(
    "job_name", help="Name of the slurm catalogue job to generate"
)

# Define a "submit" subcommand
submit_parser = subparsers.add_parser("submit", help="Submit slurm catalogue job")
submit_parser.add_argument("job_name", help="Name of the slurm catalogue job to submit")


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
        print(f"Error: Unable to get status for job {args.job_id}:")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)


# Function to handle the "generate" command
def generate_command(args):
    from tess_atlas_slurm_utils.slurm_job_generator import parse_toi_numbers, setup_jobs

    sanitized_job_name = shlex.quote(args.job_name)
    outdir = jobs_path / sanitized_job_name

    os.makedirs(outdir, exist_ok=True)

    toi_numbers = parse_toi_numbers(None, None, outdir)
    modules = os.getenv("LOADEDMODULES", "").split(':')

    setup_jobs(
        toi_numbers=toi_numbers,
        outdir=outdir,
        module_loads=" ".join(modules),
        submit=False,
        clean=True,
        email="",
    )

    print(f"Job generated successfully: {sanitized_job_name}")


# Function to handle the "submit" command
def submit_command(args):
    sanitized_job_name = shlex.quote(args.job_name)
    submit_script_path = jobs_path / sanitized_job_name / "submit" / "submit.sh"
    result = subprocess.run(
        ["bash", str(submit_script_path)], capture_output=True, text=True
    )

    if result.returncode == 0:
        print(result.stdout)
    else:
        print(f"Error: Unable to submit job {args.job_name}:")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)


if __name__ == "__main__":
    args = parser.parse_args(os.getenv("SSH_ORIGINAL_COMMAND", "").split())

    # Call the corresponding function based on the selected command
    if args.command == "status":
        status_command(args)
    elif args.command == "generate":
        generate_command(args)
    elif args.command == "submit":
        submit_command(args)
    else:
        print("Invalid command. Use '--help' for usage information.")
        sys.exit(1)
