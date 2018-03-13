# CSKV

CSKV, named after **C**onfig-**S**section-**K**ey-**V**alue, is a tool for
editing configuration files non interactively.

There are other good tools out there, like [shini](https://github.com/wallyhall/shini), [crudini](https://github.com/pixelb/crudini) for command line environment, or the [ConfigParser](https://docs.python.org/2/library/configparser.html) module for python, but CSKV has some interesting features:

* Handles both *INI* and *RAW* formats with the same tool
  (I call *RAW* a file containing just KEY = VALUE entries)

* It can be called from command line, or imported into python as a module

* It can handle indentation. In fact, the default is "autoindentation",
  which places the new entry with the most common indentation among the
  rest of the lines.

## Usage:
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
