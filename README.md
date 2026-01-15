# Automation of dpkg-reconfigure

A script you can use as `EDITOR` for `dpkg-reconfigure -f editor` to automate Debian configuration.

Example:

```shell
# Setup
curl -fLsS https://raw.githubusercontent.com/messa/dpkg-reconfigure-automation/main/dpkg-reconfigure-automation-editor -o /usr/local/bin/dpkg-reconfigure-automation-editor
chmod +x /usr/local/bin/dpkg-reconfigure-automation-editor

# Usage
EDITOR=/usr/local/bin/dpkg-reconfigure-automation-editor dpkg-reconfigure -f editor tzdata
EDITOR=/usr/local/bin/dpkg-reconfigure-automation-editor dpkg-reconfigure -f editor locales
```

What does it do:

- For tzdata, it chooses the UTC timezone
- For locales, it chooses `en_US.UTF-8`
