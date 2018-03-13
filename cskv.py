#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018, Julen Larrucea <julen@larrucea.eu>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GPLv2, the GNU General Public License version 2, as
# published by the Free Software Foundation. http://gnu.org/licenses/gpl.html


# CSKV (Config Section Key Value) is a non interactive configuration editor.
# It can parse files with INI format, as well as raw lines with key-value.
# It works by treating INI or raw files the same way. In case of INI files,
# it finds out the "slice" of file corresponding to the section, and further
# it just parses key-values the same way it would in a normal file.


# To call sys.exit
import sys

# For guessing the file type and searching for section/key/value
import re

# For checking if the file exists
import os

__version__ = '0.1'


class cskv(object):
    # Functions to edit the config file
    # Usage: Parse_File(OPTIONS_DICTIONARY)
    # OPTIONS_DICTIONARY = {'config_file': CONFIG_FILE, 'section': SECTION}
    # More options: key, value, indent, ftype

    def __init__(self, **kwargs):
        # Initilize the kwargs dictionary, which contains all variables
        try:
            self.config_file = kwargs['config_file']
        except Exception as e:
            sys.exit("ERROR: No config_file provided")

        self.kwargs = kwargs

        if 'verbosity' not in self.kwargs:
            self.kwargs['verbosity'] = 0

        none_opts = ['section', 'key', 'value', 'indent', 'sep', 'test']
        for opt in none_opts:
            if opt not in self.kwargs:
                self.kwargs[opt] = None

        if 'extra_conf' not in self.kwargs:
            self.kwargs['extra_conf'] = []

        # Supported file formats and their key/value separators
        self.separators = {'ini': '=', 'rawe': '=', 'rawc': ':', 'raws': ' '}

        self.vprt(3, '')
        self.vprt(3, '   Running cskv with the following arguments')
        self.vprt(3, '   ------------------------------------')
        for arg in self.kwargs:
            self.vprt(3, '    ' + arg + ' = ' + str(self.kwargs[arg]))
        self.vprt(3, '   ------------------------------------')
        self.vprt(3, '')

        self.icontent = self.content()
        self.iftype = self.guess_conf_type(self.icontent)

    def vprt(self, iverb, string):
        # Control the verbosity of the output:
        # 0: nothing, 1: errors, 2: warnings and 3: info
        # Usage: vprt(LINE_VERBOSITY, "TEXT TO PRINT")
        if iverb <= self.kwargs['verbosity']:
            print string

    def content(self):
        # Read the content of a file into a list of lines
        # Usage: content(FILE_NAME)
        config_content = []

        self.vprt(3, "   Reading content of file "+self.config_file)
        for line in open(self.config_file, 'r'):
            config_content.append(line.rstrip())
        return config_content

    def guess_conf_type(self, config):
        # Guess the config file type ini/raw/rawc/raws
        # Usage: guess_conf_type(LIST_OF_CONFIG_LINES)
        guess_ini, guess_rawe, guess_rawc, guess_raws = 0, 0, 0, 0
        guess_ini_file = False
        ftype = None

        if self.config_file.endswith(('.ini', '.INI')):
            guess_ini_file = True

        for line in config:
            if re.match('\[.*\]', line):
                guess_ini += 1
            if guess_ini > 0:
                if not re.match('\[.*\]', line):
                    guess_ini += 1

        if guess_ini > 1:
            if guess_ini_file:
                ftype = 'ini'
            else:
                # The configuration has "INI" format but no .ini file
                # This happens always with the pipeline lines
                # because they are not read from a file
                ftype = 'ini'
        else:
            if guess_ini_file:
                msg = 'ERROR: the file name ' + self.config_file + \
                      ' has "ini" extension, but the content does not seem' \
                      + ' like INI syntax'
                self.vprt(1, msg)
                sys.exit()

            for line in config:
                if re.match('.*=.*', line):
                    guess_rawe += 1
                elif re.match('.*:.*', line):
                    guess_rawc += 1
                elif re.match('.* .*', line):
                    guess_raws += 1

            raws = {'rawe': guess_rawe, 'rawc': guess_rawc, 'raws': guess_raws}
            ftype = max(raws, key=raws.get)

        msg = '   The file "' + self.config_file + '" seems to have "' + \
            ftype + '" syntax.'
        self.vprt(3, msg)

        return ftype

    def guess_separator(self, config):
        # Guess key/value separator with spaces (the most common one)
        # Usage: guess_separator(LIST_OF_CONFIG_LINES)

        isep = self.separators[self.iftype]

        tmplst_left = []
        tmplst_right = []
        for line in config:
            if not re.match('^\[.*\]', line) and len(line) > 3:
                left = line.split(isep)[0]
                right = isep.join(line.split(isep)[1:])
                l_spaces = len(left) - len(left.rstrip())
                r_spaces = len(right) - len(right.lstrip())

                tmplst_left.append(l_spaces)
                tmplst_right.append(r_spaces)

        l_pad = max(set(tmplst_left), key=tmplst_left.count)
        r_pad = max(set(tmplst_right), key=tmplst_right.count)
        sep = ' '*l_pad + isep + ' '*r_pad

        msg = '   The separator is |KEY"' + sep + '"VALUE|'
        self.vprt(3, msg)
        return sep

    def guess_indent(self, config):
        # Guess the most common indentation for non section lines
        # Usage: guess_indent(LIST_OF_CONFIG_LINES)
        tmplst = []
        for line in config:
            if not re.match('^\[.*\]', line) and len(line) > 3:
                l_spaces = len(line) - len(line.lstrip())
                tmplst.append(l_spaces)

        indent = max(set(tmplst), key=tmplst.count)

        msg = '   The autoindentation detected ' + str(indent) + ' blanks'
        self.vprt(3, msg)
        return indent*' '

    def section_range(self, config, section):
        # Find the range of indexes in a list of lines where an entry
        # could be added (beginning and end of section in a INI)
        # Usage: section_range(LIST_OF_CONFIG_LINES,SECTION)

        # Find the list index of the line matching our [section]
        if not section:
            section = ''
        section_regex = re.compile('^\[' + section + '\]')
        section_idx = [i for i, item in enumerate(config)
                       if re.match(section_regex, item)]

        ftype = self.iftype
        if len(section_idx) == 0 or ftype != "ini":
            # Section not in file or not "INI" type ==> we'll append later
            msg = '  Waring: Section "' + section + '" missing in file, ' +\
                'creating it.'
            self.vprt(2, msg)
            start_idx, end_idx = None, None
        elif len(section_idx) > 1:
            # The section was found multiple times (Potential error!!)
            duplicate_sections = [item for i, item in enumerate(content)
                                  if re.match(section_regex, item)]
            msg = 'ERROR: more than one ' + section + ' sections found:' +\
                  '      ', duplicate_sections, ' on indexes ', section_idx
            self.vprt(1, msg)
            sys.exit()

        else:
            start_idx = section_idx[0] + 1

        if start_idx:
            # Also find the index of the last line in the section
            section_idx = [i for i, item in enumerate(config)
                           if re.match(section_regex, item)][0]
            for i, line in enumerate(config):
                if i > section_idx:
                    if re.match('^\[.*\]', line):
                        end_idx = i-1
                        break

            try:
                end_idx
            except Exception as e:
                end_idx = len(config)-1

        if start_idx and end_idx:
            msg = '   The entry will be parsed between lines ' + \
                str(start_idx) + ' and ' + str(end_idx)
        else:
            msg = '   The entry will be parsed on the whole file'
        self.vprt(3, msg)
        return [start_idx, end_idx]

    def insert(self, section, key, value):
        # Insert a key/value on the right place on config file
        # Returns a new "content" list of lines
        # Usage: insert(SECTION,KEY,VALUE)

        content = self.icontent
        ftype = self.iftype

        # Was the indent provided on command line?
        if self.kwargs['indent'] and self.kwargs['indent'] != 'a':
            indent = self.kwargs['indent']
        else:
            indent = self.guess_indent(content)

        if self.kwargs['sep']:
            sep = self.kwargs['sep']
        else:
            sep = self.guess_separator(content)

        idxs = self.section_range(content, section)
        matched = False
        if not idxs[0] and ftype != 'ini':
            idxs = [0, len(content)-1]
        elif not idxs[0] and ftype == 'ini' and section:
            content.append('['+section+']')
            idxs = [len(content)-2, len(content)-1]

        if ftype != "ini" and section:
            msg = '  Warning: [' + section + '] given, but our file "' + \
                  self.config_file + '" does not have INI format'
            self.vprt(2, msg)

        start_idx, end_idx = idxs

        new_line = indent + key + sep + value

        # Here comes the actual parsing part
        for i, line in enumerate(content):
            # Strip spaces from line and key
            lstr = line.strip()
            kstr = key.strip()
            # Also strip comments and extra spaces from line
            lstrcs = lstr.strip('#').strip()

            # We will only work on a given slice (because of the INIs)
            if i >= start_idx and i <= end_idx:
                # The key is uncommented => set it
                if lstr.startswith(kstr):
                    if not matched:
                        content[i] = new_line
                        matched = True
                    else:
                        content[i] = '# ' + content[i]
                # The key is commented out => set it
                elif lstr.startswith('#'):
                    # The line starts with KEY+space or KEY+SEPARATOR
                    if lstrcs.startswith((kstr+' ', kstr+sep)):
                        if not matched:
                            content[i] = new_line
                            matched = True

        if not matched:
            while content[end_idx].strip() == "":
                end_idx = end_idx - 1
            content.insert(end_idx+1, new_line)

        return content

    def extra2skv(self):
        # Convert the "extra" (pipelined) arguments into a list of [s,k,v]
        extra = self.kwargs['extra_conf']
        extra_skvs = []
        if len(extra) > 0:
            eftype = self.guess_conf_type(extra)
            if eftype != self.iftype:
                msg = 'ERROR: config file and extra data format are different'
                self.vprt(1, msg)
                sys.exit()

            isep = self.separators[eftype]

            if eftype == 'ini':
                for line in extra:
                    sline = line.strip()
                    if re.match('\[.*\]', line):
                        isec = sline.strip('[]')
                    elif len(sline) > 0 and not sline.startswith('#'):
                        ikey = sline.split(isep)[0].strip()
                        ival = isep.join(sline.split(isep)[1:]).strip()
                        extra_skvs.append([isec, ikey, ival])
            else:
                for line in extra:
                    sline = line.strip()
                    isec = None
                    if len(sline) > 0 and not sline.startswith('#'):
                        ikey = sline.split(isep)[0].strip()
                        ival = isep.join(sline.split(isep)[1:]).strip()
                        extra_skvs.append([isec, ikey, ival])

        return extra_skvs

    def process(self):
        # Run all the functions above, also for pipeline or file options
        # Usage: process()

        # -s, -k and -v from command line:
        content = self.icontent
        kwargs = self.kwargs

        section = kwargs['section']
        key = kwargs['key']
        value = kwargs['value']
        if key:
            content = self.insert(section, key, value)

        # Process the extra_conf (file/piped) values
        for section, key, value in self.extra2skv():
            content = self.insert(section, key, value)

        # Print output to stdout or file
        if not kwargs['test']:
            self.vprt(3, '   Printing output to file ' + self.config_file)
            output = open(self.config_file, 'w')
            for line in content:
                print>>output, line
            output.close()
        else:
            self.vprt(2, " ")
            for line in content:
                print line

        return content


if __name__ == "__main__":
    # The program is being called from command line
    # Parse Command line arguments
    import argparse
    from argparse import RawTextHelpFormatter

    examples_text = '''
    Examples:
      - Change value in INI file, add to section if it is not already present.
         cksv /etc/samba/smb.conf -s global -k "passdb backend" -v tdbsam
      - Change value in a raw config file.
         cksv /etc/ssh/sshd_config -k PasswordAuthentication -v no
      - Merge the content of some file into our config:
         cskv /etc/samba/smb.conf -e extra_conf.ini
    '''

    description_text = '''
    CKSV is a python script for editing values in configuration files.
    It can handle INI or raw files (key value separated by "=", ":" or " ".
    '''

    parser = argparse.ArgumentParser(
                      description=description_text,
                      epilog=examples_text,
                      formatter_class=RawTextHelpFormatter
                      )

    parser.add_argument('config_file', type=str, nargs='+',
                        help='Configuration file name or path to it'
                        )

    parser.add_argument('-s', '--section', type=str,
                        help='Section (for INI type files)'
                        )

    parser.add_argument('-k', '--key', type=str,
                        help='Key/variable name as string'
                        )

    parser.add_argument('-v', '--value', type=str,
                        help='Value for the given key.'
                        )

    parser.add_argument('-i', '--indent', type=str, default='a',
                        help='"quoted" spaces or tabs for line indentation.\n'
                        'Def. "a" (autoindentation): most common indentation\n'
                        ' in the file\n'
                        )

    parser.add_argument('--sep', type=str,
                        help='Separator between key and value'
                        )

    parser.add_argument('-t', '--test', action='store_true',
                        help='Print output to stdout instead of the file'
                        )

    parser.add_argument('-e', '--extra', nargs='*',
                        type=str, default='-',
                        help='Use this option to parse extra values.\n'
                             'Works with pipes and/or files'
                        )

    parser.add_argument('--verbosity', type=int, default=0,
                        choices=[0, 1, 2, 3],
                        help='Verbosity level:\n'
                             ' 0:nothing, 1:error, 2:warning, 3:info'
                        )

    parser.add_argument('-f', '--ftype', type=str,
                        choices=['ini', 'rawe', 'rawc', 'raws'],
                        help='Config file type:\n'
                        '  * ini: DOS like Section/key/value format:\n'
                        '      [section]\n'
                        '      variable1=value1\n'
                        '      variable2=value2\n'
                        '  * rawe (equals), rawc (colon), raws (space):\n'
                        '    lines with key-value pairs with different\n'
                        '    separators (=,:," "). Example of "rawe":\n'
                        '      variable1=value1)\n'
                        '      variable2=value2)\n'
                        )

    args = parser.parse_args()

    opts = {}
    for arg in vars(args):
        opts.update({arg: getattr(args, arg)})

    opts.update({'config_file': opts['config_file'][0]})

    # Parse extra config lines from pipeline or a file (or both)
    def extra_config(argv):
        parg_idx = False
        for i, arg in enumerate(sys.argv):
            if arg == '-e' or arg == '--extra':
                parg_idx = i
                break

        extra_lines = []
        if parg_idx:
            if len(sys.argv) > parg_idx + 1:
                if not sys.argv[parg_idx + 1].startswith('-'):
                    # print 'We have a file'
                    if os.path.isfile(sys.argv[parg_idx+1]):
                        for line in open(sys.argv[parg_idx+1], 'r'):
                            if len(line.strip()) > 0:
                                extra_lines.append(line.strip())
                else:
                    for line in sys.stdin:
                        if len(line.strip()) > 0:
                            extra_lines.append(line.strip())

            else:
                # print 'We are getting extra options from file/pipeline'
                for line in sys.stdin:
                    if len(line.strip()) > 0:
                        extra_lines.append(line.strip())
        return extra_lines

    extra_config = extra_config(sys.argv)

    opts.update({'extra_conf': extra_config})

    cfile = cskv(**opts)

    cfile.process()
