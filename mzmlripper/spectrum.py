"""Module for representing Spectrum data
Holds all raw information ripped from an mzML about the Spectrum
Raw information is then decoded and serialised into a dictionary

.. moduleauthor:: Graham Keenan (Cronin Group 2019)
.. signature:: dd383a145d9a2425c23afc00c04dc054951b13c76b6138c6373597b9bf55c007

"""

# System imports
import zlib
import struct
import base64
from typing import Dict

#  list of spectrum keys that do not correspond to individual ions with specific
#  m/z and intensity values
NON_MASS_KEYS = ["mass_list", "retention_time", "parent", "scan", "parent_scan"]


class UnsupportedCompressionMethod(Exception):
    """Compression type is not yet supported
    """


class Spectrum(object):
    """Class for representing a Spectrum object from mzML

    Arguments:
        intensity_threshold (int): Threshold for cutting intensities below
        threshold
        relative (bool, optional): Specifies whether intensities of individual
            ions in spectra are displayed in relative (%) or absolute units.
    """

    def __init__(self, intensity_threshold, relative=False):
        self.scan = ""
        self.array_length = ""
        self.ms_level = ""
        self.parent_mass = ""
        self.parent_scan = ""
        self.retention_time = ""
        self.d_type = ""
        self.compression = ""
        self.mz = ""
        self.intensity = ""
        self.serialized = {}
        self.intensity_threshold = intensity_threshold
        self.relative = relative

    def _set_data_type(self):
        """Sets the data type of the binary data within
        """

        if "32" in self.d_type:
            self.d_type = "f"
        elif "64" in self.d_type:
            self.d_type = "d"

    def process(self):
        """Processes a Spectrum

        Decodes the m/z and intensity data from Base64
        Decompresses if required and converts to float array
        """

        self._set_data_type()
        self.decode_and_decompress()
        self.serialized = self.serialize()

    def decode_and_decompress(self):
        """Decodes binary data from Base64 and decompresses if necessary

        Converts the binary data to a list of floats
        """

        # Decode the MZ and intensity data
        self.mz = base64.b64decode(self.mz)
        self.intensity = base64.b64decode(self.intensity)

        # Using ZLib compression
        if "zlib" in self.compression:
            self.mz = self.decompress(self.mz)
            self.intensity = self.decompress(self.intensity)
        else:
            raise UnsupportedCompressionMethod(
                f"Compression method {self.compression} is not supported."
            )

        # Build the MZ array
        self.mz = list(
            struct.unpack(
                f"<{self.array_length}{self.d_type}",
                self.mz
            )
        )

        # Build the Intensity array
        self.intensity = list(
            struct.unpack(
                f"<{self.array_length}{self.d_type}",
                self.intensity
            )
        )

    def decompress(self, stream: bytes):
        """
        Decompresses a data stream using a zlib decompression object.
        Args:
            stream (bytes): data stream.

        Returns:
            bytes: decompressed data stream.
        """

        # Decompress the ZLib stream
        zobj = zlib.decompressobj()
        stream = zobj.decompress(stream)
        return stream + zobj.flush()

    def serialize(self) -> Dict:
        """Converts the spectrum into a dictionary

        Only takes relevant information

        Returns:
            Dict: Spectrum data
        """

        out = {}
        mass_list = []

        # Iterate through the MZ and intensity
        for mz, intensity in zip(self.mz, self.intensity):
            # Check the intensity threshold is met and add to output
            if self.ms_level == "1":
                if intensity > self.intensity_threshold:
                    out[f"{mz:.4f}"] = int(intensity)
                    mass_list.append(mz)

            # Check the intensity threshold is met and add to output for MS 2
            elif self.ms_level > "1":
                if intensity > (self.intensity_threshold / 100) * 5:
                    out[f"{mz:.4f}"] = int(intensity)
                    mass_list.append(mz)

        # Populate remaining data
        out["retention_time"] = self.retention_time

        out["scan"] = self.scan

        # Set the parent mass if applicable
        if self.parent_mass:
            out["parent"] = f"{float(self.parent_mass):.4f}"

        # Set parent scan if applicable
        if self.parent_scan:
            out["parent_scan"] = self.parent_scan

        # Create mass list
        out["mass_list"] = [float(f"{mass:.4f}") for mass in mass_list]

        #  if relative intensities are to be returned, convert spectrum dict
        if self.relative:
            out = self.convert_to_relative(out)

        return out

    def convert_to_relative(self, spectrum_dict: dict) -> Dict:
        """Converts a spectrum dict of absolute intensities to relative
        intensities.

        spectrum_dict (dict): standard spectrum dict with absolute intensities.
        Returns:
            Dict: Spectrum data
        """
        #  get list of ions ([[m/z, I], ...]) sorted by intensity
        all_ions = sorted([
            [float(mass), float(intensity)]
            for mass, intensity in spectrum_dict.items()
            if mass not in NON_MASS_KEYS], key=lambda x: x[1])

        #  get the base peak - most intense ion
        base_peak = all_ions[-1]

        #  make sure all NON_MASS_KEYS remain unchanged in spectrum_dict
        spectrum_dict = {
            key: value for key, value in spectrum_dict.items()
            if key in NON_MASS_KEYS
        }

        #  iterate through ions, readding to spectrum_dict with relative
        #  intensities
        for ion in all_ions:
            spectrum_dict[ion[0]] = round((ion[1] / base_peak[1]) * 100, 4)
        spectrum_dict["base_peak"] = base_peak

        return spectrum_dict
