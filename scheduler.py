import datetime
import subprocess
import json
from typing import Union
from simple_slurm import Slurm


def execute_slurm_file(job_name: str,
                       mail_type: str,
                       mail_user: str,
                       partition: str,
                       constraint: str,
                       cpus_per_task: int,
                       ntasks: int,
                       nodes: int,
                       dependency: Union[int, None],
                       time: list[int],
                       cmd: str,
                       slurm_job: str) -> int:

    days, hours, minutes, seconds = time

    slurm = Slurm(
        job_name=job_name,
        cpus_per_task=cpus_per_task,
        mail_type=mail_type,
        mail_user=mail_user,
        partition=partition,
        constraint=constraint,
        ntasks=ntasks,
        nodes=nodes,
        time=datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds),
    )

    if dependency:
        slurm.add_arguments(dependency=dict(afterok=dependency))

    slurm.add_cmd(cmd)
    job_id = slurm.sbatch(slurm_job)

    return job_id


def get_job_info(job_id: int) -> object:
    cmd = f'sacct -j {job_id} --json'
    p = subprocess.Popen(cmd,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         executable='/bin/bash')

    stdout, _ = p.communicate()

    stdout = stdout.decode('utf-8')

    job_info = json.loads(stdout)

    return job_info


def get_job_status(job_id: int) -> Union[str, None]:
    job_info = get_job_info(job_id)

    try:
        job_status = job_info['jobs'][0]['state']['current']
    except:
        job_status = None

    return job_status
