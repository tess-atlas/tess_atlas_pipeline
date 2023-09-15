#!/bin/bash
set -eu

JC_DIR="$1"

jc_key="$USER-job-controller"
rsync_key="$USER-rsync"

ssh-keygen -t ed25519 -C "$jc_key" -f ~/.ssh/$jc_key -N ''
echo

ssh-keygen -t ed25519 -C "$rsync_key" -f ~/.ssh/$rsync_key -N ''
echo

echo "==> Finished generating keys. Add the following to your ~/.ssh/authorized_keys on the remote"
echo

JC_PUBKEY="$(cat ~/.ssh/$jc_key.pub)"
RSYNC_PUBKEY="$(cat ~/.ssh/$rsync_key.pub)"

cat << EOF
restrict,command="$JC_DIR/bin/job-controller" $JC_PUBKEY
restrict,command="$JC_DIR/bin/rrsync -ro $JC_DIR/jobs" $RSYNC_PUBKEY

EOF
