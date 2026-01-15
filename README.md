# Automation of dpkg-reconfigure

A script you can use as `EDITOR` for `dpkg-reconfigure -f editor` to automate Debian configuration.

## Installation

Install directly from GitHub:

```shell
pip install git+https://github.com/messa/dpkg-reconfigure-automation.git
```

Or using uv:

```shell
uv pip install git+https://github.com/messa/dpkg-reconfigure-automation.git
```

### Alternative: manual installation

```shell
curl -fLsS https://raw.githubusercontent.com/messa/dpkg-reconfigure-automation/main/dpkg_reconfigure_automation_editor.py -o /usr/local/bin/dpkg-reconfigure-automation-editor
chmod +x /usr/local/bin/dpkg-reconfigure-automation-editor
```

## Usage

After pip installation:

```shell
EDITOR=dpkg-reconfigure-automation-editor dpkg-reconfigure -f editor tzdata
EDITOR=dpkg-reconfigure-automation-editor dpkg-reconfigure -f editor locales
```

### Custom values

You can specify custom values as `key=value` arguments:

```shell
EDITOR="dpkg-reconfigure-automation-editor tzdata/Areas=Asia tzdata/Zones/Asia=Shanghai" dpkg-reconfigure -f editor tzdata
```

Values with spaces need to be quoted:

```shell
EDITOR="dpkg-reconfigure-automation-editor 'tzdata/Areas=None of the above' tzdata/Zones/Etc=UTC" dpkg-reconfigure -f editor tzdata
```

## This looks silly

Yes it does :)

There should be an easier solution. But it isn't.

There is a **debconf** system that you can use to configure default values (via `debconf-set-selections`) that will be used when installing new packages.
But once a package is installed, actual configuration files or system state are preferred and the debconf selections are ignored.

```shell
# THIS DOES NOT WORK
echo 'locales locales/default_environment_locale select en_US.UTF-8' | debconf-set-selections
echo 'locales locales/locales_to_be_generated multiselect cs_CZ.UTF-8 UTF-8, en_US.UTF-8 UTF-8' | debconf-set-selections
dpkg-reconfigure -f noninteractive locales
```


## What does it do

- For tzdata, it chooses the UTC timezone (by default)
- For locales, it chooses `en_US.UTF-8` (by default)

## Running tests

```shell
uv sync
uv run pytest
```

Or with pip:

```shell
pip install pytest
pytest
```
