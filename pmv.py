#!/usr/bin/pypy

# Usage:
# ./pmv <files to rename>
# e.g. ./pmv 1020102.pdf 23510924.pdf fast_paper_10.pdf
#
# By default, files land in your current directory.  To specify an output 
# directory, use the format:
# ./pmv --dir my/output/directory <files> 
#
# or simply modify this file.

from __future__ import print_function

import codecs
import os
import sys
import tempfile
import traceback

try:
    import subprocess32 as subprocess
except ImportError:
    import subprocess

try:
    from rename_by_title import *
except ImportError:
    # Input the path to rename_by_title.py.  It is pure laziness that
    # prevents this from being packaged.
    renamepath = ''
    while renamepath == '':
        renamepath = raw_input('Please enter the path to rename_by_title.py')
    sys.path.append(renamepath)
    from rename_by_title import *

if sys.argv[1] == '--dir':
    paper_dir = sys.argv[2]
    sys.argv.pop(1)
    sys.argv.pop(1)
    print('Saving output to %s' % paper_dir)
else:
    paper_dir = None

for input_name in sys.argv[1:]:
    mime_type = subprocess.check_output(['file', '--brief', '--mime-type',
                                         input_name]).strip()
    # print(mime_type)
    _, tmp_name = tempfile.mkstemp()
    try:
        if mime_type == 'application/pdf':
            try:
                # Try pdftotext first.
                subprocess.check_call(['pdftotext', input_name, tmp_name])
                print('Successfully parsed %s with pdftotext.' % input_name)
                title = guess_title(tmp_name, 'utf-8')
            except (TitleError, OSError):
                # Try PDFMiner if pdftotext fails or isn't available.
                with open(input_name, 'r') as pdf_file, open(tmp_name,
                                                             'w') as tmp_file:
                    pdf_miner(pdf_file, tmp_file)
                print('Successfully parsed %s with PDFMiner.' % input_name)
                title = guess_title(tmp_name, 'utf-8')
            extension = '.pdf'
        elif mime_type == 'application/postscript':
            subprocess.check_call(['pstotext', '-output', tmp_name,
                                   input_name])
            print('Successfully parsed %s with pstotext.' % input_name)
            title = guess_title(tmp_name, 'latin-1')
            extension = '.ps'
        else:
            raise ValueError('%s is not a PDF or Postscript file.' %
                             input_name)
        fn = title_rename(title, input_name, extension)
        if paper_dir is not None:
            os.rename(fn, paper_dir + fn)
        else:
            os.rename(fn, os.path.dirname(input_name) + '/' + fn)
    except Exception:
        traceback.print_exc()
    finally:
        os.remove(tmp_name)
