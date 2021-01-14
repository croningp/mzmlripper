import os
import json
import pytest

from functools import partial

import mzmlripper.chromatograms as chrom

#  data folder containing raw data and chromatograms
DATA_FOLDER = os.path.join(
    os.path.dirname(__file__),
    "..",
    "test_data"
)

#  list of target m/z values for EICs
TARGET_MASSES = [154.0051, 217.1046, 309.9474]

#  list of absolute error values (u) for setting error tolerance
ABSOLUTE_ERRORS = [1, 0.1, 0.05, 0.01, 0.005]

# list of relative error values (ppm) for setting error tolerance
REL_ERRORS = [50, 25, 10, 5, 1]


@pytest.fixture
def raw_data() -> dict:
    """
    Raw orbitrap ripper data from an LC-MS run. Maximum retention time = 10 min
    This data was used to generate all EICs, BPCs and TICs in test suite.
    Contains MS1 and MS2 data.

    Returns:
        dict: ripper data dict in standard ripper format
    """

    #  load raw data from data folder
    data_path = os.path.join(
        DATA_FOLDER,
        "converted_test_data_orbi_maxrt10min.json"
    )
    with open(data_path, "r") as r:
        return json.load(r)


@pytest.fixture
def legacy_bpcs() -> dict:
    """
    Base Peak Chromatograms (BPCs) generated from raw test data. BPCs at MS1
    and MS2.

    Returns:
        dict: dict of BPC by level in format {1: MS1 BPC, 2: MS2 BPC}
    """
    bpcs = {}
    for ms_level in [1, 2]:
        with open(
            os.path.join(
                DATA_FOLDER,
                f"ms{ms_level}bpc.json"
            ),
            "r"
        ) as r:
            bpcs[ms_level] = json.load(r)

    return bpcs


@pytest.mark.unit
def test_bpcs(raw_data: dict, legacy_bpcs: dict):
    """
    Test to make sure the output of chromatogram.generate_bpc does not differ
    from legacy data.

    Args:
        raw_data (dict): ripper data dict in standard ripper format
        legacy_bpcs (dict): dict of legacy BPCs by level in format
            {1: MS1 BPC, 2: MS2 BPC}
    """

    bpc = partial(
        chrom.generate_chromatogram,
        ms_data=raw_data,
        chromatogram="bpc"
    )

    #  generate BPCs for MS1 and MS2 data
    ms1_bpc = bpc(ms_level=1)
    ms2_bpc = bpc(ms_level=2)

    #  go through MS1 and MS2 BPCs and make sure they are identical to
    #  BPCs generated previously from same data
    for i, bpc in enumerate([ms1_bpc, ms2_bpc]):
        assert [list(data) for data in bpc] == legacy_bpcs[i + 1]


@pytest.mark.unit
def test_eic_relative(raw_data: dict):
    """
    Test for generating EICs using relative error units ("ppm").

    Args:
        raw_data (dict): ripper data dict in standard ripper format
    """

    #  navigate to relative data directory containing EICs generated using
    #  relative values for error tolerance
    relative_data_dir = os.path.join(DATA_FOLDER, "relative_eics")

    #  iterate through EIC target masses, check the EIC function is working
    #  correctly for each target at all relative error values
    for target_mass in TARGET_MASSES:

        for rel_error in REL_ERRORS:

            rel_eic = chrom.generate_EIC(
                ms_data=raw_data,
                target_mass=target_mass,
                error_tolerance=rel_error,
                error_units="ppm"
            )
            raw_file = os.path.join(
                relative_data_dir,
                f"target={target_mass}mz_{rel_error}ppm_error.json"
            )

            with open(raw_file, "r") as r:
                legacy_eic = json.load(r)

            assert [list(peak) for peak in rel_eic] == legacy_eic


@pytest.mark.unit
def test_eic_absolute(raw_data):
    """
    Test for generating EIC using absolute error units ("u").

    Args:
        raw_data (dict): ripper data dict in standard ripper format
    """

    #  navigate to relative data directory containing EICs generated using
    #  absolute values for error tolerance
    abs_data_dir = os.path.join(DATA_FOLDER, "absolute_eics")

    #  iterate through EIC target masses, check the EIC function is working
    #  correctly for each target at all absolute error values
    for target_mass in TARGET_MASSES:

        for abs_error in ABSOLUTE_ERRORS:

            abs_eic = chrom.generate_EIC(
                ms_data=raw_data,
                target_mass=target_mass,
                error_tolerance=abs_error,
                error_units="u"
            )

            raw_file = os.path.join(
                abs_data_dir,
                f"target={target_mass}mz_{abs_error}u_error.json"
            )

            with open(raw_file, "r") as r:
                legacy_eic = json.load(r)

            assert [list(peak) for peak in abs_eic] == legacy_eic
