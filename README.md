# AutomatedDataPipelines

# Weather DAG for Multi-City Historical Weather Data

This repository contains an Apache Airflow DAG (`weather_dag`) that:

* **Creates** a SQLite table to store weather metrics.
* **Fetches** current and historical weather data via OpenWeather One Call API (v3.0).
* **Processes** multiple metrics: temperature, humidity, cloudiness, and wind speed.
* **Stores** results per city in the SQLite database.
* **Organizes** tasks using Airflow TaskGroups for clarity.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)

   * [Airflow Connections](#airflow-connections)
   * [Airflow Variables](#airflow-variables)
4. [DAG Structure](#dag-structure)
5. [TaskGroups](#taskgroups)
6. [Running the DAG](#running-the-dag)
7. [Extending to More Cities](#extending-to-more-cities)

---

## Prerequisites

* Python 3.11+
* Apache Airflow 3.0+
* `apache-airflow-providers-http`
* `apache-airflow-providers-common-sql`
* SQLite (default)

---

## Installation

1. Clone this repository:

   ```bash
   git clone <repo_url>
   cd <repo_folder>
   ```
2. Create and activate a virtual environment:

   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   ```
3. Install Airflow and providers:

   ```bash
   pip install apache-airflow apache-airflow-providers-http apache-airflow-providers-common-sql
   ```
4. Initialize Airflow:

   ```bash
   export AIRFLOW_HOME=~/airflow
   airflow db init
   airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com --password admin
   ```
5. Copy this DAG file into your Airflow `dags/` folder.

---

## Configuration

### Airflow Connections

1. **SQLite connection** (`weather_conn2`):

   * **Conn Id:** `weather_conn2`
   * **Conn Type:** `sqlite`
   * **Schema:** `/Users/you/airflow/weather.db` (absolute path)

2. **HTTP connection** (`weather_conn_http`):

   * **Conn Id:** `weather_conn_http`
   * **Conn Type:** `http`
   * **Host:** `api.openweathermap.org`
   * **Schema:** leave blank

### Airflow Variables

* `WEATHER_API_KEY`: Your OpenWeather API key with One Call 3.0 subscription.

  ```bash
  airflow variables set WEATHER_API_KEY <your_api_key>
  ```

---

## DAG Structure

```text
weather_dag
├── setup (TaskGroup)
│   └── create_table_sqlite
└── <city> (TaskGroup) for each city in [lviv, kyiv, kharkiv, odesa, zhmerynka]
    ├── check_api
    ├── extract_data
    ├── process_data
    └── inject_data
```

* **DAG id:** `weather_dag`
* **Schedule:** `@daily`
* **Start Date:** `2021-06-16`
* **Catchup:** Disabled (use `catchup=False`).

---

## TaskGroups

Each TaskGroup contains the following tasks:

1. **check\_api** (`HttpSensor`)

   * Ensures the One Call endpoint is reachable for the given latitude/longitude.
2. **extract\_data** (`HttpOperator`)

   * Fetches weather JSON and pushes to XCom.
3. **process\_data** (`PythonOperator`)

   * Extracts `dt`, `temp`, `humidity`, `clouds`, and `wind_speed` from the JSON.
4. **inject\_data** (`SQLExecuteQueryOperator`)

   * Inserts the processed metrics plus `city` name into the SQLite table.

---

## Running the DAG

1. Start the scheduler and webserver:

   ```bash
   airflow scheduler
   airflow webserver
   ```
2. Open the Airflow UI at `http://localhost:8080`, login as `admin` / `admin`.
3. Trigger the `weather_dag` manually or wait for its daily schedule.
4. Inspect TaskGroups and ensure all tasks succeed.
5. Query the SQLite table:

   ```bash
   sqlite3 /Users/you/airflow/weather.db
   sqlite> SELECT * FROM measures_test;
   ```

---

## Extending to More Cities

To add another city:

1. Edit the `CITIES` list at the top of the DAG.
2. Provide its `id`, `lat`, and `lon`.
3. Airflow will automatically create a new TaskGroup for it.



<img width="515" alt="image" src="https://github.com/user-attachments/assets/e3ee504d-2d98-45be-81e1-485440a4451c" />
