import json
from tqdm import tqdm
import os


def save_txt(ocr):
    print("*** Saving OCR to txt files... ***")

    # Make output directory
    out_dir = ocr.replace("ocr.json", "txt")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Load OCR json
    with open(ocr, "r") as f:
        entries = json.load(f)

    # Write text files
    for i in tqdm(range(0, len(entries))):
        with open(f"{out_dir}/{i}.txt", "w", encoding="utf-8") as f:
            f.write(entries[i]["text"])


if __name__ == "__main__":
    save_txt("")
