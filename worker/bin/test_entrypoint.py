import pytest

from entrypoint import main
import sys
import os
import shutil

JOB_DIR = os.path.join(os.path.dirname(__file__), '../jobs')


def test_entrypoint_generation(monkeypatch, tmpdir, capsys):
    job_name = 'test_job'
    monkeypatch.setenv('SSH_ORIGINAL_COMMAND', f'generate {job_name} --test')
    main()
    outdir = os.path.join(JOB_DIR, job_name)
    toi_csv = os.path.join(outdir, 'tois.csv')
    assert os.path.exists(toi_csv)
    # check if slurm_pe_0_job.sh file exists
    pe_sh = os.path.join(outdir, 'submit', 'slurm_pe_0_job.sh')
    assert os.path.exists(pe_sh)
    # check that only 2 jobs exist
    with open(pe_sh, 'r') as f:
        txt = f.read()
    assert '--array=0-1' in txt
    assert '--quickrun' in txt

    # nuke the job directory
    shutil.rmtree(outdir)
