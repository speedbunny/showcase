from airflow import DAG
from airflow.models import Variable

# Operator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.latest_only_operator import LatestOnlyOperator

from datetime import datetime, timedelta

script_dir = Variable.get('scripts_dir')  
mail_to = ['firstname.lastname@domain']

default_args = {
    'depends_on_past': False,
    'start_date': datetime(2019, 1, 20, 00, 00),
    'email': mail_to,
    'email_on_success': True,
    'email_on_failure': True,
    'retries': 1,
    'retry_delay': timedelta(minutes=10),
    'catchup': False
}

# Instantiate a DAG my_dag that runs every day
# DAG objects contain tasks
# Time is in UTC
my_dag = DAG(dag_id='my_dag_id',
             default_args=default_args,
             schedule_interval='30 13 * * *', )  # 8:30AM EST

# Hack to stop backfilling upstream tasks
latest_only = LatestOnlyOperator(task_id='task_1', dag=my_dag_id)

# Instantiate tasks
task_1 = BashOperator(
    task_id='task_1_id',
    bash_command=f'python {script_dir}/my_script.py -Args ',
    dag=my_dag_id
)

task_2 = BashOperator(
    task_id='task_2_id',
    bash_command=f'python {script_dir}/my_script2.py -Args ',
    dag=my_dag_id
)

# set task relationship
latest_only >> task_1 >> task_2
