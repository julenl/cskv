#!/usr/bin/env python

import os
import sys
import shutil
import re

# For interactive functionality
import subprocess

full_path = os.path.dirname(os.path.abspath(__file__))
cskv_dir = os.path.abspath(os.path.join(full_path, os.pardir))
cskv_cmd = os.path.abspath(os.path.join(cskv_dir, 'cskv.py'))

# Directory with original templates
orig_dir = os.path.abspath(os.path.join(full_path, 'orig'))
# Directory where originals are copied and processed
results_dir = os.path.abspath(os.path.join(full_path, 'results'))

sys.path.insert(0, cskv_dir)

try:
    from cskv import cskv
except Exception as e:
    print 'ERROR: unable to import cskv'
    sys.exit(1)


def reset_results_dir():
    try:
        shutil.rmtree(results_dir)
        # os.remove('./results')
    except OSError:
        pass

    shutil.copytree(orig_dir, results_dir)


reset_results_dir()

# file properties "ftype" = [fname, separator]
fprops = {}
fprops['ini'] = [results_dir + '/testfile.ini', '=']
fprops['rawe'] = [results_dir + '/testfile.rawe', '=']
fprops['rawc'] = [results_dir + '/testfile.rawc', ':']
fprops['raws'] = [results_dir + '/testfile.raws', ' ']


opts = {}
opts['config_file'] = results_dir + '/testfile.ini'
opts['section'] = 'section1'
opts['key'] = 'variable1'
opts['value'] = 'newvalue1'


print 'Testing cskv as python module:'

# vprt
cfile = cskv(**opts)
vprt_0 = cfile.vprt(0, 'Test_vprt_0')
vprt_1 = cfile.vprt(1, 'Test_vprt_1')

if vprt_0 == 'Test_vprt_0' and not vprt_1:
    print 'INFO: function "vprt" for printing output: OK'
else:
    print 'ERROR: function "vprt" for printing output failed'
    sys.exit(1)

# content

content = cfile.content(opts['config_file'])

fail_test = True
for line in content:
    if '[section1]' in line:
        fail_test = False

if fail_test:
    print 'ERROR: function "content" for returning content failed'
    sys.exit(1)
else:
    print 'INFO: function "content" for returning content: OK'


# guess_conf_type

for ftype in fprops:
    opts['config_file'] = fprops[ftype][0]
    cfile = cskv(**opts)
    content = cfile.content(opts['config_file'])
    iftype = cfile.guess_conf_type(content)

    if iftype == ftype:
        print 'INFO: function "guess_conf_type" for guessing config type: OK'
    else:
        print 'ERROR: config type for ' + ftype + ' was not detected properly'
        print '  The result of guess_conf_type is:', iftype,
        print ' instead of:', ftype
        print '  opts = ', opts
        sys.exit(1)


# guess_separator

for ftype in fprops:
    opts['config_file'] = fprops[ftype][0]
    sep = fprops[ftype][1]
    cfile = cskv(**opts)
    content = cfile.content(opts['config_file'])

    isep = cfile.guess_separator(content)

    if sep in isep:
        print 'INFO: function "guess_separator" for "' + sep,
        print '" for ' + ftype + ': OK'
    else:
        print 'ERROR: config type for INI was not detected properly'
        print '  The result of guess_separator is:', isep, ' instead of:',
        print sep
        print '  opts = ', opts
        sys.exit(1)

# guess_indent

for ftype in fprops:
    opts['config_file'] = fprops[ftype][0]
    cfile = cskv(**opts)
    content = cfile.content(opts['config_file'])

    iind = cfile.guess_indent(content)

    if ftype == 'ini' and len(iind) != 2:
        print 'ERROR: function "guess_indent" failed for INI format'
        sys.exit(1)

    elif 'raw' in ftype and len(iind) != 0:
        print 'ERROR: function "guess_indent" failed for ' + ftype
        sys.exit(1)

    else:
        print 'INFO: function "guess_indent" for guessing indentation (ftype=',
        print ftype + '): OK'


# section_range

opts['config_file'] = fprops['ini'][0]
cfile = cskv(**opts)
content = cfile.content(opts['config_file'])


# Find the section range in an alternative way, just to compare results
def alt_sec_range(content, section=''):
    alt_sec_range = []
    for n, line in enumerate(content):
        if section in line:
            alt_sec_range = [n+1]
        elif alt_sec_range and re.match('\[.*\]', line):
            alt_sec_range.append(n-1)
            break
    if not alt_sec_range:
        alt_sec_range = [None, None]
    elif len(alt_sec_range) == 1:
        alt_sec_range.append(n)

    return alt_sec_range


# Check for two section ranges in INI format
sec_range = cfile.section_range(content, 'section1')
if sec_range == alt_sec_range(content, 'section1'):
    print 'INFO: function "section_range" for "section1" in ',
    print opts['config_file'], ': OK'
else:
    print 'ERROR: section1 range not detected properly'
    sys.exit(1)


sec_range = cfile.section_range(content, 'sectionA')
if sec_range == alt_sec_range(content, 'sectionA'):
    print 'INFO: function "section_range" for "sectionA" in ',
    print opts['config_file'], ': OK'
else:
    print 'ERROR: sectionA range not detected properly'
    sys.exit(1)


# Check RAWE format
opts['config_file'] = fprops['rawe'][0]
cfile = cskv(**opts)
content = cfile.content(opts['config_file'])

sec_range = cfile.section_range(content, 'iaa')
if sec_range == [None, None]:
    print 'INFO: function "section_range" for "RAWE file" in ',
    print opts['config_file'], ': OK'
else:
    print 'ERROR: section range not detected properly on', opts['config_file']
    sys.exit(1)


# insert

for ftype in fprops:
    opts['config_file'] = fprops[ftype][0]
    sep = fprops[ftype][1]
    cfile = cskv(**opts)
    content = cfile.content(opts['config_file'])
    key = opts['key']
    value = opts['value']
    new_cont = cfile.insert('section1', 'variable1', 'newvalue1')

    fail_test = True
    for line in new_cont:
        if key in line and sep in line and value in line:
            fail_test = False

    if fail_test:
        print 'ERROR: insert s/k/v failed on', opts['config_file']
        sys.exit(1)
    else:
        print 'INFO: function "insert" for ', opts['config_file'],  ': OK'

# insert (emtpy value)
opts.pop('value', None)
for ftype in fprops:
    opts['config_file'] = fprops[ftype][0]
    sep = fprops[ftype][1]
    cfile = cskv(**opts)
    content = cfile.content(opts['config_file'])
    key = opts['key']
    new_cont = cfile.insert('section1', 'variable1')

    fail_test = True
    for line in new_cont:
        # If line contains separator
        if line.split(sep) > 0:
            parse_key = line.split(sep)[0]
        else:
            parse_key = line

        if key in parse_key:
            fail_test = False

    if fail_test:
        print 'ERROR: insert s/k empty value on', opts['config_file']
        sys.exit(1)
    else:
        print 'INFO: function "insert" for', opts['config_file'],
        print '(empty value): OK'

opts['value'] = 'newvalue1'

# insert (blank separator)
for ftype in fprops:
    opts['config_file'] = fprops[ftype][0]
    sep = ' '
    opts['sep'] = sep
    opts['sep'] = ' '
    cfile = cskv(**opts)
    content = cfile.content(opts['config_file'])
    key = opts['key']
    value = opts['value']
    new_cont = cfile.insert('section1', key, value)

    fail_test = True
    for line in new_cont:
        if len(line.strip()) > 0:
            if re.match(key + ' ' + value, line.strip()):
                fail_test = False

    if fail_test:
        print 'ERROR: insert s/k blank separator on', opts['config_file']
        sys.exit(1)
    else:
        print 'INFO: function "insert" for', opts['config_file'],
        print '(blank separator): OK'

opts.pop('sep')

# delete
opts['key'] = 'deleteme'
opts['value'] = 'whatever'

opts['delete'] = True
for ftype in fprops:
    opts['config_file'] = fprops[ftype][0]
    sep = fprops[ftype][1]
    cfile = cskv(**opts)
    content = cfile.content(opts['config_file'])
    key = opts['key']
    value = opts['value']
    new_cont = cfile.delete()

    # Get only key/values for INI files
    if ftype == 'ini':
        new_cont = cfile.get_keyvals(new_cont, opts['section'])

    fail_test = False
    for line in new_cont:
        if len(line.strip()) > 0:
            if line.strip().startswith(key) and '_' not in line:
                fail_test = True

    if fail_test:
        print 'ERROR: deleting line with key on', opts['config_file']
        sys.exit(1)
    else:
        print 'INFO: function "delete" for', opts['config_file'],  ': OK'

opts.pop('delete', None)

opts['key'] = 'variable1'
opts['value'] = 'newvalue1'

# extra2skv

extra_conf = """
[newsection]
  newvariable1 = newvalue1
  newvariable2 = newvalue2
"""

opts['config_file'] = fprops['ini'][0]
opts['extra_conf'] = extra_conf
cfile = cskv(**opts)
content = cfile.content(opts['config_file'])

extra_c = [['newsection', 'newvariable1', 'newvalue1'],
           ['newsection', 'newvariable2', 'newvalue2']]

extra_skvs = cfile.extra2skv()

if extra_skvs == extra_c:
    print 'INFO: option "extra_config" (extra/piped config) for INI: OK'
else:
    print 'ERROR: unable to parse extra/piped config for ini'
    sys.exit(1)


# process

opts.pop('extra_conf', None)
for ftype in fprops:
    opts['config_file'] = fprops[ftype][0]
    sep = fprops[ftype][1]
    cfile = cskv(**opts)
    content = cfile.content(opts['config_file'])
    key = opts['key']
    value = opts['value']
    new_cont = cfile.process()

    fail_test = True
    for line in new_cont:
        if key in line and sep in line and value in line:
            fail_test = False

    if fail_test:
        print 'ERROR: process failed on', opts['config_file'],
        print ' as return value'
        sys.exit(1)
    else:
        print 'INFO: option "extra_config" on', opts['config_file'],
        print 'as return value: OK'

    fail_test = True
    for line in open(opts['config_file'], 'r'):
        if key in line and sep in line and value in line:
            fail_test = False

    if fail_test:
        print 'ERROR: process failed on', opts['config_file'],
        print ' as written file'
        sys.exit(1)
    else:
        print 'INFO: function "process" on', opts['config_file'],
        print 'as written file: OK'


# compare

# I am using the opts['key'] and opts['value'] just for filtering the output
# They don't do anything regarding this cskv request
for ftype in fprops:
    opts['config_file'] = fprops[ftype][0]
    opts['compare'] = fprops[ftype][0].replace('results', 'orig')
    sep = fprops[ftype][1]
    cfile = cskv(**opts)
    contenta = cfile.content(opts['config_file'])
    contentb = cfile.content(opts['compare'])
    new_cont = cfile.compare_confs()

    fail_test = True
    for line in new_cont:
        if opts['key'] in line and opts['value'] in line:
            fail_test = False

    if fail_test:
        print 'ERROR: compare failed on', opts['config_file']
        sys.exit(1)
    else:
        print 'INFO: function "compare" for ', opts['config_file'], ': OK'


# ######################################
# Testing interactive (shell) interface
# ######################################

print
print 'Testing cskv as command line tool:'


def test_value(ftype, section, key, value, extra_opt='', extra_val=''):
    orig_name = orig_dir + '/testfile.' + ftype
    file_name = results_dir + '/testfile.' + ftype
    cmd = ['python', cskv_cmd, file_name, '-s', section, '-k', key, '-v',
           value]
    if extra_opt:
        cmd.append(extra_opt)
    if extra_val:
        cmd.append(extra_val)

    print "SP", cmd
    out = subprocess.check_output(cmd)

    testok = False
    for line in open(file_name, 'r'):
        if key in line and value in line:
            testok = True

    if key.startswith('deleteme_int'):
        key_found = False
        for line in open(file_name, 'r'):
            if line.strip().startswith(key):
                key_found = True

        if not key_found:
            testok = True

    if testok:
        return 'OK'
    else:
        print
        print 'ERROR: the following command failed:'
        print ' '.join(cmd)
        sys.exit(1)


changes = {}
changes['section1'] = ['interactive', 'ok', 'Edit key/val']
changes['section a'] = ['new interactive', 'newvalue value',
                        'New key/val with spaces']
changes['sectionA'] = ['deleteme_int', 'whatever', 'Delete key/val',
                       '--delete']


for ftype in ['ini', 'rawe', 'rawc', 'raws']:
    for sec in changes:
        skip_test = False
        key = changes[sec][0]
        value = changes[sec][1]
        comment = changes[sec][2]
        extra_opt, extra_val = '', ''
        if len(changes[sec]) > 3:
            extra_opt = changes[sec][3]
        if len(changes[sec]) > 4:
            extra_val = changes[sec][4]

        if ftype != 'ini':
            sec = ''
        if ftype == 'raws':
            # Do not test stuff with spaces on RAWS
            if 'space' in comment:
                if len(key.split()) > 1 or len(value.split()) > 1:
                    skip_test = True

        if not skip_test:
            print 'INFO:  ' + comment + ' (ftype=' + ftype.upper() + '):',
            print test_value(ftype, sec, key, value, extra_opt, extra_val)
