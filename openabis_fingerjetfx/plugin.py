import os
import subprocess
from io import BytesIO

from .fmr import FingerprintMinutiaeRecord
from PIL import Image

TEMPLATE_FORMAT_ISO19794 = "iso19794"


class FingerjetExtractor:
    """
    Fingerprint extractor configuration

    :param config: App environment configuration
    """

    def __init__(self, config):
        self.name = "fingerjet"
        self.version = "x"
        self.max_minutiae = config.get("FINGERJET_MAX_MINUTIAE", 0)
        self.image_dpi = config.get("DEFAULT_FINGERPRINT_DPI", 0)

        self.fingerjet_binary = os.path.join(os.path.dirname(os.path.realpath(__file__)), "extract")
        env = os.environ.copy()
        env["LD_LIBRARY_PATH"] = os.path.dirname(__file__) + ":" + os.getenv("LD_LIBRARY_PATH", "")
        self.subprocess_env = env

    def extract(self, fingerprint):
        """
        Extract fingerprint image buffer to ISO19794 buffer

        :param fingerprint: Base64 image buffer
        :return: ISO 19794 fingerprint template
        """
        # image = fingerprint.image

        fin = BytesIO()
        fin.write(fingerprint.image)
        img = Image.open(fin)
        img_out = img.convert("L")
        width, height = img_out.size

        fout = BytesIO()
        img_out.save(fout, "PPM")
        fout.seek(0)
        img_bin = fout.read()

        dpi = self.image_dpi
        if "dpi" in img.info and img.info["dpi"] is not None:
            dpi_x, dpi_y = img.info["dpi"]
            if dpi_x != dpi_y:
                raise Exception("DPI X and Y should be the same")
            dpi = dpi_x

        if fingerprint.imageDpi:
            dpi = fingerprint.imageDpi

        if dpi <= 0:
            raise Exception("Could not determine image's DPI")

        result = subprocess.Popen(
            [self.fingerjet_binary, str(width * height), str(dpi)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            env=self.subprocess_env,
        )
        # result.stdin.write(open("test.pgm", "rb").read())
        result.stdin.write(img_bin)
        output, status = result.communicate()

        if self.max_minutiae > 0:
            fin = BytesIO(output)
            fin.seek(0)
            fmr = FingerprintMinutiaeRecord()
            fmr.read(fin)
            for finger in fmr.fingers:
                finger.shrink_minutiae(self.max_minutiae)

            fout = BytesIO()
            fmr.write(fout)
            fout.seek(0)
        else:
            fout = BytesIO(output)

        biometricTemplate = fingerprint.templates.add()
        # biometricTemplate.template = output
        biometricTemplate.template = fout.read()
        biometricTemplate.extractor = self.name
        biometricTemplate.extractorVersion = "1"
        biometricTemplate.format = TEMPLATE_FORMAT_ISO19794

        return biometricTemplate

    def to_grayscale(self, image):
        """
        Convert image to 8-bit grayscale buffer
        Receive image and then convert it to grayscale image
        to be used as input for extraction process. Most of the extraction
        algorithm works only with grayscale.

        :param image: byte array
        :return:
            width: width of the input image
            height: height of the input image
            image buffer: buffer of output 8-bit grayscale image
        """
        fin = BytesIO()
        fin.write(image)
        img = Image.open(fin)
        img_out = img.convert("L")
        width, height = img_out.size
        fout = BytesIO()
        img_out.save(fout, "PPM")
        fout.seek(0)
        return width, height, fout.read()
