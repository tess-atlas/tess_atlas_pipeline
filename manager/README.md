# Manager (nectar)

This contains the collection of scripts/tools that the workflow manager needs. 
- ssh/setup-ssh: helps create the ssh-keys to access the worker and provide it _specific_ commands
- pipeline.py: the main workflow that can be run as a python script
- manager.py: utils for the workflow pipeline.py
- setup_gh_action_runner.sh: script to setup this machine as a github-runner for the tess-atlas projects



NOTE: To start the gh-runner as a service (in the background of the venv), run 
```
sudo ./svc.sh install
sudo ./svc.sh start
```

Then to check in on it/kill it:
```
sudo ./svc.sh status
sudo ./svc.sh stop
```
