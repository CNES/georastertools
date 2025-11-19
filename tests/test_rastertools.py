#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os

from click.testing import CliRunner
from pathlib import Path

from eolab.georastertools import georastertools
from eolab.georastertools.product import RasterType

from . import utils4test

__author__ = "Olivier Queyrut"
__copyright__ = "Copyright 2019, CNES"
__license__ = "Apache v2.0"

from .utils4test import RastertoolsTestsData

_logger = logging.getLogger(__name__)

class TestCase:
    __test__ = False

    def __init__(self, args, sys_code=0):
        self._args = args.split()
        self._outputs = list()
        self._logs = list()
        self._sys_exit = sys_code

    def __repr__(self):
        return (f"georastertools {' '.join(self._args)}"
                f"[outputs={self._outputs}][logs={self._logs}][sys_exit={self._sys_exit}]")

    @property
    def args(self):
        return self._args

    @property
    def outputs(self):
        return self._outputs

    @property
    def logs(self):
        return self._logs

    @property
    def sys_exit(self):
        return self._sys_exit

    def output(self, filenames):
        self._outputs = filenames
        return self

    def ri_output(self, indices, indice_filenames):
        self._outputs = [f.format(ind) for ind in indices.split() for f in indice_filenames]
        return self

    def zs_output(self, input_filenames, outlier=False):
        # check list of outputs
        self._outputs = [f + "-stats.geojson" for f in input_filenames]
        if outlier:
            self._outputs.extend([file + "-stats-outliers.tif" for file in input_filenames])
        return self

    def ti_output(self, input_filenames, ids, name="{}-tile{}", subdir=""):
        if subdir:
            if not(subdir.endswith("/")):
                subdir = subdir + "/"
        else:
            subdir = ""
        self._outputs = [name.format(f, id) for id in ids for f in input_filenames]
        return self

    def fi_output(self, input_filenames, filter):
        self._outputs = [name.format(filter) for name in input_filenames]
        return self

    def with_logs(self, logs=list(), loglevel=logging.INFO):
        self._logs = logs
        self._loglevel = loglevel
        return self

    def with_sys_exit(self, sys_exit):
        self._sys_exit = sys_exit
        return self

    def with_refdir(self, refdir):
        self._refdir = refdir
        return self

    def run_test(self, caplog=None, loglevel=logging.ERROR, check_outputs=True, check_sys_exit=True, check_logs=True,
                 compare=False, save_gen_as_ref=False):

        runner = CliRunner()
        if caplog is not None:
            caplog.set_level(loglevel)
        else:
            check_logs = False

        try:
            georastertools(self.args)
        except Exception as wrapped_exception:
            if check_sys_exit:
                # Check if the exit code matches the expected value
                assert wrapped_exception.code == self._sys_exit, (f"Expected exit code {self._sys_exit}, but got {wrapped_exception.code}")
        except SystemExit as sys_e:
            if check_sys_exit:
                # Check if the exit code matches the expected value
                assert sys_e.code == self._sys_exit, (f"Expected exit code {self._sys_exit}, but got {sys_e.code}")

        # check list of outputs
        if check_outputs:
            outdir = Path(RastertoolsTestsData.tests_output_data_dir + "/")
            assert sorted([x.name for x in outdir.iterdir()]) == sorted(self._outputs)

        if compare:
            match, mismatch, err = utils4test.cmpfiles(RastertoolsTestsData.tests_output_data_dir + "/", self._refdir, self._outputs)

            assert len(match) == len([x.name for x in Path(self._refdir).iterdir()])
            assert len(mismatch) == 0
            assert len(err) == 0
        elif save_gen_as_ref:
            # save the generated files in the refdir => make them the new refs.
            utils4test.copy_to_ref(self._outputs, self._refdir)

        # check logs
        if check_logs:
            for i, log in enumerate(self._logs):
                assert caplog.record_tuples[i] == log

        # clear the log recorder
        if caplog is not None:
            caplog.clear()

        #clear output dir
        utils4test.clear_outdir()


def test_rastertools_command_line_info():

    tests = [
        TestCase("--help"),
        TestCase("-h"),
        TestCase("--version"),
        TestCase("", 2),
        TestCase("radioindice --help"),
        TestCase("ri -h"),
        TestCase("zonalstats --help"),
        TestCase("zs -h"),
        TestCase("tiling --help"),
        TestCase("ti -h"),
        TestCase("filter --help"),
        TestCase("fi -h"),
        TestCase("timeseries --help"),
        TestCase("ts -h"),
        TestCase("speed --help"),
        TestCase("sp -h"),
        TestCase("svf --help"),
        TestCase("svf -h"),
        TestCase("hillshade --help"),
        TestCase("hs -h")
    ]
    for test in tests:
        test.run_test()

def generate_lst_file(file_list, output_file):

    with open(output_file,"w") as lst_file:
        for f in file_list:
            lst_file.write(RastertoolsTestsData.tests_input_data_dir + "/" + f.split('/')[-1] + "\n")


def test_radioindice_command_line_default():
    # create output dir and clear its content if any
    utils4test.create_outdir()

    lst_file_path = f"{RastertoolsTestsData.tests_input_data_dir}/listing.lst"
    generate_lst_file(["SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip",
                       "SENTINEL2B_20181023-105107-455_L2A_T30TYP_D.zip"],
                      lst_file_path)

    # list of commands to test
    argslist = [
        # no indice defined
        f" -v ri -o {RastertoolsTestsData.tests_output_data_dir} {lst_file_path}",
        # two indices with their own options, merge
        f"-v ri --pvi --savi -o {RastertoolsTestsData.tests_output_data_dir} -m {lst_file_path}",
        # indices option, roi
        f"--verbose ri --indices pvi --indices savi -nd nir red --roi {RastertoolsTestsData.tests_input_data_dir}/COMMUNE_32001.shp"
        f" --output {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip"
        f" {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2B_20181023-105107-455_L2A_T30TYP_D.zip"
    ]
    # get list of expected outputs
    indices_list = ["ndvi ndwi ndwi2", "indices", "pvi savi nd[nir-red]"]
    indices_filenames = ["SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-{}.tif",
                         "SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-{}.tif"]

    # generate test cases
    tests = [TestCase(args).ri_output(indices, indices_filenames)
             for (args, indices) in zip(argslist, indices_list)]

    # execute test cases
    for test in tests:
        test.run_test()


def test_radioindice_additional_type():
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # add rastertypes to handle new data product
        f"-t {RastertoolsTestsData.tests_input_data_dir}/additional_rastertypes.json -v"
        f" ri -o {RastertoolsTestsData.tests_output_data_dir} --ndvi {RastertoolsTestsData.tests_input_data_dir}/RGB_TIF_20170105_013442_test.tif"
    ]
    # get list of expected outputs
    indices_list = "ndvi"
    indices_filenames = ["RGB_TIF_20170105_013442_test-{}.tif"]

    # generate test cases
    tests = [TestCase(args).ri_output(indices_list, indices_filenames)
             for args in argslist]

    # execute test cases
    for test in tests:
        test.run_test()

    assert RasterType.get("RGB_TIF") is not None
    assert RasterType.get("RGB_TIF_ARCHIVE") is not None


def test_radioindice_command_line_errors(caplog):
    # list of commands to test
    argslist = [
        # missing positional argument
        "ri --ndvi",
        # unkwnow indice
        f"ri {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip --indices strange",
        # unknown raster type: unrecognized raster type
         f"-v ri --ndvi -o {RastertoolsTestsData.tests_output_data_dir} {RastertoolsTestsData.tests_input_data_dir}/OCS_2017_CESBIO_extract.tif",
        # unknown raster type: unsupported extension
        f"-v ri --ndvi -o {RastertoolsTestsData.tests_output_data_dir} {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.aaa",
        # output dir does not exist
        f"-v ri -o ./toto --ndvi {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip",
        # unknown band in normalized difference
        f"-v ri -nd unknown red {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip"
    ]

    # expected logs
    logslist = [
        [],
        [("eolab.georastertools.georastertools", logging.ERROR, "Invalid indice name: strange")],
        [("eolab.georastertools.cli.utils_cli", logging.ERROR,
           "Unsupported input file, no matching raster type identified to handle the file")],
        [("eolab.georastertools.cli.utils_cli", logging.ERROR,
          f"Unsupported input file {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.aaa")],
        [("eolab.georastertools.georastertools", logging.ERROR,
          "Output directory \"./toto\" does not exist.")],
        [("eolab.georastertools.georastertools", logging.ERROR,
          "Invalid band(s) in normalized difference: unknown and/or red")]
    ]
    sysexitlist = [2, 2, 1, 1, 2, 2]

    # generate test cases
    tests = [TestCase(args).with_logs(logs).with_sys_exit(sysexit)
             for (args, logs, sysexit) in zip(argslist, logslist, sysexitlist)]

    # execute test cases with logging level set to INFO
    for test in tests:
        test.run_test(caplog, check_outputs=False)


def test_speed_command_line_default(compare):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    lst_file_path = f"{RastertoolsTestsData.tests_input_data_dir}/listing.lst"
    generate_lst_file(["SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip",
                       "SENTINEL2B_20181023-105107-455_L2A_T30TYP_D.zip"],
                      lst_file_path)

    # list of commands to test
    argslist = [
        # default with a listing of S2A products
        f"-v sp -b 1 -o {RastertoolsTestsData.tests_output_data_dir} {lst_file_path}",
        # default with a list of files
        f"--verbose speed --output {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"
        f" {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi.tif"
    ]
    speed_filenames = [
        ["SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-speed-20180928-105515.tif"],
        ["SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi-speed-20180928-105515.tif"]
    ]

    # generate test cases
    tests = [TestCase(args).output(f)
             for args, f in zip(argslist, speed_filenames)]

    # execute test cases with logging level set to INFO
    for test in tests:
        test.run_test()
    os.remove(lst_file_path)


def test_speed_command_line_errors(caplog):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    lst_file_path = f"{RastertoolsTestsData.tests_input_data_dir}/listing2.lst"
    generate_lst_file(["SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif",
                       "SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi.tif"],
                      lst_file_path)

    # list of commands to test
    argslist = [
        # output dir does not exist
        f"-v sp -o ./toto {lst_file_path}",
        # missing one file for speed
        f"-v sp -o {RastertoolsTestsData.tests_output_data_dir} {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip",
        # different types for input files
        f"-v sp -a -o {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip"
        f" {RastertoolsTestsData.tests_input_data_dir}/S2A_MSIL2A_20190116T105401_N0211_R051_T30TYP_20190116T120806.zip"
    ]
    # expected logs
    logslist = [
        [("eolab.georastertools.georastertools", logging.ERROR,
          "Output directory \"./toto\" does not exist.")],
        [("eolab.georastertools.cli.utils_cli", logging.ERROR,
          "Can not compute speed with 1 input image. Provide at least 2 images.")],
        [("eolab.georastertools.cli.utils_cli", logging.ERROR,
          "Speed can only be computed with images of the same type")]
    ]
    sysexitlist = [2, 1, 1]

    # generate test cases
    tests = [TestCase(args).with_logs(logs).with_sys_exit(sys_exit)
             for args, logs, sys_exit in zip(argslist, logslist, sysexitlist)]

    # execute test cases with logging level set to INFO
    for test in tests:
        test.run_test(caplog, check_outputs=False)
    os.remove(lst_file_path)


def test_timeseries_command_line_default(compare, save_gen_as_ref):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # default with a list of files
        f"--verbose ts --output {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"
        f" {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi.tif"
        " -s 2018-09-26 -e 2018-11-07 -p 20 -ws 512"
    ]
    timeseries_filenames = [
        ["SENTINEL2A_20180926-000000-685_L2A_T30TYP_D-ndvi-timeseries.tif",
         "SENTINEL2A_20181016-000000-685_L2A_T30TYP_D-ndvi-timeseries.tif",
         "SENTINEL2A_20181105-000000-685_L2A_T30TYP_D-ndvi-timeseries.tif"]
    ]
    refdir = utils4test.get_refdir("test_timeseries/")

    # generate test cases
    tests = [TestCase(args).output(f)
             for args, f in zip(argslist, timeseries_filenames)]

    # execute test cases with logging level set to INFO
    for test in tests:
        test.with_refdir(refdir)
        test.run_test(compare=compare, save_gen_as_ref=save_gen_as_ref)


def test_timeseries_command_line_errors(caplog):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    lst_file_path = f"{RastertoolsTestsData.tests_input_data_dir}/listing2.lst"
    generate_lst_file(["SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif",
                       "SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi.tif"],
                      lst_file_path)

    period = " -s 2018-09-26 -e 2018-11-07 -p 20"
    # list of commands to test
    argslist = [
        # output dir does not exist
        f"-v ts -o ./toto {lst_file_path}" + period,
        # missing one file for timeseries
        f"-v ts -o {RastertoolsTestsData.tests_output_data_dir} {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif" + period,
        # unknown raster type
        f"-v ts -o {RastertoolsTestsData.tests_output_data_dir} -a"
        f" {RastertoolsTestsData.tests_input_data_dir}/DSM_PHR_Dunkerque.tif"
        f" {RastertoolsTestsData.tests_input_data_dir}/S2A_MSIL2A_20190116T105401_N0211_R051_T30TYP_20190116T120806.zip" + period,
        # different types for input files
        f"-v ts -o {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip"
        f" {RastertoolsTestsData.tests_input_data_dir}/S2A_MSIL2A_20190116T105401_N0211_R051_T30TYP_20190116T120806.zip" + period,
        # invalid date format
        f"-v ts -o {RastertoolsTestsData.tests_output_data_dir} {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"
        f" {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi.tif"
        " -s 20180926 -e 2018-11-07 -p 20",
        # invalid date format
        f"-v ts -o {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"
        f" {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi.tif"
        " -s 2018-09-26 -e 20181107 -p 20"
    ]
    # expected logs
    logslist = [
        [("eolab.georastertools.georastertools", logging.ERROR,
          "Output directory \"./toto\" does not exist.")],
        [("eolab.georastertools.cli.utils_cli", logging.ERROR,
          "Can not compute a timeseries with 1 input image. Provide at least 2 images.")],
        [("eolab.georastertools.cli.utils_cli", logging.ERROR,
          f"Unknown rastertype for input file {RastertoolsTestsData.tests_input_data_dir}/DSM_PHR_Dunkerque.tif")],
        [("eolab.georastertools.cli.utils_cli", logging.ERROR,
          "Timeseries can only be computed with images of the same type")],
        [("eolab.georastertools.georastertools", logging.ERROR,
          "Invalid format for start date: 20180926 (must be %Y-%m-%d)")],
        [("eolab.georastertools.georastertools", logging.ERROR,
          "Invalid format for end date: 20181107 (must be %Y-%m-%d)")]
    ]
    sysexitlist = [2, 1, 1, 1, 2, 2]

    # generate test cases
    tests = [TestCase(args).with_logs(logs).with_sys_exit(sys_exit)
             for args, logs, sys_exit in zip(argslist, logslist, sysexitlist)]

    # execute test cases with logging level set to INFO
    for test in tests:
        test.run_test(caplog, check_outputs=False)
    os.remove(lst_file_path)


def test_zonalstats_command_line_default():
    # create output dir and clear its content if any
    utils4test.create_outdir()

    lst_file_path = f"{RastertoolsTestsData.tests_input_data_dir}/listing2.lst"
    generate_lst_file(["SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif",
                       "SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi.tif"],
                      lst_file_path)

    # list of commands to test
    argslist = [
        # specify stats to compute and sigma, 1st band computed
        f"-v zs -o {RastertoolsTestsData.tests_output_data_dir} -f GeoJSON"
        f" -g {RastertoolsTestsData.tests_input_data_dir}/COMMUNE_32xxx.geojson --stats min --stats max --sigma 1.0"
        f" {lst_file_path}",
        # default stats, all bands computed
        f"-v zs -o {RastertoolsTestsData.tests_output_data_dir} -f GeoJSON"
        f" --all -g {RastertoolsTestsData.tests_input_data_dir}/COMMUNE_32xxx.geojson"
        f" {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"
        f" {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi.tif"
    ]
    files = ["SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi",
             "SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi"]
    outliers = [True, False]

    # generate test cases
    tests = [TestCase(args).zs_output(files, outlier)
             for (args, outlier) in zip(argslist, outliers)]

    # execute test cases
    for test in tests:
        test.run_test()
    os.remove(lst_file_path)

def test_zonalstats_command_line_product():
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # input file is a S2A product
        f"-v zs -o {RastertoolsTestsData.tests_output_data_dir} -f GeoJSON"
        f" --all -g {RastertoolsTestsData.tests_input_data_dir}/COMMUNE_32xxx.geojson"
        f" {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip"
    ]
    files = ["SENTINEL2A_20180928-105515-685_L2A_T30TYP_D"]

    # generate test cases
    tests = [TestCase(args).zs_output(files) for args in argslist]

    # execute test cases
    for test in tests:
        test.run_test()


def test_zonalstats_command_line_categorical():
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # input file is a S2A product
        f"-v zs -o {RastertoolsTestsData.tests_output_data_dir} -f GeoJSON --categorical"
        f" {RastertoolsTestsData.tests_input_data_dir}/OCS_2017_CESBIO_extract.tif"
    ]
    files = ["OCS_2017_CESBIO_extract"]

    # generate test cases
    tests = [TestCase(args).zs_output(files) for args in argslist]

    # execute test cases
    for test in tests:
        test.run_test()


def test_zonalstats_command_line_errors():
    # create output dir and clear its content if any
    utils4test.create_outdir()

    lst_file_path = f"{RastertoolsTestsData.tests_input_data_dir}/listing2.lst"
    generate_lst_file(["SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif",
                       "SENTINEL2B_20181023-105107-455_L2A_T30TYP_D-ndvi.tif"],
                      lst_file_path)

    # list of commands to test
    argslist = [
        # output dir does not exist
        f"-v zs {lst_file_path} -o ./toto -f GeoJSON"
        f" -g {RastertoolsTestsData.tests_input_data_dir}/COMMUNE_32xxx.geojson --stats mean"
        " -b 0",
        # band 0 does not exist
        f"-v zs {lst_file_path} -o {RastertoolsTestsData.tests_output_data_dir} -f GeoJSON"
        f" -g {RastertoolsTestsData.tests_input_data_dir}/COMMUNE_32xxx.geojson --stats mean"
        " -b 0",
        # invalid format
        f"-v zs -o {RastertoolsTestsData.tests_output_data_dir} -f Truc {lst_file_path}",
        # invalid geometry index name
        f"-v zs -o {RastertoolsTestsData.tests_output_data_dir} -f GeoJSON --stats mean"
        f" -g {RastertoolsTestsData.tests_input_data_dir}/COMMUNE_32xxx.geojson -gi truc"
        f" -c {RastertoolsTestsData.tests_output_data_dir}/chart.png"
        f" {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip",
        # invalid prefix length
        f"-v zs -o {RastertoolsTestsData.tests_output_data_dir} -f GeoJSON --prefix band1"
        f" --all -g {RastertoolsTestsData.tests_input_data_dir}/COMMUNE_32xxx.geojson"
        f" {RastertoolsTestsData.tests_input_data_dir}/SENTINEL2A_20180928-105515-685_L2A_T30TYP_D.zip"
    ]

    logslist = [
        [("eolab.georastertools.main", logging.ERROR,
          "Output directory \"./toto\" does not exist.")],
        [("eolab.georastertools.main", logging.ERROR,
          "Invalid bands, all values are not in range [1, 1]")],
        [("eolab.georastertools.main", logging.ERROR,
          "Unrecognized output format Truc. Possible values are ")],
        [("eolab.georastertools.main", logging.ERROR,
          "Index 'truc' is not present in the geometries."
          " Please provide a valid value for -gi option.")],
        [("eolab.georastertools.main", logging.ERROR,
          "Number of prefix does not equal the number of bands.")],
    ]

    sysexitlist = [2, 1, 2, 1, 1]

    # generate test cases
    tests = [TestCase(args).with_logs(logs).with_sys_exit(sysexit)
             for (args, logs, sysexit) in zip(argslist, logslist, sysexitlist)]

    # execute test cases
    for test in tests:
        test.run_test(check_outputs=False)
    os.remove(lst_file_path)


def test_tiling_command_line_default():
    # create output dir and clear its content if any
    utils4test.create_outdir()

    lst_file_path = f"{RastertoolsTestsData.tests_input_data_dir}/listing3.lst"
    generate_lst_file(["tif_file.tif"],
                      lst_file_path)

    # list of commands to test
    argslist = [
        # default case with listing of input files
        f"-v ti -o {RastertoolsTestsData.tests_output_data_dir} -g {RastertoolsTestsData.tests_input_data_dir}/grid.geojson {lst_file_path}",
        # default case with input file
        f"--verbose ti -o {RastertoolsTestsData.tests_output_data_dir} -g {RastertoolsTestsData.tests_input_data_dir}/grid.geojson"
        f" {RastertoolsTestsData.tests_input_data_dir}/tif_file.tif",
        # specify specific ids
        f"-v ti -o {RastertoolsTestsData.tests_output_data_dir} -g {RastertoolsTestsData.tests_input_data_dir}/grid.geojson --id 77 --id 93 --id_col id"
        f" {RastertoolsTestsData.tests_input_data_dir}/tif_file.tif"
    ]
    input_filenames = [f"{RastertoolsTestsData.tests_input_data_dir}/tif_file.tif"]

    # generate test cases
    tests = [TestCase(args).ti_output(input_filenames, [77, 93]) for args in argslist]

    # execute test cases
    for test in tests:
        test.run_test(check_outputs=False)

    # Additional tests to check naming and subdir options
    # specify naming convention
    args = (f"-v ti -o {RastertoolsTestsData.tests_output_data_dir} -g {RastertoolsTestsData.tests_input_data_dir}/grid.geojson -n tile{{}}"
            f" --id_col id {RastertoolsTestsData.tests_input_data_dir}/tif_file.tif")
    test = TestCase(args).ti_output(input_filenames, [77, 93], name="tile{}")
    test.run_test(check_outputs=False)

    # specify subdir naming convetion
    args = (f"-v ti -o {RastertoolsTestsData.tests_output_data_dir} -g {RastertoolsTestsData.tests_input_data_dir}/grid.geojson -d tile{{}}"
            f" --id_col id {RastertoolsTestsData.tests_input_data_dir}/tif_file.tif")
    test = TestCase(args).ti_output(input_filenames, [77, 93], subdir="tile{}")
    # create one subdir to check if it is not re-created
    subdir = Path(f"{RastertoolsTestsData.tests_output_data_dir}/tile77")
    subdir.mkdir()
    test.run_test(check_outputs=False)
    os.remove(lst_file_path)


def test_tiling_command_line_special_case(caplog):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # some invalid ids
        f"-v ti -o {RastertoolsTestsData.tests_output_data_dir} -g {RastertoolsTestsData.tests_input_data_dir}/grid.geojson --id 1 --id 2 --id 93 --id_col id"
        f" {RastertoolsTestsData.tests_input_data_dir}/tif_file.tif",
        # a geometry does not overlap raster
        f"-v ti -o {RastertoolsTestsData.tests_output_data_dir} -g {RastertoolsTestsData.tests_input_data_dir}/grid.geojson --id 78 --id 93 --id_col id"
        f" {RastertoolsTestsData.tests_input_data_dir}/tif_file.tif"
    ]

    # expected logs
    logslist = [
        [("eolab.georastertools.tiling", logging.ERROR,
          "The grid column \"id\" does not contain the following values: [1, 2]")],
        [("eolab.georastertools.tiling", logging.ERROR,
          "Input shape 78 does not overlap raster")]
    ]

    # generate test cases
    tests = [TestCase(args).with_logs(logs) for (args, logs) in zip(argslist, logslist)]

    # execute test cases
    for test in tests:
        test.run_test(caplog, check_outputs=False)


def test_tiling_command_line_errors(caplog):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # ids without id_col
        f"-v ti --id 77 93 -o {RastertoolsTestsData.tests_output_data_dir} -g {RastertoolsTestsData.tests_input_data_dir}/grid.geojson"
        f" {RastertoolsTestsData.tests_input_data_dir}/tif_file.tif",
        # invalid id column
        f"-v ti -o {RastertoolsTestsData.tests_output_data_dir} -g {RastertoolsTestsData.tests_input_data_dir}/grid.geojson --id 77 --id 93 --id_col truc"
        f" {RastertoolsTestsData.tests_input_data_dir}/tif_file.tif",
        # output dir does not exist
        f"-v ti -o tests/truc -g {RastertoolsTestsData.tests_input_data_dir}/grid.geojson {RastertoolsTestsData.tests_input_data_dir}/tif_file.tif",
        # all invalid ids
        f"-v ti -o {RastertoolsTestsData.tests_output_data_dir} -g {RastertoolsTestsData.tests_input_data_dir}/grid.geojson --id 1 --id 2 --id_col id"
        f" {RastertoolsTestsData.tests_input_data_dir}/tif_file.tif"
    ]

    # expected logs
    logslist = [
        [("eolab.georastertools.georastertools", logging.ERROR,
          "Ids cannot be specified when id_col is not defined")],
        [("eolab.georastertools.georastertools", logging.ERROR,
          "Invalid id column named \"truc\": it does not exist in the grid")],
        [("eolab.georastertools.georastertools", logging.ERROR,
          "Output directory \"tests/truc\" does not exist.")],
        [("eolab.georastertools.georastertools", logging.ERROR,
          "No value in the grid column \"id\" are matching the given list of ids [1, 2]")]
    ]
    sysexitlist = [2, 2, 2, 2]

    # generate test cases
    tests = [TestCase(args).with_logs(logs).with_sys_exit(sysexit)
             for (args, logs, sysexit) in zip(argslist, logslist, sysexitlist)]

    # execute test cases
    for test in tests:
        test.run_test(caplog, check_outputs=False)


def test_filtering_command_line_default():
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # default case: median
        f"-v --max_workers 1 fi median -a --kernel_size 8 -o {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/RGB_TIF_20170105_013442_test.tif",
        # default case: local sum
        f"-v fi sum -b 1 -b 2 --kernel_size 8 -o {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/RGB_TIF_20170105_013442_test.tif",
        # default case: local mean
        f"-v fi mean -b 1 --kernel_size 8 -o {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/RGB_TIF_20170105_013442_test.tif",
        # default case: adaptive gaussian
        f"-v fi adaptive_gaussian -b 1 --kernel_size 32 --sigma 1 -o {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/RGB_TIF_20170105_013442_test.tif",
    ]
    input_filenames = ["RGB_TIF_20170105_013442_test-{}.tif"]
    names = ["median", "sum", "mean", "adaptive_gaussian"]

    # generate test cases
    tests = [TestCase(args).fi_output(input_filenames, name)
             for args, name in zip(argslist, names)]

    # execute test cases
    for test in tests:
        test.run_test(check_outputs=False)


def test_filtering_command_line_errors(caplog):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # output dir does not exist
        "-v filter median --kernel_size 8 -o tests/truc"
        f" {RastertoolsTestsData.tests_input_data_dir}/tif_file.tif",
        # missing required argument
        f"-v filter adaptive_gaussian --kernel_size 32 -o {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/RGB_TIF_20170105_013442_test.tif",
        # # kernel_size > window_size
        f"-v filter median -a --kernel_size 15 --window_size 16 -o {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/RGB_TIF_20170105_013442_test.tif",
    ]

    # expected logs
    logslist = [
        [("eolab.georastertools.georastertools", logging.ERROR,
          "Output directory \"tests/truc\" does not exist.")],
        [],
        [("eolab.georastertools.cli.utils_cli", logging.ERROR,
          "The kernel size (option --kernel_size, value=15) must be strictly less than the "
          "window size minus 1 (option --window_size, value=16)")]
    ]
    sysexitlist = [2, 2, 1]

    # generate test cases
    tests = [TestCase(args).with_logs(logs).with_sys_exit(sysexit)
             for (args, logs, sysexit) in zip(argslist, logslist, sysexitlist)]

    # execute test cases
    for test in tests:
        test.run_test(caplog, check_outputs=False)


def test_svf_command_line_default():
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # default case: svf at the point height
        f"-v svf --radius 50 --directions 16 --resolution 0.5 -o {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/toulouse-mnh.tif",
        # default case: svf on ground
        f"-v svf --radius 50 --directions 16 --resolution 0.5 --altitude 0 -o {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/toulouse-mnh.tif",
    ]
    output_filenames = ["toulouse-mnh-svf.tif"]

    # generate test cases
    tests = [TestCase(args).output(output_filenames)
             for args in argslist]

    # execute test cases
    for test in tests:
        test.run_test(check_outputs=False)


def test_svf_process_files(compare, save_gen_as_ref):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # default case: svf at the point height
        f"-v svf --radius 50 --directions 16 --resolution 0.5 -o {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/toulouse-mnh.tif",
    ]
    output_filenames = ["toulouse-mnh-svf.tif"]

    refdir = utils4test.get_refdir("test_svf/")

    # generate test cases
    tests = [TestCase(args).output(output_filenames)
             for args in argslist]

    # execute test cases
    for test in tests:
        test.with_refdir(refdir)
        test.run_test(compare=compare, save_gen_as_ref=save_gen_as_ref)


def test_svf_command_line_errors(caplog):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # output dir does not exist
        "-v svf --radius 50 --directions 16 --resolution 0.5 -o tests/truc"
        f" {RastertoolsTestsData.tests_input_data_dir}/toulouse-mnh.tif",
        # missing required argument
        f"-v svf --directions 16 --resolution 0.5 -o {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/toulouse-mnh.tif",
        # radius > window_size / 2
        "-v svf --radius 100 --window_size 128 --directions 16 --resolution 0.5"
        f" --altitude 0 -o {RastertoolsTestsData.tests_output_data_dir} {RastertoolsTestsData.tests_input_data_dir}/toulouse-mnh.tif",
    ]

    # expected logs
    logslist = [
        [("eolab.georastertools.georastertools", logging.ERROR,
          "Output directory \"tests/truc\" does not exist.")],
        [],
        [("eolab.georastertools.cli.utils_cli", logging.ERROR,
          "The radius (option --radius, value=100) must be strictly less than half the"
          " size of the window (option --window_size, value=128)")]
    ]
    sysexitlist = [2, 2, 1]

    # generate test cases
    tests = [TestCase(args).with_logs(logs).with_sys_exit(sysexit)
             for (args, logs, sysexit) in zip(argslist, logslist, sysexitlist)]

    # execute test cases
    for test in tests:
        test.run_test(caplog, check_outputs=False)


def test_hillshade_command_line_default():
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    # elevation / azimuth are retrieved from https://www.sunearthtools.com/dp/tools/pos_sun.php
    argslist = [
        # default case: hillshade at Toulouse the September, 21 solar noon
        f"-v hs --elevation 27.2 --azimuth 82.64 --resolution 0.5 -o {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/toulouse-mnh.tif",
        # default case: hillshade at Toulouse the June, 21, solar 6PM
        f"-v hs --elevation 25.82 --azimuth 278.58 --resolution 0.5 -o {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/toulouse-mnh.tif",
        # default case: hillshade at Toulouse the June, 21, solar noon
        f"-v hs --elevation 69.83 --azimuth 180 --resolution 0.5 -o {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/toulouse-mnh.tif",
        # default case: hillshade at Toulouse the June, 21, solar 8AM
        f"-v hs --elevation 27.2 --azimuth 82.64 --resolution 0.5 -o {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/toulouse-mnh.tif",
    ]
    output_filenames = ["toulouse-mnh-hillshade.tif"]

    # generate test cases
    tests = [TestCase(args).output(output_filenames)
             for args in argslist]

    # execute test cases
    for test in tests:
        test.run_test(check_outputs=False)

def test_hillshade_process_files(compare, save_gen_as_ref):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    # elevation / azimuth are retrieved from https://www.sunearthtools.com/dp/tools/pos_sun.php
    argslist = [
        # default case: hillshade at Toulouse the September, 21 solar noon
        f"-v hs --elevation 27.2 --azimuth 82.64 --resolution 0.5 -o {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/toulouse-mnh.tif"
    ]
    output_filenames = ["toulouse-mnh-hillshade.tif"]

    refdir = utils4test.get_refdir("test_hillshade/")

    # generate test cases
    tests = [TestCase(args).output(output_filenames)
             for args in argslist]

    # execute test cases
    for test in tests:
        test.with_refdir(refdir)
        test.run_test(compare=compare, save_gen_as_ref=save_gen_as_ref)


def test_hillshade_command_line_errors(caplog):
    # create output dir and clear its content if any
    utils4test.create_outdir()

    # list of commands to test
    argslist = [
        # output dir does not exist
        "-v hs --elevation 46.81 --azimuth 180.0 --resolution 0.5 -o tests/truc"
        f" {RastertoolsTestsData.tests_input_data_dir}/toulouse-mnh.tif",
        # missing required argument
        "-v hs --elevation 46.81 --resolution 0.5 "
        f" {RastertoolsTestsData.tests_input_data_dir}/toulouse-mnh.tif",
        # input file has more than 1 band
        f"-v hs --elevation 46.81 --azimuth 180.0 --resolution 0.5 -o {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/S2A_MSIL2A_20190116T105401_N0211_R051_T30TYP_20190116T120806.vrt",
        # radius > window_size / 2
        "-v hs --elevation 27.2 --azimuth 82.64 --resolution 0.5"
        f" --radius 100 --window_size 128 -o {RastertoolsTestsData.tests_output_data_dir}"
        f" {RastertoolsTestsData.tests_input_data_dir}/toulouse-mnh.tif",
    ]

    # expected logs
    logslist = [
        [("eolab.georastertools.georastertools", logging.ERROR,
          "Output directory \"tests/truc\" does not exist.")],
        [],
        [("eolab.georastertools.cli.utils_cli", logging.ERROR,
          "Invalid input file, it must contain a single band.")],
        [("eolab.georastertools.cli.utils_cli", logging.ERROR,
          "The radius (option --radius, value=100) must be strictly less than half"
          " the size of the window (option --window_size, value=128)")]
    ]
    sysexitlist = [2, 2, 1, 1]

    # generate test cases
    tests = [TestCase(args).with_logs(logs).with_sys_exit(sysexit)
             for (args, logs, sysexit) in zip(argslist, logslist, sysexitlist)]

    # execute test cases
    for test in tests:
        test.run_test(caplog, check_outputs=False)
