#!/usr/bin/env python

import sys
from utils import wait_for_jobs, generate_tess_job, submit_script, get_results, get_job_ids

# Steps:
# 1) generate job dir + scripts
# 2) submit jobs
# 3) wait for jobs to finish
# 4) copy back job results if successful

jobname = "tess-test"

generate_tess_job(jobname)
submit_script(jobname)
jobids = get_job_ids(jobname)
states = wait_for_jobs(jobids)

print("Final states:")
fstring = "{: >10} {: >10}"
print(fstring.format("Job ID", "State"))
for jobid, state in zip(jobids, states):
    print(fstring.format(jobid, state))

if set(states) == set(["COMPLETE"]):
    get_results(jobname)
else:
    print("\nERROR: some jobs failed.")
    sys.exit(1)
