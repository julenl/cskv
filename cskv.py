#!/usr/bin/python
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

__version__ = '0.2'


class cskv(object):
    # Functions to handle the config file
    # Usage: cskv(OPTIONS_DICTIONARY)
    # OPTIONS_DICTIONARY = {'config_file': CONFIG_FILE, 'section': SECTION, ..}
    # More options: key, value, indent, ftype, compare, verbosity

    def __init__(self, **kwargs):
        # Initilize the kwargs dictionary, which contains all variables

        try:
            self.config_file = kwargs['config_file']
            # Ensure the path to the file is absolute
            abs_path = os.path.abspath(kwargs['config_file'])
            self.config_file = abs_path
        except Exception as e:
            sys.exit("ERROR: No config_file provided or path cannot be found.")

        self.kwargs = kwargs

        # Running as a module does not have default verbosity
        if 'verbosity' not in self.kwargs:
            self.kwargs['verbosity'] = 0

        # If we have a file to compare with
        try:
            abs_path = os.path.abspath(kwargs['compare'])
            self.icompare = self.content(abs_path)
        except Exception as e:
            self.icompare = None
            pass

        # Clear these option/variables
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

        # File content as a list of lines
        self.icontent = self.content(kwargs['config_file'])
        self.iftype = self.guess_conf_type(self.icontent)

    def vprt(self, iverb, string):
        # Control the verbosity of the output:
        # 0: nothing, 1: errors, 2: warnings and 3: info
        # Usage: vprt(LINE_VERBOSITY, "TEXT TO PRINT")
        if iverb <= self.kwargs['verbosity']:
            return string

    def content(self, file_name):
        # Read the content of a file into a list of lines
        # Usage: content(FILE_NAME)
        config_content = []

        print_me = self.vprt(3, "   Reading content of file " + file_name)
        if print_me:
            print print_me

        for line in open(file_name, 'r'):
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
                print_me = self.vprt(1, msg)
                if print_me:
                    print print_me
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

        print_me = self.vprt(3, msg)
        if print_me:
            print print_me

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
        print_me = self.vprt(3, msg)
        if print_me:
            print print_me
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
        print_me = self.vprt(3, msg)
        if print_me:
            print print_me

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
            print_me = self.vprt(2, msg)
            if print_me:
                print print_me
            start_idx, end_idx = None, None

        elif len(section_idx) > 1:
            # The section was found multiple times (Potential error!!)
            duplicate_sections = [item for i, item in enumerate(content)
                                  if re.match(section_regex, item)]
            msg = 'ERROR: more than one ' + section + ' sections found:' +\
                  '      ', duplicate_sections, ' on indexes ', section_idx
            print_me = self.vprt(1, msg)
            if print_me:
                print print_me
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

        print_me = self.vprt(3, msg)
        if print_me:
            print print_me
        return [start_idx, end_idx]

    def insert(self, section, key, value=''):
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

    def delete(self, section=None, key=None):
        # Delete a line containing a key on config file
        # Returns a new "content" list of lines (without the line)
        # Usage: delete(SECTION,KEY)

        if not key:
            key = self.kwargs['key']
        if not section:
            section = self.kwargs['section']

        content = self.icontent
        ftype = self.iftype

        if ftype == 'ini' and not section:
            print 'ERROR: parsing INI files requires to specify a section'
            print '       use the "-s" flag'
            sys.exit(1)

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

        for i, line in enumerate(content):
            # Strip spaces from line and key
            lstr = line.strip()
            kstr = key.strip()
            # Also strip comments and extra spaces from line
            lstrcs = lstr.strip('#').strip()

            if i >= start_idx and i <= end_idx:
                # key found => delete it
                if lstr.startswith(kstr):
                    del content[i]

        return content

    def extra2skv(self):
        # Convert the "extra" (pipelined) arguments into a list of [s,k,v]
        extra_skvs = []
        if self.kwargs['extra_conf']:
            extra = self.kwargs['extra_conf'].splitlines()
            eftype = self.guess_conf_type(extra)
            if eftype != self.iftype:
                msg = 'ERROR: config file and extra data format are different'
                print_me = self.vprt(1, msg)
                if print_me:
                    print print_me
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

    def get_ini_sections(self, content):
        # Get the list of sections on an ini file
        sections = []
        for line in content:
            if re.match('\[.*\]', line):
                section = line.strip('[]')
                sections.append(section)
        return sections

    def get_keyvals(self, content, section):
        # Get a dict of key/values present on a section
        keyvals = {}

        ftype = self.guess_conf_type(content)
        sep = self.separators[ftype]

        if self.guess_conf_type(content) == 'ini':
            parse = False
        else:
            parse = True

        for line in content:
            if re.match('\[.*\]', line):
                if section in line:
                    parse = True
                else:
                    parse = False

            elif parse is True:
                if not line.startswith(('#', ';')) and len(line.strip()) > 0:
                    lines = line.split(sep)
                    key = lines[0].strip()
                    if len(lines) > 1:
                        value = lines[1].strip()
                    else:
                        value = None
                    keyvals[key] = value
                    key, value = None, None
        return keyvals

    def compare_confs(self, contenta=None, contentb=None):
        # Compare both configuration files
        # We can provide two lists of lines explicitly
        # or it will take the content of "config_file" and "compare" in opts
        if not contenta:
            contenta = self.icontent
        if not contentb:
            contentb = self.icompare

        cta = self.guess_conf_type(contenta)
        ctb = self.guess_conf_type(contentb)
        if cta != ctb:
            msg = "ERROR: the config files " + self.kwargs['config']
            msg += " and " + self.kwargs['compare'] + " seem to have different"
            msg += " formats: (" + cta + " and " + ctb + ")"
            sys.exit()

        if cta == "ini":
            secs_a = self.get_ini_sections(contenta)
            secs_b = self.get_ini_sections(contentb)
            sections = sorted(set(secs_a + secs_b))
        else:
            sections = ['']

        # List containing output lines
        out_content = []

        # Print a header if the verbosity > 0
        if 0 < self.kwargs['verbosity']:
            msg = '>>>>>>>>>> Compare configuration files <<<<<<<<<<'
            out_content.append(msg)

        # Print the column headers with the file names
        msg = '  {:20} {:25}  {}'.format('',
                                         self.kwargs['config_file'],
                                         self.kwargs['compare'])
        out_content.append(msg)

        # Print a line under the title if the verbosity is >0
        if 0 < self.kwargs['verbosity']:
            msg = "-"*70
            out_content.append(msg)

        for sec in sections:
            # Do not print section names without differences
            print_section = False

            keyvalsa = self.get_keyvals(contenta, sec)
            keyvalsb = self.get_keyvals(contentb, sec)

            for key in sorted(set(keyvalsa.keys() + keyvalsb.keys())):
                if key in keyvalsa:
                    val_a = keyvalsa[key]
                else:
                    val_a = ''
                if key in keyvalsb:
                    val_b = keyvalsb[key]
                else:
                    val_b = ''

                if val_a != val_b:
                    # Print section header only after 1st difference found
                    if not print_section:
                        print_section = True
                        if sections != ['']:
                            out_content.append("##### " + sec + "####")

                    msg = '  {:20} {:25}  {}'.format(key, val_a, val_b)
                    out_content.append(msg)

                # If verbosity is > 1, print also the values that are identic
                elif self.kwargs['verbosity'] > 1:
                    msg = '  {:20} {:25}  {}'.format(key, val_a, val_b)
                    out_content.append(msg)

        return out_content

    def process(self):
        # Run all the functions above, also for pipeline or file options
        # Variables are defined in the opts dictionary and in the class init
        # Usage: process()

        content = self.icontent
        kwargs = self.kwargs

        if self.icompare:
            compare = self.icompare
            out_content = self.compare_confs(content, self.icompare)

        else:
            # Parse Key/Values (for section)
            kwargs = self.kwargs

            section = kwargs['section']
            key = kwargs['key']
            value = kwargs['value']
            if key:
                # Delete option requested, deleting line(s)
                if 'delete' in kwargs and kwargs['delete']:
                    content = self.delete(section, key)
                else:
                    # Parsing s/k/v from opts dictionary or as cmd arguments
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

            out_content = content

        return out_content


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
      - Delete line containing key/starting with "PermitRootLogin":
         cskv /etc/ssh/sshd_config -k "PermitRootLogin" --delete
      - Compare two config files:
         cskv /etc/samba/smb.conf --compare /root/old_smb.conf
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

    parser.add_argument('-c', '--compare', type=str,
                        help='Compare the config file with this one.\n'
                        )

    parser.add_argument('--sep', type=str,
                        help='Separator between key and value'
                        )

    parser.add_argument('-d', '--delete', action='store_true',
                        help='Delete line(s) defining a key (in section)'
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

    opts = {'interactive': True}
    for arg in vars(args):
        opts.update({arg: getattr(args, arg)})

    opts.update({'config_file': opts['config_file'][0]})

    if opts['compare']:
        opts.update({'compare': opts['compare']})

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

    output = cfile.process()
    if opts['compare']:
        for line in output:
            print line
