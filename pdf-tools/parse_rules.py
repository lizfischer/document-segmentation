# Given a gaps file & some rules, break a series of images into entries
import re

import pandas as pd
import pytesseract
from PIL import Image
from tqdm import tqdm

from find_gaps import find_gaps
from models import *
from tesseract import get_formatted_text
from utils import update_status

pd.set_option("display.max_rows", 10, "display.max_columns", None)


def ignore_helper(project, direction, n_gaps, min_size, blank_thresh, task=None, steps=None):
    n_gaps = int(n_gaps)
    min_size = int(min_size)
    blank_thresh = float(blank_thresh)

    if direction == "above" or direction == "below":
        thresholds = get_or_create(db.session, Threshold, h_width=min_size, h_blank=blank_thresh)
    elif direction == "left" or direction == "right":
        thresholds = get_or_create(db.session, Threshold, v_width=min_size, v_blank=blank_thresh)
    else:
        thresholds = None

    x, steps = find_gaps(project, thresh=thresholds, verbose=False, task=task, steps=steps)
    whitespace_data = project.get_whitespace(thresholds)

    if steps:
        steps["current"] += 1
    if task:
        update_status(task, 'Ignoring out of bounds data...', 0, 100, steps)

    for i, ws in enumerate(whitespace_data):
        pg = project.get_page_by_id(ws.page_id)

        if direction == "above":  # ignore text above
            # The 0-start gap is ALWAYS ignored because it is a margin with no text detected at this threshold
            gap = ws.get_nth_horizontal(n_gaps)
            start = int(gap.start + gap.width/2) if gap else 0 # start at the top of the page if there are no gaps to ignore
            pg.set_ignore("start", start)
        elif direction == "below":  # ignore text below
            # The last gap is ALWAYS ignored because it is a margin with no text detected at this threshold
            gap = ws.get_nth_horizontal(-n_gaps - 1)
            end = int(gap.start + gap.width/2) if gap else 0
            pg.set_ignore("end", end)
        elif direction == "left":  # ignore text to the left
            gap = ws.get_nth_vertical(n_gaps - 1)
            left = gap.end - 2  if gap else 0
            # left_edge = page["vertical_gaps"][n_gaps - 1].end - 2  # + page["vertical_gaps"][n_gaps-1]["width"]/2
            pg.set_ignore("left", left)
        elif direction == "right":  # ignore text to the left
            gap = ws.get_nth_vertical(n_gaps - 1)
            right = gap.start + 2  if gap else 0
            pg.set_ignore("right", right)

        if task:
            update_status(task, 'Ignoring out of bounds data...', i+1, len(whitespace_data), steps)

    return True, steps


# rule1 and rule 2 should each take the form {direction: 'above'|'below', n_gaps: #, min_size: #, blank_thresh: #}
# Returns none for starts, ends, lefts, and rights if no rules specified
def ignore(project, rule1=None, rule2=None, task=None, steps=None):
    print("\n***Finding which sections to ignore...***")
    starts, ends, lefts, rights = None, None, None, None

    if rule1:
        if rule1["direction"] == "above":
            starts, steps = ignore_helper(project, "above", rule1["n_gaps"], rule1["min_size"], rule1["blank_thresh"], task=task, steps=steps)
        elif rule1["direction"] == "below":
            ends, steps = ignore_helper(project, "below", rule1["n_gaps"], rule1["min_size"], rule1["blank_thresh"], task=task, steps=steps)
        elif rule1["direction"] == "left":
            lefts, steps = ignore_helper(project, "left", rule1["n_gaps"], rule1["min_size"], rule1["blank_thresh"], task=task, steps=steps)
        elif rule1["direction"] == "right":
            rights, steps = ignore_helper(project, "right", rule1["n_gaps"], rule1["min_size"], rule1["blank_thresh"], task=task, steps=steps)

    if rule2:
        if rule2["direction"] == "above" and not starts:
            starts, steps = ignore_helper(project, "above", rule2["n_gaps"], rule2["min_size"], rule2["blank_thresh"], task=task, steps=steps)
        elif rule2["direction"] == "below" and not ends:
            ends, steps = ignore_helper(project, "below", rule2["n_gaps"], rule2["min_size"], rule2["blank_thresh"], task=task, steps=steps)
        elif rule2["direction"] == "left" and not lefts:
            lefts, steps = ignore_helper(project, "left", rule2["n_gaps"], rule2["min_size"], rule2["blank_thresh"], task=task, steps=steps)
        elif rule2["direction"] == "right" and not rights:
            rights, steps = ignore_helper(project, "right", rule2["n_gaps"], rule2["min_size"], rule2["blank_thresh"], task=task, steps=steps)
        else:
            print("Rule 2 ignored because it would replace rule 1")

    return steps

def ocr_page(page, start=None, end=None, left=None, right=None):
    custom_config = r'-c preserve_interword_spaces=1 --oem 1 --psm 1 -l eng+ita'  # TODO: Add language customization?

    # Get the image & run Tesseract
    image_path = page.get_img()

    df = pytesseract.image_to_data(Image.open(image_path), output_type='data.frame', config=custom_config).dropna()

    # Remove ignored areas at start & end
    content = df
    if start:
        content = content[content["top"] > start]
    if end:
        content = content[content["top"] < end]
    if left:
        content = content[content["left"] > left]
    if right:
        content = content[content["left"] < right]
    return content


def write_entries(project):
    project_folder = project.get_folder()
    file = os.path.join(project_folder, "entries.json")
    data = project.entries_to_json()
    with open(file, "w") as outfile:
        json.dump(data, outfile, indent=4)
    return file


# TODO: Rethinking the available rules
# What are the cases that I actually see in the documents?
# 1. After gap of certain size
# 2. Text to the left of a certain line, and (after gap of certain size or at the top of a page)
# could have "simple" and "advanced" versions. Simple has a problem with top-of-page starts. Could get regex involved?


# validate inputs for simple_separate TODO: Expand validation
# split = "strong" | "weak" | "regex"
# ignore = [start, end]
def simple_separate_val(split, regex=None):
    valid_types = ["strong", "weak", "regex"]
    if split not in valid_types:
        raise ValueError(f"Invalid split type: '{split}'. Split type should be one of {valid_types}")
    if split == "regex":
        if not regex:
            raise ValueError("Split type 'regex', but no regular expression provided.")
        try:
            re.compile(regex)
        except re.error:
            raise ValueError(f"Non-valid regex pattern: {regex}")
    # if len(ignore) != 4:
    #     raise ValueError(f"Invalid shape for 'ignore'. Expected [starts, ends, lefts, rights] but received: {ignore}")
    return True


# IN SIMPLE SEPARATE, NEW ENTRIES START:
# After gap of a certain size, OR at the top of the page IF the first line of text meets certain conditions
# option to always start a new entry at the top ("strong split"), or never do so ("weak split")
# So the options are: Always, never, or first-line regex
# FIXME: Can I decompose this method more?
def simple_separate(project, gap_size, blank_thresh, split, regex=None, task=None, steps=None):
    simple_separate_val(split=split, regex=regex)

    print("\n***Removing old entry data...***")
    project.clear_entries()

    print("\n***Starting simple separate...***")
    print("\n**Finding gaps...**")

    # Do gap recognition at the set threshold
    thresholds = get_or_create(db.session, Threshold, h_width=gap_size, h_blank=blank_thresh)
    if steps:
        steps['prefix_message'] = 'Separating entries'
    find_gaps(project, thresh=thresholds, verbose=False, task=task, steps=steps)

    print("\n**Separating entries gaps...**")

    # Establish list of entries & var to track the active entry
    separated_entries = []
    active_entry = {"text": "", "pages": []}

    def save_entry():
        nonlocal active_entry
        nonlocal project
        if active_entry["text"] != "":
            e = Entry(text=active_entry["text"])
            project.add_entry(e)
            for p in active_entry["pages"]:
                x,y,w,h = p["xywh"].split(",")
                e.add_box(BoundingBox(page=p["page"], x=x, y=y, w=w, h=h))

    def get_bounds(df_slice):
        df_slice["right"] = df_slice["left"] + df_slice["width"]
        df_slice["bottom"] = df_slice["top"] + df_slice["height"]
        x = df_slice["left"].min()
        y = df_slice["top"].min()
        w = df_slice["right"].max() - x
        h = df_slice["bottom"].max() - y
        return f"{x},{y},{w},{h}"

    def new_entry(df_slice, pg):
        nonlocal active_entry
        save_entry()  # save the previous entry first!
        active_entry = {"text": get_formatted_text(df_slice),
                        "pages": [{"page": pg, "xywh": get_bounds(df_slice)}]
                        }

    def add_to_entry(df_slice, pg):
        nonlocal active_entry
        t = get_formatted_text(df_slice)
        active_entry["text"] += f"\n\n{t}"
        active_entry["pages"].append({"page": pg, "xywh": get_bounds(df_slice)})

    pages = project.get_pages()

    if steps:
        steps['current'] += 1
    if task:
        update_status(task, 'Separating...', 0, len(pages), steps)

    # For each page in numerical order NB: this relies on find_gaps returning a SORTED list
    for i, page in enumerate(pages):  # NOTE: This is the place to limit pages if desired for testing
        n = page.sequence

        # OCR the page
        start = page.ignore_start if page.ignore_start else 0
        end = page.ignore_end if page.ignore_end else page.height
        left = page.ignore_left if page.ignore_left else 0
        right = page.ignore_right if page.ignore_right else page.width

        ocr = ocr_page(page, start, end, left, right)

        # Get relevant gaps (ie take the ignore boundaries into account) # find this page
        all_page_gaps = page.get_whitespace(thresholds).get_horizontal()
        gaps_within_content = [g for g in all_page_gaps if g.start > start and g.end < end]

        # FIRST GAP
        n_gaps_considered = 0
        # If there are no gaps, select the whole page
        if len(gaps_within_content) == 0:
            active_selection = ocr
        # If there are gaps, select up to the first gap
        else:
            active_selection = ocr[ocr["top"] < gaps_within_content[0].start]
            n_gaps_considered += 1  # we've looked up to the first gap

        # Decide what to do with the selected text (top of page) based on the split method specified
        # If strong, start a new entry
        if split == "strong":
            new_entry(active_selection, n)
            # active_entry = get_formatted_text(active_selection)
        # If weak, append to previous entry
        elif split == "weak":
            add_to_entry(active_selection, n)
            # active_entry += f"\n\n{get_formatted_text(active_selection)}"
        # If regex, test regex and then either append or start new
        elif split == "regex" and regex:
            # Get text
            text = get_formatted_text(active_selection)
            needs_split = re.search(regex, text)

            if needs_split:  # Start a new entry
                new_entry(active_selection, n)
            else:  # Do NOT start a new entry, append current selection to previous entry instead
                add_to_entry(active_selection, n)
                # active_entry += f"\n\n{text}"

        # If there are NO gaps on the page, move to the next page
        if len(gaps_within_content) == 0: continue

        # GAPS AFTER THE FIRST
        # While there are more gaps on the page, select the text between the "last" gap and the "next" gap
        while n_gaps_considered < len(gaps_within_content):
            upper_bound = gaps_within_content[n_gaps_considered - 1].start
            lower_bound = gaps_within_content[n_gaps_considered].start
            active_selection = ocr[ocr["top"] > upper_bound]  # below last gap
            active_selection = active_selection[active_selection["top"] < lower_bound]  # above next gap

            # Start a new entry and add the selected text to it
            new_entry(active_selection, n)
            # active_entry = get_formatted_text(active_selection)

            # Increment gaps considered (entry will get "finished" when the next entry starts)
            n_gaps_considered += 1

        # WHEN THERE ARE NO GAPS LEFT
        # select the text between the last gap & the bottom of the page
        upper_bound = gaps_within_content[n_gaps_considered - 1].start
        active_selection = ocr[ocr["top"] > upper_bound]
        # start a new entry and add the selected text to it
        new_entry(active_selection, n)
        # active_entry = get_formatted_text(active_selection)

        if task:
            update_status(task, 'Separating...', i, len(pages), steps)

    save_entry()
    return write_entries(project)


# TODO: Indent separate parser
# Indent separate
# type - hanging or regular

def indent_separate_val(project_id, indent_type, margin_thresh, indent_width, ignore):
    valid_types = ["hanging", "regular"]
    if indent_type not in valid_types:
        raise ValueError(f"Invalid indent type: '{indent_type}'. Split type should be one of {valid_types}")

    if not isinstance(margin_thresh, float):
        raise TypeError(f"Invalid margin threshold: '{margin_thresh}'. Expecting float, received {type(margin_thresh)}")

    if not isinstance(indent_width, float):
        raise TypeError(f"Invalid margin threshold: '{indent_width}'. Expecting float, received {type(indent_width)}")

    if len(ignore) != 4:
        raise ValueError(f"Invalid shape for 'ignore'. Expected [starts, ends, lefts, rights] but received: {ignore}")

    return True


def indent_separate(project_id, indent_type, margin_thresh, indent_width, ignore):
    indent_separate_val(project_id, indent_type, margin_thresh, indent_width, ignore)

    starts = ignore[0]
    ends = ignore[1]
    lefts = ignore[2]
    rights = ignore[3]

    print("\n***Starting simple separate...***")
    # Do gap recognition at the set threshold
    thresh = Threshold(v_blank=margin_thresh)
    binary_im_dir = f"interface/static/projects/{project_id}/binary_images"
    gaps_data = find_gaps(binary_im_dir, thresh=thresh, verbose=False)

    # Establish list of entries & var to track the active entry
    separated_entries = []
    active_entry = ""

    # For each page in numerical order NB: this relies on find_gaps returning a SORTED list
    for p in tqdm(gaps_data):  # NOTE: This is the place to limit pages if desired for testing
        n = p["num"]

        # OCR the page
        start = starts[n] if starts else 0
        end = ends[n] if ends else p["height"]
        left = lefts[n] if lefts else 0
        right = rights[n] if rights else p["width"]

        ocr = ocr_page(project_id, n, start, end, left, right) # FIXME

        # Find left margin
        all_vertical_gaps = next((pg for pg in gaps_data if pg["num"] == n), None)["vertical_gaps"]  # find this page
        left_margin_line = all_vertical_gaps[0].end

        # Group by line
        lines = ocr.groupby(["block_num", "par_num", "line_num"])
        line_starts = lines.first()

        # Go through line by line
        for line in lines:
            first_word = line[1].iloc[0]
            if indent_type == "hanging":
                is_start = first_word["left"] < left_margin_line - 5  # NOTE: 5 fudge pixels-- this could be a variable?
            else:  # indent_type is "regular"
                is_start = first_word["left"] > left_margin_line + indent_width-5

            # TODO: Get text between, etc.