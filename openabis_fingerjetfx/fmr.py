#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import struct
from operator import attrgetter


class Minutia(object):
    TypeOther = 0b00
    TypeTermination = 0b01
    TypeBifurcation = 0b10
    TypeUnknown = 0b11

    TYPE_LABELS = {
        TypeOther: "Other",
        TypeTermination: "Termination",
        TypeBifurcation: "Bifurcation",
        TypeUnknown: "Unknown",
    }

    type = None
    x = None
    y = None
    direction = None
    quality = None

    def __repr__(self):
        return "<Minutia (Type: {}, x: {}, y: {}, Direction: {}°, Quality: {})>".format(
            self.TYPE_LABELS[self.type],
            self.x,
            self.y,
            (self.direction * 360 + 128) / 256,
            self.quality or "Not Reported",
        )

    def __init__(self):
        self.type = None
        self.x = None
        self.y = None
        self.direction = None
        self.quality = None


class Finger(object):
    position = None
    view_number = None
    impression_number = None
    fp_quality = None
    minutiae_count = None

    minutiae = []

    def __repr__(self):
        return "<Finger (Position: {}, View #: {}, Impression #: {}, FP Quality: {}, Minutiae #: {})>".format(
            self.position, self.view_number, self.impression_number, self.fp_quality, self.minutiae_count
        )

    def __init__(self):
        self.position = None
        self.view_number = None
        self.impression_number = None
        self.fp_quality = None
        self.minutiae_count = None
        self.minutiae = []

    def add_minutia(self, minutia):
        self.minutiae.append(minutia)

    def sort_minutiae_by_quality(self):
        self.minutiae.sort(key=attrgetter("quality"), reverse=True)

    def shrink_minutiae(self, number_minutiae):
        if number_minutiae >= self.minutiae_count:
            return
        del self.minutiae[number_minutiae:]
        self.minutiae_count = len(self.minutiae)


class FingerprintMinutiaeRecord(object):
    version = None
    size = None
    dpi = None

    fingers = []

    def __repr__(self):
        return "<FingerprintMinutiaeRecord (Version: {}, Size: {}, DPI: {}, Num Fingers: {})>".format(
            self.version.strip(b" \x00"),
            self.size,
            (int(self.dpi[0] * 2.54), int(self.dpi[1] * 2.54)),
            len(self.fingers),
        )

    def __init__(self):
        self.version = None
        self.size = None
        self.dpi = None
        self.fingers = []

    def add_finger(self, finger):
        self.fingers.append(finger)

    def write(self, f):
        f.write(b"FMR\x00")
        f.write(b" 20\x00")
        f.write(struct.pack(">I", 0))  # Length will be updated later
        f.write(b"\x00\x00")
        f.write(struct.pack(">HH", self.size[0], self.size[1]))
        f.write(struct.pack(">HH", round(self.dpi[0]), round(self.dpi[1])))
        f.write(struct.pack("B", len(self.fingers)))
        f.write(b"\x00")

        for finger in self.fingers:
            f.write(struct.pack("B", finger.position))
            view_number_impression_number = (finger.view_number << 4) + finger.impression_number
            f.write(struct.pack("B", view_number_impression_number))
            f.write(struct.pack("B", finger.fp_quality))
            f.write(struct.pack("B", finger.minutiae_count))

            for minutia in finger.minutiae:
                minutia_type_and_x = (minutia.type << 14) + minutia.x
                f.write(struct.pack(">H", minutia_type_and_x))
                minutia_y = (0 << 14) + minutia.y
                f.write(struct.pack(">H", minutia_y))
                f.write(struct.pack("B", minutia.direction))
                f.write(struct.pack("B", minutia.quality))

            f.write(b"\x00\x00")

        # Update length
        length = f.tell()
        f.seek(8)
        f.write(struct.pack(">I", length))

    def read(self, f):
        magic = struct.unpack("4s", f.read(4))[0]
        if magic != b"FMR\x00":
            raise ValueError("Not an ISO FMR file.")

        self.version = struct.unpack("4s", f.read(4))[0]
        if self.version != b" 20\x00":
            raise ValueError("Unsupported file version. Must be 20.")

        struct.unpack(">I", f.read(4))[0]

        f.read(2)

        self.size = struct.unpack(">HH", f.read(4))
        self.dpi = struct.unpack(">HH", f.read(4))
        num_fingers = struct.unpack("B", f.read(1))[0]

        f.read(1)

        for finger in range(1, num_fingers + 1):
            finger = Finger()

            finger.position = struct.unpack("B", f.read(1))[0]
            view_number_impression_number = struct.unpack("B", f.read(1))[0]
            finger.view_number = view_number_impression_number >> 4
            finger.impression_number = view_number_impression_number & 0b00001111
            finger.fp_quality = struct.unpack("B", f.read(1))[0]
            finger.minutiae_count = struct.unpack("B", f.read(1))[0]

            for i in range(1, finger.minutiae_count + 1):
                minutia = Minutia()

                minutia_type_and_x = struct.unpack(">H", f.read(2))[0]
                minutia.type = minutia_type_and_x >> 14
                minutia.x = minutia_type_and_x & 0b0011111111111111

                minutia_y = struct.unpack(">H", f.read(2))[0]
                minutia.y = minutia_y & 0b0011111111111111

                minutia.direction = struct.unpack("B", f.read(1))[0]
                minutia.quality = struct.unpack("B", f.read(1))[0]

                finger.add_minutia(minutia)

            f.read(2)
            self.add_finger(finger)

    def generate_random(self, size=[300, 400], position=0):
        finger = Finger()

        finger.position = position
        finger.view_number = 0
        finger.impression_number = 0
        finger.fp_quality = random.randint(50, 100)
        finger.minutiae_count = random.randint(24, 36)

        for n in range(0, finger.minutiae_count):
            minutia = Minutia()
            minutia.type = random.choice([Minutia.TypeBifurcation, Minutia.TypeTermination, Minutia.TypeOther])
            minutia.x = random.randint(0, size[0] - 1)
            minutia.y = random.randint(0, size[1] - 1)
            minutia.direction = random.randint(0, 255)
            minutia.quality = random.randint(50, 100)
            finger.add_minutia(minutia)

        self.add_finger(finger)
        self.size = size
        self.dpi = [500 / 2.54, 500 / 2.54]
        self.version = "20"

    def annotate(self, image):
        import math
        from PIL import Image, ImageDraw

        im = Image.open(image)
        im = im.convert("RGB")
        draw = ImageDraw.Draw(im)

        for minutia in self.fingers[0].minutiae:
            color = (255, 0, 0, 255)
            if minutia.type == Minutia.TypeBifurcation:
                color = (0, 255, 0, 255)
                draw.rectangle([minutia.x - 3, minutia.y - 3, minutia.x + 3, minutia.y + 3], outline=color)
            else:
                draw.ellipse([minutia.x - 3, minutia.y - 3, minutia.x + 3, minutia.y + 3], outline=color)

            angle = minutia.direction
            x = math.cos(math.radians(angle)) * 10
            y = math.sin(math.radians(angle)) * 10
            draw.line([minutia.x, minutia.y, minutia.x + x, minutia.y - y], fill=color)
        im.show()


if __name__ == "__main__":
    # import argparse

    # parser = argparse.ArgumentParser()
    # parser.add_argument(
    #     "num_fingerprints", type=int, help="number of fingerprint templates to generate"
    # )
    # args = parser.parse_args()

    # for i in range(1, args.num_fingerprints + 1):
    #     fmr = FingerprintMinutiaeRecord()
    #     fmr.generate_random()

    #     output_dir = "templates"
    #     if not os.path.exists(output_dir):
    #         os.makedirs(output_dir)

    #     with open(path.join(output_dir, "{:07}.ist".format(i)), "wb") as f:
    #         fmr.write(f)
    import sys

    fmr = FingerprintMinutiaeRecord()
    with open(sys.argv[1], "rb") as f:
        fmr.read(f)
    print(fmr)
    for finger in fmr.fingers:
        finger.sort_minutiae_by_quality()
        finger.shrink_minutiae(45)
        print("\t{}".format(finger))
        for minutia in finger.minutiae:
            print("\t\t{}".format(minutia))
    with open(sys.argv[1] + ".new", "wb") as f:
        fmr.write(f)
