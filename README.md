<a name="readme-top"></a>
<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/MishaVyb/weather-collector">
    <img src="https://user-images.githubusercontent.com/103563736/202907625-a4942bed-c096-40eb-9550-b6542878af74.png" alt="Logo">
  </a>

<h3 align="center">Weather Collector</h3>

  <p align="center">
    Python package for collecting weather measurements.
    <br />
    <a href="#usage"><strong>Explore Usage topic »</strong></a>
    <br />
  </p>
</div>


<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#features">Features</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#explanations">Explanations</a></li>
    <li><a href="#restrictions">Restrictions</a></li>
    <li><a href="#appreciations">Appreciations</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



## Features
- Fetching world's largest cities from third-party API.
- Fetching weather for provided cities from third-party API and store data into database.
- Easy to configurate cities at `cities.json` file. Only name is required.
- Making report for last and average temperature for every city.

## Built With
![](https://img.shields.io/badge/python-3.10.4-blue)
![](https://img.shields.io/badge/SQL_Alchemy-1.4-blue)
![](https://img.shields.io/badge/alembic-1.8-blue)
![](https://img.shields.io/badge/pydantic-1.10-blue)
![](https://img.shields.io/badge/pytest-7.2-blue)
<br>

![](https://img.shields.io/badge/mypy-0.97-blue)
![](https://img.shields.io/badge/black-22.6-blue)
![](https://img.shields.io/badge/flake8-5.0-blue)



# Getting Started

## Run docker compose.
### Prerequisites
* Docker **20.10.21**

1. Clone the repo.
   ```sh
   $ git clone git@github.com:MishaVyb/weather-collector.git
   ```
2. Define environment variables
    ```sh
      $ cd weather-collector
      $ nano prod.env
    ```
    ```env
    debug = false
    open_weather_key = ...
    POSTGRES_USER = vybornyy
    POSTGRES_PASSWORD = vybornyy
    POSTGRES_DB = default
    ```

3. Build and run docker compose by predefined `make` command.
    ```sh
    $ make app
    ```
    > WARNING! <br>
    > If database connection fails, try again in a few seconds. It could be because postress server is not running yet.


## Run as python script.
### Prerequisites

* python **3.10.4**
* pip


### Installation

1. Clone the repo.
   ```sh
   $ git clone git@github.com:MishaVyb/weather-collector.git
   ```
2. Activate virtual environment.
   ```sh
   $ cd weather-collector
   $ python3.10 -m venv venv
   $ source venv/bin/activate

3. Install requirements.
    ```sh
   (venv) $ pip install -r requirements.txt
   ```

4. Migrate database.
    ```sh
   (venv) $ alembic upgrade head
   ```
5. Define environment variables
    ```sh
      $ nano debug.env
    ```
    ```env
    debug = true
    open_weather_key = ...
    ```
<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Usage

1. Init cities and run continuously collecting weather.
    ```sh
    $ python3 manage.py collect --initial
    ```

    For the beginning, collector looks for `cites.json` file where list of cities described.
    ```json
    [
        {"name": "Moscow"},
        {"name": "Istanbul"}
    ]
    ```

    If that file does not exist, collector getting the most populated cities from GeoDB API.
    > WARNING! <br>
    > Weather Collector do **not** guarantee that received cites is a *real* the most populated cities on the Earth at current moment. It's better to manually fill `cities.json` file.

    After that collector begin collecting weather every hour and store all data into database.

2. Change tracked cities.

    Describe cities at `cites.json` file and call for `InitCities` service.
    ```sh
    $ python3 manage.py init_cites
    ```
    By default cites will be appended to already handled ones. If you want to track only that new list of cities, use `--override` flag. It seting all existing cities at database not to be tracking for weather collecting anymore.
    ```sh
    $ python3 manage.py init_cites --override
    ```
    Or re-fetch cities. This line invokes `InitCities` with `--override` flag after fetching.
    ```sh
    $ python3 manage.py fetch_cites --override
    ```
    Or re-init and run collecting in one line.
    ```sh
    $ python3 manage.py collect --initial --override
    ```

3. Get weather report.
    ```sh
    $ python3 manage.py report
    $ python3 manage.py report --average
    $ python3 manage.py report --latest
    ```

4. More options.
    ```sh
    $ python3 manage.py --help
    ```


<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Explanation

1. Database Structure.
    ![Untitled (3)](https://user-images.githubusercontent.com/103563736/202989181-cb714940-7df3-4a67-880c-048acd2bf571.jpg)

    `CityModel` <br>
    Contains cities which weather collecting for.

    `MeasurementModel`<br>
    For every weather measurement (API request) associated with the city.

    Open Weather API provides a lot of information about current city weather. Depending on location and current weather situation, some fields could appear some other could not. For that situation we decided to store all response root fields in separate tables.

    Why `MainWeatherDataModel` table? <br>
    The basic reason for collecting weather is understanding how to cool down company's servers. Therefore, we parsing and store `main` field that contains current temperature. All other data storing as json at `ExtraMeasurementDataModel` for any future purposes.

    We may describe other tables to store all the data in relational (SQL) way later, if we will need it.

2. Services Structure.
    ![Untitled (2)](https://user-images.githubusercontent.com/103563736/202989192-42b7c2cc-f939-46fc-8630-06cb9e6fee1a.jpg)

    `BaseService` presents basic definition for all other services.<br>
    `DBSessionMixin` for making operations with databse.<br>
    `FetchServiceMixin` for handling http requests.<br>


## Restrictions
1. Not async. <br>
    When executing services, all http requests runs synchronously. It takes a lot of time and hold processing execution. It's better to make them in async way to reach more speed.

2. Cities names unique constraint <br>
    When calling for `InitCites` service, all cities descibed at `cities.json` appending to database and there are now checking for repetitions. So database may contains several cities with the same name and location.

    To specify city explicitly, provide location coordinates or country code.
      ```json
    [
        {"name": "..", "latitude": 31.1, "longitude": 121.4},
        {"name": "..", "countryCode": "BR"}
    ]

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Appreciations

Great thanks for third-party API services used to handle this package.
- [GeoDB](http://geodb-cities-api.wirefreethought.com/) - for presenting list of the most populated cities.
- [Open Weather](https://openweathermap.org/) - for presenting cities location and their weather.

## Contacts

Misha Vybornyy

[![Telegram Badge](https://img.shields.io/badge/-mishaviborniy-blue?style=social&logo=telegram&link=https://t.me/mishaviborniy)](https://t.me/mishaviborniy)<br>
[![Gmail Badge](https://img.shields.io/badge/-misha.vybornyy@gmail.com-c14438?style=flat&logo=Gmail&logoColor=white&link=mailto:vbrn.mv@gmail.com)](mailto:vbrn.mv@gmail.com)
<p align='left'>

<p align="right">(<a href="#readme-top">back to top</a>)</p>