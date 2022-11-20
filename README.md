<a name="readme-top"></a>
<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/github_username/repo_name">
    <img src="https://user-images.githubusercontent.com/103563736/202896555-7c74c5e9-2807-4e35-a64a-b018bbc2d497.png" alt="Logo">
  </a>

<h3 align="center">Weather Collector</h3>

  <p align="center">
    Python package for collecting wether measurements.
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
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



## Features
- Fetching list of world's largest cities from third-party API.
- Fetching weather for provided cities from third-party API and store data into database.
- Easy to configurate cities at `cities.json` file. Only name is required.
- Report last and average temperature for every cities.

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

## Getting Started

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
<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Usage

1. Run continuously collecting weather.
    ```sh
    $ python3 manage.py
    ```
    By default `collect` service with `--initial` flag is calling. So it equls to:
    ```sh
    $ python3 manage.py collect --initial
    ```

    After that collector looks for `cites.json` file where list of cites described.
    ```json
    [
        {"name": "Moscow"},
        {"name": "Istanbul"}
    ]
    ```

    If file does not exist, collector getting the most populated cities from GeoDB API.
    > WARNING! <br>
    > Wether Collector do not guarantee that recived cites is a *real* the most populated cites ont the Earth at current moment. It's better to manualy fill `cities.json` file.

    After that collector begin collecting weather from Open Weather API every hour and store all data into database.

2. Change tracked cities.
    Describe cities at `cites.json` file and call for `InitService`.
    ```sh
    $ python3 manage.py init_cites
    ```
    By defaul cites will be appended to already handled ones. If you want to override existing, use `--override` flag. It will delete all already existing records in city table before.
    ```sh
    $ python3 manage.py init_cites --override
    ```

3. Get report.
    ```sh
    $ python3 manage.py report
    $ python3 manage.py report --average
    $ python3 manage.py report --latest
    ```
<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Explanation

1. Table Structure.

    Open Weather API provides a lot of information about current city weather. Depending on location and current weather situation some fields could appear some other could not. For that situation we decided to store all root fields in separate tables.

    Why `main`? <br>
    The basic reason for collecting weather is understanding how to cool down company's servers. Therefore, we parsing and store `main` field that contains current temperature. All other data storing as json at `ExtraMeasurementDataModel` for any future purposes.

    We may describe other tables to store all the data in relational (SQL) way later, if we will need it.

2. Restrictions.

    For now all http requests runs synchronously. It takes a lot of time and hold processing execution. It's better to make them in async way to reach more speed.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contacts

Misha Vybornyy:

[![Gmail Badge](https://img.shields.io/badge/-misha.vybornyy@gmail.com-c14438?style=flat&logo=Gmail&logoColor=white&link=mailto:vbrn.mv@gmail.com)](mailto:vbrn.mv@gmail.com)
[![Telegram Badge](https://img.shields.io/badge/-mishaviborniy-blue?style=social&logo=telegram&link=https://t.me/mishaviborniy)](https://t.me/mishaviborniy) <p align='left'>