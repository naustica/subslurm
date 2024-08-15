import pickle
import time
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from bq_utils import upload_files_to_bucket, create_table_from_bucket, delete_files_from_bucket
from workflows.document_types import DocumentTypeSnapshot
from scheduler import execute_slurm_file, get_job_status


dotenv_path = Path('~/.env')
load_dotenv(dotenv_path=dotenv_path)
ETL_URL = os.environ['ETL_URL']
LOG_URL = os.environ['LOG_URL']
MAIL_USER = os.environ['MAIL_USER']
MODEL_URL = os.environ['MODEL_URL']


logging.basicConfig(filename=f'{LOG_URL}/scheduler.log', encoding='utf-8', level=logging.DEBUG)


logging.info('Creating Snapshot object.')
document_type_snapshot = DocumentTypeSnapshot(model_path=f'{MODEL_URL}',
                                              download_path=f'{ETL_URL}/download_document_types',
                                              transform_path=f'{ETL_URL}/transform_document_types')

logging.info('Snapshot object created.')
logging.info('Saving Snapshot object.')

with open(f'{ETL_URL}/document_type_snapshot.pkl', 'wb') as out:
    pickle.dump(document_type_snapshot, out, pickle.HIGHEST_PROTOCOL)

logging.info('Snapshot object saved.')

logging.info('Running slurm job.')
job_id = execute_slurm_file(job_name='document_types_snapshot',
                            mail_type='ALL',
                            mail_user=f'{MAIL_USER}',
                            partition='medium',
                            constraint='scratch',
                            cpus_per_task=16,
                            ntasks=1,
                            nodes=1,
                            mem='100GB',
                            dependency=None,
                            time=[0, 9, 0, 0],
                            cmd='module load python',
                            slurm_job='python ../workflows/document_types.py')

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
                           file_path=f'{ETL_URL}/transform_document_types/*',
                           gcb_dir='transform_document_types')

    logging.info(f'Creating Table in Google BigQuery.')
    create_table_from_bucket(uri='gs://bigschol/transform_document_types/*',
                             table_id='document_types_snapshot',
                             project_id='subugoe-wag-closed',
                             dataset_id='oal_doctypes',
                             schema_file_path='../schemas/schema_document_types.json',
                             source_format='jsonl',
                             write_disposition='WRITE_EMPTY',
                             table_description='Document Type Classification',
                             ignore_unknown_values=True)

    logging.info(f'Table in Google BigQuery was created.')

    logging.info(f'Removing files in Google Bucket.')

    delete_files_from_bucket(bucket_name='bigschol',
                             gcb_dir='transform_document_types')

    logging.info(f'Successfully removed files in Google Bucket.')
