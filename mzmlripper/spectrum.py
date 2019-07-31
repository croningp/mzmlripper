"""Module for representing Spectrum data
Holds all raw information ripped from an mzML about the Spectrum
Raw information is then decoded and serialised into a dictionary

.. moduleauthor:: Graham Keenan (Cronin Group 2019)
.. signature:: dd383a145d9a2425c23afc00c04dc054951b13c76b6138c6373597b9bf55c007

"""

import zlib
import struct
import base64


class Spectrum(object):
    """Class for representing a Spectrum object from mzML

    Arguments:
        intensity_threshold {int} -- Threshold for cutting intensities below threshold
    """

    def __init__(self, intensity_threshold):
        self.array_length = ""
        self.ms_level = ""
        self.parent = ""
        self.retention_time = ""
        self.d_type = ""
        self.compression = ""
        self.mz = ""
        self.intensity = ""
        self.serialized = {}
        self.intensity_threshold = intensity_threshold


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

        self.mz = base64.b64decode(self.mz)
        self.intensity = base64.b64decode(self.intensity)

        if "zlib" in self.compression:
            self.mz = zlib.decompress(self.mz)
            self.intensity = zlib.decompress(self.intensity)

        self.mz = list(
            struct.unpack(
                f"<{self.array_length}{self.d_type}",
                self.mz
            )
        )

        self.intensity = list(
            struct.unpack(
                f"<{self.array_length}{self.d_type}",
                self.intensity
            )
        )


    def serialize(self) -> dict:
        """Converts the spectrum into a dictionary

        Only takes relevant information

        Returns:
            dict -- Spectrum data
        """

        out = {}
        mass_list = []

        for mz, intensity in zip(self.mz, self.intensity):
            if self.ms_level == "1":
                if intensity > self.intensity_threshold:
                    out[f"{mz:.4f}"] = int(intensity)
                    mass_list.append(mz)
            elif self.ms_level > "1":
                if intensity > (self.intensity_threshold/100) * 5:
                    out[f"{mz:.4f}"] = int(intensity)
                    mass_list.append(mz)

        out["retention_time"] = self.retention_time
        out["mass_list"] = [float(f"{mass:.4f}") for mass in mass_list]

        if self.parent:
            out["parent"] = f"{float(self.parent):.4f}"

        return out
