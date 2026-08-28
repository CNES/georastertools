#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from . import cmptools

__author = "Olivier Queyrut"
__copyright = "Copyright 2019, CNES"
__license = "Apache v2.0"

indir = "tests/tests_data/"
outdir = "tests/tests_out/"
__root_refdir = "tests/tests_refs/"


@dataclass
class RastertoolsTestsData:

    project_dir: Path = Path(__file__).parent.parent
    tests_project_dir:str = str(project_dir)
    tests_input_data_dir:str = str(project_dir / "tests" / "tests_data" )
    tests_output_data_dir:str = str(project_dir / "tests" / "tests_out")
    tests_ref_data_dir:str = str(project_dir / "tests" / "tests_refs")

def get_refdir(testname: str):
    return RastertoolsTestsData.tests_ref_data_dir + '/' + testname


def clear_outdir(subdirs=True):
    """function to clear content of a dir"""
    for file in os.listdir(RastertoolsTestsData.tests_output_data_dir + '/'):
        file_path = os.path.join(RastertoolsTestsData.tests_output_data_dir + '/', file)
        if os.path.isfile(file_path):
            os.unlink(file_path)
        elif subdirs:
            # delete the subdir
            delete_dir(file_path)


def create_outdir():
    if not os.path.isdir(RastertoolsTestsData.tests_output_data_dir + '/'):
        os.makedirs(RastertoolsTestsData.tests_output_data_dir + '/')
    clear_outdir()


def delete_dir(dir):
    shutil.rmtree(dir)


def copy_to_ref(files, refdir):
    for f in files:
        os.replace(RastertoolsTestsData.tests_output_data_dir + '/' + f, refdir + f)


def basename(infile):
    """
    Function to get basename of file
    """
    file = Path(infile) if isinstance(infile, str) else infile
    suffix = len("".join(file.suffixes))
    return file.name if suffix == 0 else file.name[:-suffix]


def cmpfiles(a : str, b : str, common : list, tolerance : float=1e-9, **kwargs) -> tuple:
    """
    Compare common files in two directories.

    Args:
    a, b (str) : Directory names
    common (list) : List of file names found in both directories

    Returns:
      Tuple of three lists ( [files that are the same], [files that differs], [filenames that aren't regular files] )
    """
    res = ([], [], [])
    for x in common:
        new = os.path.join(a, x)
        golden = os.path.join(b, x)
        res[_cmp(golden, new, tolerance, **kwargs)].append(x)
    return res


def _cmp(gld, new, tolerance, **kwargs):
    """

    """

    ftype = os.path.splitext(gld)[-1].lower()
    cmp = cmptools.CMP_FUN[ftype]
    try:
        return not cmp(gld, new, tolerance=tolerance, **kwargs)
    except OSError:
        return 2
