import pytesseract
from PIL import Image
import json
from tqdm import tqdm
import pandas as pd
import numpy as np

pd.set_option("display.max_rows", None, "display.max_columns", None)

THRESHOLD = 50  # number of pixels before identified start to begin looking for entry text
TAB_THRESHOLD = 10
global all_entries, active_entry


def write_output(outfile):
    global all_entries
    with open(outfile, "w") as f:
        json.dump(all_entries, f, indent=4)


# mostly copied from stackoverflow... Made a few changes to make it actually show multiple blocks
# https://stackoverflow.com/questions/59582008/preserving-indentation-with-tesseract-ocr-4-x
def get_formatted_text(df, sort=True):
    try:
        if sort:
            block_order = df.groupby('block_num').first().sort_values('left').sort_values('top').index.tolist()
        else:
            block_order = df.groupby('block_num').first().index.tolist()
        text = ''
        for block in block_order:
            curr = df[df['block_num'] == block]
            sel = curr[curr.text.str.len() > 3]
            char_w = (sel.width / sel.text.str.len()).mean()
            prev_par, prev_line, prev_left = 0, 0, 0
            for ix, ln in curr.iterrows():
                # add new line when necessary
                if prev_par != ln['par_num']:
                    text += '\n'
                    prev_par = ln['par_num']
                    prev_line = ln['line_num']
                    prev_left = 0
                elif prev_line != ln['line_num']:
                    text += '\n'
                    prev_line = ln['line_num']
                    prev_left = 0

                added = 0  # num of spaces that should be added
                if ln['left'] / char_w > prev_left + 1:
                    added = int((ln['left']) / char_w) - prev_left
                    text += ' ' * added
                text += ln['text'] + ' '
                prev_left += len(ln['text']) + added + 1
            text += '\n'
        return text.strip()
    except OverflowError:  # TODO Real solution?
        return ""


def finish_entry():
    global active_entry, all_entries
    if active_entry["text"].strip():
        all_entries.append(active_entry)
    active_entry = {"text": "", "pages": []}


def do_recognize(margin_data):
    print("\n *** OCRing image regions... ***")

    # Make file name
    outfile = "/".join(margin_data.split_pdf("/")[:-1]) + "/ocr.json"

    global active_entry, all_entries

    # Prep lists
    all_entries = []
    active_entry = {"text": "", "pages": []}

    # Load margin data
    with open(margin_data, "r") as f:
        pages = json.load(f)

    # Do The Thing
    for page in tqdm(pages):
        # incremental save
        if page["p"] % 20 == 0:
            write_output(outfile)

        # Get image
        image_path = page["image"]

        # OCR
        custom_config = r'-c preserve_interword_spaces=1 --oem 1 --psm 1 -l eng+ita'
        df = pytesseract.image_to_data(Image.open(image_path), output_type='data.frame', config=custom_config).dropna()

        # For every gap
        prev_divider = 0
        for divider in page["gaps"]:
            # Select body text
            section = df[df["top"] < divider]
            section = section[section["top"] > prev_divider]
            section = section[section["left"] > page["left_margin"]]  # only select main column, not left-marginal stuff

            # Reset the divider bounds
            prev_divider = divider

            # remove blank-only text
            section["text"].replace('\s+', np.nan, inplace=True, regex=True)
            section.dropna(subset=['text'], inplace=True)

            # Group by line
            lines = section.groupby(["block_num", "par_num", "line_num"])
            line_starts = lines.first()

            # Find the average left-start of the text
            avg_left = line_starts.iloc[2:]["left"].median()

            # If there are multiple lines, check for an indent
            if len(lines) > 1:
                line_two_left = line_starts.iloc[1]["left"]
                # If the second line starts significantly right of average, this section it's a new document.
                if line_two_left > avg_left + TAB_THRESHOLD:
                    if active_entry["text"]:  # append the old entry if it has text in it
                        all_entries.append(active_entry)
                    active_entry = {"text": "", "pages": []}

            # Add current section to active entry
            active_entry["text"] += get_formatted_text(section)
            if page["p"] not in active_entry["pages"]:
                active_entry["pages"].append(page["p"])  # Question: does this work?

    # Add last entry
    all_entries.append(active_entry)
    write_output(outfile)
    return outfile
