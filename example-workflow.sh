#!/bin/bash
set -eu

# Inputs with defaults:

JC_USER=${JC_USER:-$USER}
JC_HOSTNAME=${JC_HOSTNAME:-nt.swin.edu.au}
JC_KEY=${JC_KEY:-"~/.ssh/${JC_USER}-job-controller"}
RSYNC_KEY=${RSYNC_KEY:-"~/.ssh/${JC_USER}-rsync"}
SLEEP=${SLEEP:-5}   # It's probably best not to ping sacct too often...

#----------------------------------------

DESTINATION="${JC_USER}@$JC_HOSTNAME"
REMOTE="ssh -i $JC_KEY $DESTINATION"

echo "==> Submitting job..."
JOB_ID=$($REMOTE submit test-job slurm.q)
echo "[$(date)] Job $JOB_ID submitted successfully"

# Wait 5 seconds before first ping (sometimes job ID isn't in sacct yet)
sleep 5

while true; do
  JOB_STATUS=$($REMOTE status "$JOB_ID")
  echo "[$(date)] Job status: $JOB_STATUS"
  case "$JOB_STATUS" in
    PENDING|RUNNING|REQUEUED|RESIZING|SUSPENDED) sleep "$SLEEP" ;;
    *) break ;;
  esac
done

if [ "$JOB_STATUS" == "COMPLETED" ]; then
  echo "It's done!"
else
  echo "Oh no. Job failed :("
  exit 1
fi

# Copy things back, if completed
echo "==> Copying job output"
rsync -e "ssh -i $RSYNC_KEY" -avzP "${DESTINATION}:jobs/test-job/output" .
