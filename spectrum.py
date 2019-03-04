import struct
import zlib
import base64

INTENSITY_THRESH = 1000.0

class Spectrum(object):
    def __init__(self):
        self.array_length = ""
        self.ms_level = ""
        self.parent = ""
        self.retention_time = ""
        self.d_type = ""
        self.compression = ""
        self.mz = ""
        self.intensity = ""
        self.serialized = {}


    def _set_data_type(self):
        if "32" in self.d_type:
            self.d_type = "f"
        elif "64" in self.d_type:
            self.d_type = "d"


    def process(self):
        self._set_data_type()
        self.decode_and_decompress()
        self.serialized = self.serialize()


    def decode_and_decompress(self):
        self.mz = base64.b64decode(self.mz)
        self.intensity = base64.b64decode(self.intensity)

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
        out = {}
        mass_list = []
        for mz, intensity in zip(self.mz, self.intensity):
            if intensity > INTENSITY_THRESH:
                out[f"{mz:.4f}"] = int(intensity)
                mass_list.append(mz)

        out["retention_time"] = self.retention_time
        out["mass_list"] = [float(f"{mass:.4f}") for mass in mass_list]

        if self.parent:
            out["parent"] = self.parent

        return out
