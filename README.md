# CSKV

CSKV, named after **C**onfig-**S**ection-**K**ey-**V**alue, is a tool for
editing configuration files non interactively.

There are other good tools out there, like [shini](https://github.com/wallyhall/shini), [crudini](https://github.com/pixelb/crudini) for command line environment, or the [ConfigParser](https://docs.python.org/2/library/configparser.html) module for python, but CSKV has some interesting features:

* Handles both *INI* and *RAW* formats with the same tool
  (I call *RAW* a file containing just KEY = VALUE entries)

* It can be called from command line, or imported into python as a module

* It can handle indentation. In fact, the default is "autoindentation",
  which places the new entry with the most common indentation among the
  rest of the lines.

## Installation:

The easiest way to install `cskv` is with python pip. Just install it with:

```shell
    pip install cskv
   ```
   
   Alternatively, download the file with:
   
   ```shell
      wget -O /usr/local/bin/cskv https://raw.githubusercontent.com/julenl/cskv/master/cskv.py
   ```

## Usage (interactive/command line):
* Change value in INI file, add to section if it is not already present:
```shell
   cksv /etc/samba/smb.conf -s global -k "passdb backend" -v tdbsam
```

* Change value in a raw config file. It will detect automatically that the
  KEY/VALUE separator is a space (RAWS config type):
```shell
   cksv /etc/ssh/sshd_config -k PasswordAuthentication -v no
```

* Merge the content of some file into our config (-e/--extra):
```shell
   cskv /etc/samba/smb.conf -e extra_conf.ini
```

* Set values from pipeline (echo/cat):
```shell
  cat extra_conf.ini | cskv /etc/samba/smb.conf -e
```

## Usage (as module):
```python
from cskv import cskv
opts = {}
opts['config_file'] = 'some_path/some_file.ini'
opts['section'] = 'some_section'
opts['key'] = 'some_key'
opts['value'] = 'some_value'

cfile = cskv(**opts)
cfile.process()
```

## Runing the tests
```shell
cd tests
./tests.py
```

