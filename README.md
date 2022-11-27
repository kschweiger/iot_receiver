# IoT Data Receiver
[![CI](https://github.com/kschweiger/iot_receiver/actions/workflows/test.yml/badge.svg)](https://github.com/kschweiger/iot_receiver/actions/workflows/test.yml)

Lightweight REST service for accepting data from IoT devices and saving them to a database.

## Setup

The following steps outline how to setup the service. Additionally a Postgres instance
reachable from the running machine/container is required.

### Installation

The package relies on the [poetry](https://python-poetry.org) utility. Options to run it
are the installer on your system or using `pipx`. Ony poetry is installed you can install
the package with

```zsh
poetry install
```

for a production install or

```zsh
poetry install --with dev,test
```

for a development installation.

If you are using `pyenv`, you can set the poetry configuration option
`virtualenvs.prefer-active-python` to `true`. After that, poetry should use you venv set
with `pyenv`. The documentation can be found [here](https://python-poetry.org/docs/managing-environments#managing-environments).
If you installed poetry with the installer under MacOS, the config should should be
located at `~/Library/Preferences/pypoetry/config.toml`.

### Configuration

Configuration files are expected in the `config/` directory. This projects is based
around database interaction with the [data-organizer](https://github.com/kschweiger/data_organizer)
package. At least a `settings.toml` file and a `.secrets.toml` file is expected. The
former is committed to this repository with some default settings. The `.secrets` file
has to be created by the user and should look something like this

```toml
dynaconf_merge=true
[db]
  user=...
  password=...
  host=...
```

### Database setup

Before running the API endpoints you should also setup a schema and the required tables
on your postgres instance. See `scripts/database_init_commands.sql` for the necessary
commands.

### Security

For the interaction with the service, a APIKey verification is used. Use the `create_sender`
cli tool to generate keys and insert them in the database. At least one valid sender
should be added to the database before running the service.

## The API

For all endpoints it is necessary to first register the APIKey (also called Sender) for
a given endpoint using a **post request** to the `/register` endpoint. In addition the
APIKey in the header (as `access_token`) json data is expected:

```json
{
  "endpoint" : "ENDPOINT_NAME",
  "fields" : []
}
```

The `"endpoint"` has to be a valid endpoint of the service. The `"fields"` can be used to
define a subset of valid endpoint input model fields the sender will send to service.
This mainly effects which columns will be created in the table for the Sender/Endpoint.

### Environment endpoint

Input model:

```json
{
  "timestamp" : ["2022-01-01T00:00:00+00:00", ...],
  "temperatur" : [25,0 , ...],
  "pressure" : [1000.0, ...],
  "humidity" : [50.0, ...],
  "light" : [100,0, ...],
  "noise" : [1.0, ...],
  "gas_co" : [1.0, ...],
  "gas_no2" : [1.0, ...],
  "gas_nh3" : [1.0, ...],
}
```


## Docker

## Building the container

```zsh
docker build -t iot_receiver:$(poetry version -s) .
```

## Running the container

```zsh
docker run --add-host=host.docker.internal:host-gateway \
           --env IOTRECEIVER_db__host=host.docker.internal \
           -dp 7770:7770 iot_receiver:$(poetry version -s)
```

You can also overwrite other parameters for the database connection using the
`IOTRECEIVER_db__XXXX` environment variables.
