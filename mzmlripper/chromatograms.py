"""
Module for basic chromatograms
"""
from .spectrum import NON_MASS_KEYS


def generate_EIC(
    ms_data: dict,
    target_mass: float,
    error_tolerance: float = 10,
    error_units: float = "ppm",
    min_rt: float = 0,
    max_rt: float = None
) -> tuple:
    """
    Generate Extracted Ion Chromatograms (EIC) for target mass.

    Args:
        ms_data (dict): mzml ripper data in standard ripper format.
        target_mass (float): target m/z for EIC (units = Th).
        error_tolerance (float, optional): error threshold for matching target
            m/z to candidates. Can either be in absolute units (u) or relative
            (ppm) Defaults to 10 (ppm).
        error_units (float, optional): units for error tolerance. Must be either
            "ppm" for relative units or "u" for absolute mass units.
            Defaults to "ppm".
        min_rt (float, optional): specifies minimum retention time for EIC.
            Defaults to 0.
        max_rt (float, optional): specifies maximum retention time for EIC.
            Defaults to None.

    Raises:
        Exception: raised if error_units not in ["ppm", "u"].

    Yields:
        Tuple[float, float]: EIC data point in format:
            (retention time, intensity)
    """

    #  remove unneccessary MSn data
    if "ms1" in ms_data:
        ms_data = ms_data["ms1"]

    #  filter by retention time
    ms_data = [
        spec for spec in ms_data.values()
        if float(spec["retention_time"]) >= min_rt
    ]

    if max_rt:
        ms_data = [
            spec for spec in ms_data.values()
            if float(spec["retention_time"]) <= max_rt
        ]

    #  check and (if necessary) convert error_tolerance to absolute (Thomson)
    #  units
    if error_units == "ppm":
        error_tolerance = (target_mass / 1E6 * error_tolerance)
    elif error_units != "u":
        raise Exception(
            f"{error_units} not valid error units. Choose either 'u' or 'ppm'"
            " for absolute and relative error, respectively.")

    #  get final mass range for matching
    mass_range = (target_mass - error_tolerance, target_mass + error_tolerance)

    #  iterate through spectra, matching masses
    for spec in ms_data:
        matches = match_mass(candidates=spec["mass_list"], range=mass_range)
        if matches:

            intensity = sum(
                [float(spec[format(match, ".4f")]) for match in matches]
            )
            yield (float(spec["retention_time"]), intensity)


def generate_chromatogram(
    ms_data: dict,
    chromatogram: str,
    ms_level: int = 1
) -> list:
    """
    Generates a either a Base Peak Chromatogram (BPC) or Total Ion Chromatogram
    (TIC) from ripper data.

    Args:
        ms_data (dict): mzml ripper data in standard ripper format.
        chromatogram (str): specifies type of chromatogram. Must be either "tic"
            or "bpc" for Total Ion Chromatogram or Base Peak Chromatogram,
            respectively.
        ms_level (int, optional): specifies ms level for BPC. Defaults to 1.

    Raises:
        Exception: raised if chromatogram.lower() is not in ["tic", "bpc"]

    Returns:
        BPC (List[Tuple[float, float, float]]): list of base peaks in format:
            [(retention time, m/z, intensity), ...]
        TIC (List[Tuple[float, float]]): list of total ion currents in format:
            [(retention_time, total_intensity), ...]
    """
    if f"ms{ms_level}" not in ms_data:
        return []

    ms_data = ms_data[f"ms{ms_level}"]

    if chromatogram.lower() == "bpc":
        return [
            find_max_peak(spectrum=spectrum) for spectrum in ms_data.values()
        ]
    elif chromatogram.lower() == "tic":
        return [
            sum_intensity_peaks(spectrum) for spectrum in ms_data.values()
        ]
    else:
        raise Exception(
            f"{chromatogram} not valid chromatogram type. Please choose "
            "'tic' or 'bpc' for Total Ion Chromatogram or Base Peak "
            "Chromatogram, repspectively"
        )


def match_mass(candidates: list, range: tuple) -> list:
    """
    Matches candidate m/z values to tolerance range.

    Args:
        candidates (List[float]): list of candidate m/z values.
        range (Tuple[float, float]): tolerance range for m/z matches in format:
            (minimum m/z, maximum m/z).

    Returns:
        List[float]: list of candidate m/z values that match error tolerance.
    """
    return [
        float(mass) for mass in candidates
        if float(mass) >= range[0] and float(mass) <= range[1]]


def find_max_peak(spectrum: dict) -> tuple:
    """
    Finds most intense peak in spectrum.

    Args:
        spectrum (dict): single ripper spectrum.

    Returns:
        Tuple[float, float, float]: most intense peak in format:
            (retention time, m/z, intensity)
    """
    peaks = sorted(
        [(float(mass), float(intensity)) for mass, intensity in spectrum.items()
            if mass not in NON_MASS_KEYS], key=lambda x: x[1]
    )
    return (float(spectrum["retention_time"]), ) + peaks[-1]


def sum_intensity_peaks(spectrum: dict) -> tuple:
    """
    Takes a standard ripper spectrum and sums intensity of peaks. Returns tuple
    of retention time and total intensity.

    Args:
        spectrum (dict): standard ripper spectrum dict.

    Returns:
        Tuple[float, float]: (retention time, intensity)
    """
    intensity = sum(
        [
            float(spectrum[mass]) for mass in spectrum
            if mass not in NON_MASS_KEYS
        ]
    )

    return (float(spectrum["retention_time"]), intensity)
