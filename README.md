# TESS Atlas Catalogue Pipeline

First, "install" the worker by copying the `worker` skeleton directory to the remote cluster, e.g.
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


## NOTE: this is not meant to be a library (just a convenient place to keep the pipeline code)
