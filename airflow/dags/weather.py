import json
from datetime import datetime

from airflow import DAG
from airflow.models import Variable
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import HttpOperator
from airflow.providers.standard.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

CITIES = [
    {"id": "lviv",     "lat": 49.839683, "lon": 24.029717},
    {"id": "kyiv",     "lat": 50.450100, "lon": 30.523400},
    {"id": "kharkiv",  "lat": 49.993500, "lon": 36.230400},
    {"id": "odesa",    "lat": 46.482526, "lon": 30.723309},
    {"id": "zhmerynka","lat": 49.044040, "lon": 28.118620},
]

def _process_weather(ti):
    data = ti.xcom_pull(task_ids=f"{ti.task_id.rsplit('.',1)[0]}.extract_data")
    current = data.get("current", {})
    return (
        current.get("dt"),
        current.get("temp"),
        current.get("humidity"),
        current.get("clouds"),
        current.get("wind_speed"),
    )

with DAG(
    dag_id="weather_dag_test",
    schedule="@daily",
    start_date=datetime(2021, 6, 16),
    catchup=False,
) as dag:

    create_table = SQLExecuteQueryOperator(
        task_id="create_table_sqlite",
        conn_id="weather_conn2",
        sql="""
        CREATE TABLE IF NOT EXISTS measures_test2 (
            timestamp   TIMESTAMP,
            temp        FLOAT,
            humidity    FLOAT,
            cloudiness  FLOAT,
            wind_speed  FLOAT,
            city        TEXT
        );
        """,
    )

    city_groups = []
    for city in CITIES:
        with TaskGroup(group_id=city["id"], prefix_group_id=True, add_suffix_on_collision=False) as tg:
            check = HttpSensor(
                task_id="check_api",
                http_conn_id="weather_conn_http",
                endpoint="data/3.0/onecall",
                request_params={
                    "lat": city["lat"],
                    "lon": city["lon"],
                    "appid": Variable.get("WEATHER_API_KEY"),
                },
            )

            extract = HttpOperator(
                task_id="extract_data",
                http_conn_id="weather_conn_http",
                endpoint="data/3.0/onecall",
                method="GET",
                data={
                    "lat": city["lat"],
                    "lon": city["lon"],
                    "appid": Variable.get("WEATHER_API_KEY"),
                },
                response_filter=lambda r: json.loads(r.text),
                log_response=True,
            )

            process = PythonOperator(
                task_id="process_data",
                python_callable=_process_weather,
            )

            inject = SQLExecuteQueryOperator(
                task_id="inject_data",
                conn_id="weather_conn2",
                sql="""
                    INSERT INTO measures_test2
                      (timestamp, temp, humidity, cloudiness, wind_speed, city)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                parameters=[
                    "{{ ti.xcom_pull(task_ids='" + city["id"] + ".process_data')[0] }}",
                    "{{ ti.xcom_pull(task_ids='" + city["id"] + ".process_data')[1] }}",
                    "{{ ti.xcom_pull(task_ids='" + city["id"] + ".process_data')[2] }}",
                    "{{ ti.xcom_pull(task_ids='" + city["id"] + ".process_data')[3] }}",
                    "{{ ti.xcom_pull(task_ids='" + city["id"] + ".process_data')[4] }}",
                    city["id"],
                ],
            )

            check >> extract >> process >> inject

        city_groups.append(tg)

    create_table >> city_groups
