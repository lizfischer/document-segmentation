import sys
import uuid
import numpy as np
np.set_printoptions(threshold=sys.maxsize)

import whitespace_helpers as ws
from models import *


##
# Saves a dataframe to the given directory with the name "whitespace.json"
# Returns the file name
def write_output(df, output_dir, thresholds, thresholds_in_filename=False):
    sorted_pages = sorted(df, key=lambda x: x["num"])
    if thresholds_in_filename:
        filename = f"{output_dir}/whitespace_{thresholds.h_width}-{thresholds.h_blank}-" \
               f"{thresholds.v_width}-{thresholds.v_blank}.json"
    else:
        filename = f"{output_dir}/whitespace.json"
    output = { "thresholds": thresholds.toJSON(), "pages": sorted_pages}
    with open(filename, "w") as outfile:
        json.dump(output, outfile, indent=4)
    return filename


##
# Turn the output of gap detection into annotations for Annotorious
##

class Annotation:
    def __init__(self, x, y, w, h, text=""):
        self.id = uuid.uuid1()
        self.text = text
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.json = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "project_id": f"#{self.id}",
            "type": "Annotation",
            "body": [{
                "type": "TextualBody",
                "value": f"{self.text}"
            }],
            "target": {
                "selector": {
                    "type": "FragmentSelector",
                    "conformsTo": "http://www.w3.org/TR/media-frags/",
                    "value": f"xywh=pixel:{x},{y},{w},{h}"
                }
            }
        }


def whitespace_to_annotations(data, page):
    annotations = []
    # First vertical gap, start at end of the gap
    annotation = Annotation(data["vertical_gaps"][0]["end"], 0, 1, page.height)
    annotations.append(annotation.json)

    # Middle vertical gaps, give the midpoint
    for v in data["vertical_gaps"][1:-1]:
       x = v['start'] + v['width'] / 2
       annotation = Annotation(x, 0, 1, page.height)
       annotations.append(annotation.json)

    # Last vertical gap, start at start of the gap
    if len(data["vertical_gaps"]) > 2 :
       annotation = Annotation(data["vertical_gaps"][-1]["start"], 0, 1, page.height)
    annotations.append(annotation.json)

    # First horizontal gap, start at end of the gap
    annotation = Annotation(0, data["horizontal_gaps"][0]["end"], page.width, 1)
    annotations.append(annotation.json)

    # Middle horizontal gaps, give the midpoint
    for h in data["horizontal_gaps"][1:-1]:
        y = h['start'] + h["width"] / 2
        annotation = Annotation(0, y,  page.width, 1, text=h["width"])
        annotations.append(annotation.json)

    # Last horizontal gap, start at start of the gap
    annotation = Annotation(0, data["horizontal_gaps"][-1]["start"],  page.width, 1)
    annotations.append(annotation.json)

    return json.dumps(annotations)


##
# Given an image and a set of threshold values, find the whitespace on a page
#
# Threshold should contain:
# h_width: the minimum width of a horizontal space (in px)
# h_blank: The % of pixels in a horizontal line that are blank to "count" the line as blank
# v_width: the minimum width of a vertical space (in px)
# v_blank: the % of pixels in a horizontal line that are blank to "count" the line as blank
#
# Returns ALL the qualifying gaps on a page. This can be used to later classify
# different kinds of gaps (margin, header, etc)
def process_page(im_path, thresholds, viz=False):
    img, img_binary = ws.get_binary_image(im_path)
    height, width = img_binary.shape
    try:
        horizontal_gaps = ws.find_gaps_directional(img_binary, 1, width_thresh=thresholds.h_width,
                                                  blank_thresh=thresholds.h_blank)
        vertical_gaps = ws.find_gaps_directional(img_binary, 0, width_thresh=thresholds.v_width,
                                                  blank_thresh=thresholds.v_blank)
    except IndexError:  # FIXME: When was this throwing an error
        horizontal_gaps = []
        vertical_gaps = []
    except ValueError:
        raise

    if viz:
        ws.visualize(img_binary, horizontal_gaps, vertical_gaps)

    return {"height": height,
            "width": width,
            "vertical_gaps": vertical_gaps,
            "horizontal_gaps": horizontal_gaps}


def find_gaps(project, thresh=None,
              viz=False, verbose=True):

    if verbose:
        print("\n*** Detecting margins & whitespace... ***")
    if not thresh:
        thresh = Threshold.get_default()

    if project.has_whitespace(thresh):
        return True

    for page in project.get_pages(): # for every page
        image_path = page.get_binary()
        try:
            data = process_page(image_path, thresh, viz=viz) # Try to process the page
        except ValueError:
            continue  # If you can't, skip it

        whitespace = Whitespace(threshold=thresh)

        for gap in data["vertical_gaps"]:
            g = Gap(start=gap["start"], end=gap["end"], width=gap["width"], direction="vertical")
            whitespace.add_gap(g)
        for gap in data["horizontal_gaps"]:
            g = Gap(start=gap["start"], end=gap["end"], width=gap["width"], direction="horizontal")
            whitespace.add_gap(g)
        whitespace.set_annotation(whitespace_to_annotations(data, page))

        page.add_whitespace(whitespace)
        project.set_gaps(True)

    return True