import pipeline
from pipeline import main
import pytest
import sys
import os
import subprocess
from subprocess import CompletedProcess as SSHRes


def test_pipeline_generation(monkeypatch, tmpdir, capsys):
    # setup mock dirs
    jobname = 'test_job'
    tess_data_dir = str(tmpdir / 'tess_data')
    webdir = str(tmpdir / 'webdir')
    os.makedirs(tess_data_dir, exist_ok=True)
    os.makedirs(webdir, exist_ok=True)
    monkeypatch.setattr('sys.argv', ['pipeline.py', jobname, tess_data_dir, '--web-build-dir', webdir, '--test'])

    # setup the mock return values from the subprocess calls
    n_jobs = 2
    job_ids = [i for i in range(n_jobs)]
    job_id_str = "\n".join([str(i) for i in job_ids])
    ssh_retuns = [
        SSHRes(args=["generation"], returncode=0, stdout='GENERATION SUCCESSFUL', stderr=''),  # from generate job
        SSHRes(args=["submit"], returncode=0, stdout=job_id_str, stderr=''),  # from submit job
        *[SSHRes(args=["status"], returncode=0, stdout='RUNNING', stderr='') for _ in range(n_jobs)],
        # from 1st sacct check
        *[SSHRes(args=["status"], returncode=0, stdout='COMPLETED', stderr='') for _ in range(n_jobs)],
        # from while loop
        SSHRes(args=["rsync"], returncode=0, stdout='', stderr=''),  # from rsync
        subprocess.CompletedProcess(args=["make"], returncode=0, stdout='', stderr=''),  # from make-website
    ]
    monkeypatch.setattr('subprocess.run', lambda *args, **kwargs: ssh_retuns.pop(0))
    monkeypatch.setattr(pipeline, 'WAIT_BETWEEN_CHECKS', 0.0001)
    monkeypatch.setattr(pipeline, 'WAIT_FOR_SACCT', 0.0001)
    main()

    # check that the logs are as we expect
    captured = capsys.readouterr()

    assert f"generate {jobname} --test " in captured.out
    assert f"submit {jobname}" in captured.out
    assert 'Waiting for jobs to finish' in captured.out
    assert f"status {job_ids[0]}" in captured.out
    assert f"status {job_ids[1]}" in captured.out
    assert "All jobs finished" in captured.out
    assert f"Getting results from: {jobname} rsync-ing them to: {tess_data_dir}" in captured.out
    assert f"Building web site in {webdir}" in captured.out
