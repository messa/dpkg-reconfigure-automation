# Automation of dpkg-reconfigure

A script you can use as `EDITOR` for `dpkg-reconfigure -f editor` to automate Debian configuration.

Example:

```shell
# Setup
curl -fLsS https://raw.githubusercontent.com/messa/dpkg-reconfigure-automation/refs/heads/main/... -o /usr/local/bin/...

# Usage
EDITOR=/usr/local/bin/... dpkg-reconfigure -f editor tzdata
EDITOR=/usr/local/bin/... dpkg-reconfigure -f editor locales
```

What does it do:

- For tzdata, it choses the UTC timezone
- For locales, it choses `en_US.UTF-8`
