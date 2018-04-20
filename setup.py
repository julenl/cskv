from setuptools import setup, find_packages

long_desc = 'CSKV is a python tool too edit INI or RAW config files '
long_desc += 'with a single call. It can be used as a command-line tool, '
long_desc += 'or it can be imported as a module in python 2.*. '
long_desc += 'It does what other similar tools also do, but it also handles '
long_desc += 'indentation, and automatic file-type recognition (INI or '
long_desc += 'different RAW types). If the documentation is not clear enough, '
long_desc += 'the source code is relatively short, so any issue can be '
long_desc += 'quickly traced.'


setup(
    name = 'cskv',
    version = '1.0.0.dev7',
    description = 'Config parser for INI and RAW formatted files',
    long_description = long_desc,
    license = 'GNU General Public License v2 (GPLv2)',
    author = 'Julen Larrucea',
    author_email = 'julen@larrucea.eu',
    url = 'https://github.com/julenl/cskv',
    download_url = 'https://github.com/julenl/cskv/archive/0.1.tar.gz',
    keywords = ['config', 'ini', 'raw', 'parser', 'non-interactive'],
    classifiers = [
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Topic :: System :: Systems Administration",
        ],
    packages = find_packages(),
    scripts = ['bin/cskv'],
)
