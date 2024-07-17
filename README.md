# TESS Atlas Catalog Pipeline
[![Coverage Status](https://coveralls.io/repos/github/tess-atlas/tess_atlas_pipeline/badge.svg?branch=main)](https://coveralls.io/github/tess-atlas/tess_atlas_pipeline?branch=main)


#### NOTE: this is not meant to be a library (just a convenient place to keep the pipeline code)


## Example Usage:

On Nectar
```
cd /mnt/storage/tess_atlas_pipeline/manager          
python pipeline.py tess_oct2_23 /mnt/storage/tess_atlas_webbuilder/source/objects/ --web-build-dir /mnt/storage/tess_atlas_webbuilder/ |& tee pipeline.log
```

This will (1) generate+submit slurm jobs on OzStar, (2) build the website once the slurm jobs are all completed. 



## Installation instructions

Clone this repo in the cloud-server where you want 'manage' the pipeline, and build the website. 



Then, "install" the worker by copying the `worker` skeleton directory to the remote cluster (like OzStar), e.g.
```
scp -r worker <destination>:<worker_install_path>
```

For security, we want to do everything via restricted ssh keys.

Go to `manager/ssh/` and run the `setup-ssh` script:
```
cd manager/ssh/
setup-ssh <username_on_remote> <worker_install_path>
```

This script will:
- Generate two new ssh keys. One as the main key for running commands on the remote, and the other for rsync use
- Print the lines you need to add to your `~/.ssh/authorized_keys` on the remote cluster
- Create an SSH configuration file to be used by the manager

## Restricted rsync
`rrsync` you can get from the rsync github page. You should probably download the version that matches the rsync version on your remote machine. Check this by doing `rsync --version`.

If you have, for example, version `3.2.3`, then do
```
cd <worker_install_path>/bin
wget https://raw.githubusercontent.com/WayneD/rsync/v3.2.3/support/rrsync

chmod +x rrsync
```

There's also a helper script in the skeleton dir that you can run.

Note, that depending on the version, the script may be a Perl or Python3 script. Check the shebang at the top of the file to make sure.


