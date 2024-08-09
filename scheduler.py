import datetime
import subprocess
import json
import time
import pickle
import logging
import os
from dotenv import load_dotenv
from typing import Union
from simple_slurm import Slurm
from bq_utils import upload_files_to_bucket, create_table_from_bucket
from workflows.crossref import CrossrefSnapshot


load_dotenv()
ETL_URL = os.environ['ETL_URL']
LOG_URL = os.environ['LOG_URL']
MAIL_USER = os.environ['MAIL_USER']


logging.basicConfig(filename=f'{LOG_URL}/scheduler.log', encoding='utf-8', level=logging.DEBUG)


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
    logging.info('Creating Snapshot object.')
    crossref_snapshot = CrossrefSnapshot(snapshot_date=[2024, 2],
                                         filename='all.json',
                                         download_path=f'{ETL_URL}/download',
                                         transform_path=f'{ETL_URL}/transform')

    logging.info('Snapshot object created.')
    logging.info('Saving Snapshot object.')

    with open(f'{ETL_URL}/crossref_snapshot.pkl', 'wb') as out:
        pickle.dump(crossref_snapshot, out, pickle.HIGHEST_PROTOCOL)

    logging.info('Snapshot object saved.')

    logging.info('Downloading snapshot.')
    crossref_snapshot.download()
    logging.info('Snapshot downloaded.')

    logging.info('Running slurm job.')
    job_id = execute_slurm_file(job_name='crossref_test',
                                mail_type='ALL',
                                mail_user=f'{MAIL_USER}',
                                partition='medium',
                                constraint='scratch',
                                cpus_per_task=16,
                                ntasks=1,
                                nodes=1,
                                dependency=None,
                                time=[0, 9, 0, 0],
                                cmd='module load python',
                                slurm_job='python crossref.py')

    logging.info(f'Slurm job id: {job_id}')

    job_status = get_job_status(job_id)

    while job_status in [None, 'PENDING', 'RUNNING']:
        time.sleep(60)
        job_status = get_job_status(job_id)

    if job_status == 'COMPLETED':
        logging.info(f'Slurm job {job_id} ended.')
        print(job_status)
        """
        upload_files_to_bucket(bucket_name='bigschol',
                               file_path='/scratch/users/haupka/transform/*',
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
        """


if __name__ == '__main__':
    test_case()
