# How it works

## dpkg-reconfigure and debconf

`dpkg-reconfigure` is a Debian tool that allows reconfiguring already installed packages. It uses the **debconf** system to manage package configuration through various frontends.

## Editor frontend

When you run `DEBIAN_FRONTEND=editor dpkg-reconfigure <package>` (or use `-f editor`), it uses the "editor" frontend. This frontend:

1. Collects all configuration questions for the package
2. Writes them to a temporary file in a shell-like format
3. Opens the file in `$EDITOR`
4. After the editor exits, reads the modified file and applies the new values

This allows automation by providing a custom script as `EDITOR` that modifies the file programmatically.

## File format

The temporary file contains configuration questions in this format:

```
# You are using the editor-based debconf frontend to configure your system. See
# the end of this document for detailed instructions.
###############################################################################

# Description of the option and available choices...
#
# (Choices: Option1, Option2, Option3)
# Question label:
package/question_name="current_value"


###############################################################################
# The editor-based debconf frontend presents you with one or more text files to
# edit. This is one such text file...
```

The key format is: `package/question_name="value"`

## Example: tzdata

When running `DEBIAN_FRONTEND=editor dpkg-reconfigure tzdata`, the file looks like:

```
# Please select the geographic area in which you live.
#
# (Choices: Africa, America, Antarctica, Arctic, Asia, Atlantic, Australia,
# Europe, Indian, Pacific, Etc, Legacy)
# Geographic area:
tzdata/Areas="Europe"
```

And for the timezone selection:

```
# Please select your time zone.
#
# (Choices: Amsterdam, Berlin, Prague, ...)
# Time zone:
tzdata/Zones/Europe="Prague"
```

To set UTC timezone, you need to change:
- `tzdata/Areas="Etc"`
- `tzdata/Zones/Etc="UTC"`

## Example: locales

When running `DEBIAN_FRONTEND=editor dpkg-reconfigure locales`, the file looks like:

```
# Please choose which locales to generate.
#
# (Choices: All locales, aa_DJ.UTF-8 UTF-8, ..., en_US.UTF-8 UTF-8, ...)
# (Enter zero or more items separated by a comma followed by a space (', ').)
# Locales to be generated:
locales/locales_to_be_generated=""
```

To set en_US.UTF-8, you need to change:
- `locales/locales_to_be_generated="en_US.UTF-8 UTF-8"`
- `locales/default_environment_locale="en_US.UTF-8"` (if this question appears)

## How this script works

The `dpkg-reconfigure-automation-editor.py` script:

1. Receives the temporary file path as a command-line argument
2. Reads the file content
3. Detects the package type by looking for known question patterns
4. Uses regex substitution to modify the values
5. Writes the modified content back to the file
6. Exits, allowing dpkg-reconfigure to apply the changes
