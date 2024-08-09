import pickle
import time
import os
import logging
from dotenv import load_dotenv
from workflows.document_types import DocumentTypeSnapshot
from scheduler import execute_slurm_file, get_job_status


load_dotenv()
ETL_URL = os.environ['ETL_URL']
LOG_URL = os.environ['LOG_URL']
MAIL_USER = os.environ['MAIL_USER']
MODEL_URL = os.environ['MODEL_URL']


logging.basicConfig(filename=f'{LOG_URL}/scheduler.log', encoding='utf-8', level=logging.DEBUG)


logging.info('Creating Snapshot object.')
document_type_snapshot = DocumentTypeSnapshot(model_path=f'{MODEL_URL}',
                                              download_path=f'{ETL_URL}/download',
                                              transform_path=f'{ETL_URL}/transform_document_types')

logging.info('Snapshot object created.')
logging.info('Saving Snapshot object.')

with open(f'{ETL_URL}/document_type_snapshot.pkl', 'wb') as out:
    pickle.dump(document_type_snapshot, out, pickle.HIGHEST_PROTOCOL)

logging.info('Snapshot object saved.')

logging.info('Running slurm job.')
job_id = execute_slurm_file(job_name='document_types_test',
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
                            slurm_job='python ../workflows/document_types.py')

logging.info(f'Slurm job id: {job_id}')

job_status = get_job_status(job_id)

while job_status in [None, 'PENDING', 'RUNNING']:
    time.sleep(60)
    job_status = get_job_status(job_id)

if job_status == 'COMPLETED':
    logging.info(f'Slurm job {job_id} ended.')
    print(job_status)
