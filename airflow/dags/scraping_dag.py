from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    'owner': 'IgorMichels',
    'start_date': datetime(2023, 8, 15),
    'retries': 0,
}

dag = DAG(
    'GitHub_scraping_pipeline',
    default_args=default_args,
    schedule_interval='30 12 1 4-12 2,5',
    catchup=False,
)

update_repository_task = BashOperator(
    task_id='update_repository',
    bash_command="cd ../../../../../../../Users/igor.michels/Documents/BrazilianSoccerData/ && git pull",
    dag=dag,
)

execute_scrape_task = BashOperator(
    task_id='execute_scrape',
    bash_command='cd ../../../../../../../Users/igor.michels/Documents/BrazilianSoccerData/scripts && python main.py --s',
    dag=dag,
)

commit_results_task = BashOperator(
    task_id='commit_results',
    bash_command="cd ../../../../../../../Users/igor.michels/Documents/BrazilianSoccerData/ && git status && git add auxiliary/ results/ README.md && git commit -m 'Automated update' && git push",
    dag=dag,
)

update_repository_task >> execute_scrape_task >> commit_results_task
