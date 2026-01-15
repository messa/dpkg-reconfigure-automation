# How it works

## dpkg-reconfigure and debconf

`dpkg-reconfigure` is a Debian tool that allows reconfiguring already installed packages. It uses the **debconf** system to manage package configuration through various frontends.

## Editor frontend

When you run `dpkg-reconfigure -f editor <package>`, it uses the "editor" frontend. This frontend:

1. Collects all configuration questions for the package
2. Writes them to a temporary file
3. Opens the file in `$EDITOR`
4. After the editor exits, reads the modified file and applies the new values

This allows automation by providing a custom script as `EDITOR` that modifies the file programmatically.

## File format

The temporary file contains configuration questions in this format:

```
Name: <package>/<question-name>
Template: <package>/<question-name>
Value: <current-value>
Owners: <package>

Name: <package>/<another-question>
...
```

## Example: tzdata

When running `dpkg-reconfigure -f editor tzdata`, the file looks like:

```
Name: tzdata/Areas
Template: tzdata/Areas
Value: Europe
Owners: tzdata

Name: tzdata/Zones/Europe
Template: tzdata/Zones/Europe
Value: Prague
Owners: tzdata
```

To set UTC timezone, you need to change:
- `tzdata/Areas` value to `Etc`
- `tzdata/Zones/Etc` value to `UTC`

## Example: locales

When running `dpkg-reconfigure -f editor locales`, the file looks like:

```
Name: locales/locales_to_be_generated
Template: locales/locales_to_be_generated
Value: cs_CZ.UTF-8 UTF-8
Owners: locales

Name: locales/default_environment_locale
Template: locales/default_environment_locale
Value: cs_CZ.UTF-8
Owners: locales
```

To set en_US.UTF-8, you need to change:
- `locales/locales_to_be_generated` value to `en_US.UTF-8 UTF-8`
- `locales/default_environment_locale` value to `en_US.UTF-8`

## How this script works

The `dpkg-reconfigure-automation-editor.py` script:

1. Receives the temporary file path as a command-line argument
2. Reads the file content
3. Detects the package type by looking for known question names
4. Modifies the values according to predefined rules
5. Writes the modified content back to the file
6. Exits, allowing dpkg-reconfigure to apply the changes
