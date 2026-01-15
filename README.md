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
