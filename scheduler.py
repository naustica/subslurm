import datetime
import subprocess
import json
import time
from typing import Union
from simple_slurm import Slurm
from bq_utils import upload_files_to_bucket, create_table_from_bucket
from workflows.crossref import CrossrefSnapshot


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


def test_case():

    crossref_snapshot = CrossrefSnapshot(snapshot_date=[2023, 11],
                                         filename='all.json',
                                         download_path='/scratch/users/haupka/download',
                                         transform_path='/scratch/users/haupka/transform')

    crossref_snapshot.download()

    job_id = execute_slurm_file(job_name='crossref_test',
                                mail_type='ALL',
                                mail_user='nick.haupka@sub.uni-goettingen.de',
                                partition='medium',
                                constraint='scratch',
                                cpus_per_task=16,
                                ntasks=1,
                                nodes=1,
                                dependency=None,
                                time=[0, 9, 0, 0],
                                cmd='module load python',
                                slurm_job='python crossref.py')

    job_status = get_job_status(job_id)

    while job_status in [None, 'PENDING', 'RUNNING']:
        time.sleep(60)
        job_status = get_job_status(job_id)

    if job_status == 'COMPLETED':
        upload_files_to_bucket(bucket_name='bigschol',
                               file_path='/scratch/haupka/transform/*',
                               gcb_dir='tests')

        create_table_from_bucket(uri='gs://bigschol/tests/*',
                                 table_id='crossref_test',
                                 project_id='subugoe-collaborative',
                                 dataset_id='resources',
                                 schema_file_path='schemas/schema_crossref.json',
                                 source_format='jsonl',
                                 write_disposition='WRITE_EMPTY',
                                 table_description='Test Table',
                                 ignore_unknown_values=True)


if __name__ == '__main__':
    test_case()
