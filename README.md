# Job Controller Lite

First, copy the skeleton directory to where you want the job controller working directory to be, e.g.
```
scp -r remote-skel-dir <destination>:<jc-working-directory>
```

For security, we want to do everything via restricted ssh keys.

You'll need:

- Two new ssh keys. One as the main job controller key, and the other for rsync use
```
ssh-keygen -t ed25519 -C "$USER-job-controller" -f ~/.ssh/$USER-job-controller -N ''
ssh-keygen -t ed25519 -C "$USER-rsync" -f ~/.ssh/$USER-rsync -N ''
```

- On the remote (where jobs will run), add the public keys to your ~/.ssh/authorized_keys like so
```
restrict,command="<jc-working-directory>/bin/job-controller" <main-job-controller-publickey>
restrict,command="<jc-working-directory>/bin/rrsync -ro <jc-working-directory>/jobs" <rsync-publickey>
```
where `<jc-working-directory>` is the path you've chosen for your job controller to work in.

The `job-controller` should be a wrapper script that handles and sanitizes commands+arguments you wish to run on the remote.

`rrsync` you can get from the rsync github page. You should probably download the version that matches the rsync version on your remote machine. Check this by doing `rsync --version`.

If you have, for example, version `3.2.3`, then do
```
cd <jc-working-directory>/bin
wget https://raw.githubusercontent.com/WayneD/rsync/v3.2.3/support/rrsync
chmod +x rrsync
```

There's also a helper script in the skeleton dir that you can run.

Note, that depending on the version, the script may be a Perl or Python3 script. Check the shebang at the top of the file to make sure.
