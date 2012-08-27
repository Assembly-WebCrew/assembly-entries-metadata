import argparse
import asmmetadata
import Image
import os.path
import subprocess

def check_file_exists(value):
    if not os.path.isfile(value):
        raise ValueError("%s is not a file." % value)
    return value

def check_directory_exists(value):
    if not os.path.isdir(value):
        raise ValueError("%s is not a directory." % value)
    return value

parser = argparse.ArgumentParser()
parser.add_argument(
    "--cascade", help=u"Cascade file for face detector.",
    default="/usr/share/opencv/haarcascades/haarcascade_frontalface_alt.xml")
parser.add_argument("face_detector", metavar="face-detector")
parser.add_argument("asmmetadata", type=argparse.FileType("rb"))
parser.add_argument("data_root", type=check_directory_exists)
parser.add_argument("width", type=int)
parser.add_argument("height", type=int)
args = parser.parse_args()

def create_small_thumbnail_file(args, source_filename, entry):
    target_aspect = float(args.width)/args.height

    facedetect_call = [args.face_detector, "--cascade=%s" % args.cascade, source_filename]
    output = subprocess.check_output(facedetect_call)
    output = output.strip()

    if " " not in output:
        output += " "

    dimensions, faces_str = output.split(" ", 1)

    width, height = map(int, dimensions.split("x"))

    class Face(object):
        def __init__(self, left, top, face_width, face_height):
            self.top = int(top)
            self.left = int(left)
            self.width = int(face_width)
            self.height = int(face_height)

        def __repr__(self):
            return "(%d;%d)/%dx%d" % (self.left, self.top, self.width, self.height)

    null_faces = [Face(width / 2, 0, width / 2, 0)]
    faces = [Face(*face_str.split(",")) for face_str in faces_str.split()]

    source_aspect = float(width)/height
    #print target_aspect, source_aspect

    if source_aspect < target_aspect:
        faces_sorted = sorted(faces, lambda first, second: first.top < second.top) + null_faces
        cut_width = width
        cut_height = int(round(cut_width / target_aspect))
        cut_left = 0
        highest_face = faces_sorted[0]
        cut_top = max(0, highest_face.top - highest_face.height * 0.2)
        if cut_top + cut_height > height:
            cut_top = height - cut_height
        cut_top = int(round(cut_top))
    else:
        faces_sorted = sorted(faces, lambda first, second: first.left < second.left) + null_faces
        cut_height = height
        cut_width = int(round(height * target_aspect))
        cut_top = 0
        leftest_face = faces_sorted[0]
        cut_left = max(0, leftest_face.left - leftest_face.width * 0.2)
        if cut_left + cut_width > width:
            cut_left = width - cut_width
        cut_left = int(round(cut_left))

    assert cut_left >= 0
    assert cut_top >= 0
    assert cut_width <= width
    assert cut_height <= height

    print source_filename, faces
    print width, height, len(faces)
    print cut_left, cut_top, cut_width, cut_height

    inphoto = Image.open(source_filename)

    # Just for testing that where the faces are actually detected.
    # import ImageDraw
    # draw = ImageDraw.Draw(inphoto)
    # for face in faces:
    #     draw.rectangle((face.left, face.top, face.left + face.width, face.top + face.height), fill=128)

    cut_region = (cut_left, cut_top, cut_left + cut_width, cut_top + cut_height)
    cropped = inphoto.crop(cut_region)
    scaled = cropped.resize((args.width, args.height), Image.ANTIALIAS)

    full_title = "%s by %s" % (entry['title'], entry['author'])

    section_name = asmmetadata.normalize_key(entry['section']['name'])
    thumbnail_path = os.path.join(args.data_root, "thumbnails", "small", section_name)
    basename = asmmetadata.normalize_key(full_title)
    jpeg_file = os.path.join(thumbnail_path, basename + ".jpeg")
    scaled.save(jpeg_file)
    png_file = os.path.join(thumbnail_path, basename + ".png")
    scaled.save(png_file)

entry_data = asmmetadata.parse_file(args.asmmetadata)
for entry in entry_data.entries:
    section = asmmetadata.normalize_key( entry['section']['name'])
    if "photos" not in section:
        continue

    section_name = asmmetadata.normalize_key(entry['section']['name'])
    file_base = os.path.join(args.data_root, section_name)
    full_title = "%s by %s" % (entry['title'], entry['author'])
    basename = asmmetadata.normalize_key(full_title)
    source_file = os.path.join(file_base, basename + ".jpeg")

    if not os.path.isfile(source_file):
        continue

    create_small_thumbnail_file(args, source_file, entry)
