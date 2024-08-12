import pickle
import time
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from bq_utils import upload_files_to_bucket, create_table_from_bucket, delete_files_from_bucket
from workflows.crossref import CrossrefSnapshot
from scheduler import execute_slurm_file, get_job_status


dotenv_path = Path('~/.env')
load_dotenv(dotenv_path=dotenv_path)
ETL_URL = os.environ['ETL_URL']
LOG_URL = os.environ['LOG_URL']
MAIL_USER = os.environ['MAIL_USER']


logging.basicConfig(filename=f'{LOG_URL}/scheduler.log', encoding='utf-8', level=logging.DEBUG)


logging.info('Creating Snapshot object.')
crossref_snapshot = CrossrefSnapshot(snapshot_date=[2024, 7],
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
job_id = execute_slurm_file(job_name='crossref_snapshot',
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
                            slurm_job='python ../workflows/crossref.py')

logging.info(f'Slurm job id: {job_id}')

job_status = get_job_status(job_id)

while job_status in [None, 'PENDING', 'RUNNING']:
    time.sleep(60)
    job_status = get_job_status(job_id)

if job_status == 'COMPLETED':
    logging.info(f'Slurm job {job_id} ended.')
    logging.info(f'Slurm job status: {job_status}.')

    logging.info(f'Upload files to Google Bucket.')
    upload_files_to_bucket(bucket_name='bigschol',
                           file_path=f'{ETL_URL}/transform/*',
                           gcb_dir='crossref')

    logging.info(f'Creating Table in Google BigQuery.')
    create_table_from_bucket(uri='gs://bigschol/crossref/*',
                             table_id='cr_instant',
                             project_id='subugoe-collaborative',
                             dataset_id='resources',
                             schema_file_path='schemas/schema_crossref.json',
                             source_format='jsonl',
                             write_disposition='WRITE_EMPTY',
                             table_description='Crossref Snapshot',
                             ignore_unknown_values=True)

    logging.info(f'Table in Google BigQuery was created.')

    logging.info(f'Removing files in Google Bucket.')

    delete_files_from_bucket(bucket_name='bigschol',
                             gcb_dir='crossref')

    logging.info(f'Successfully removed files in Google Bucket.')

