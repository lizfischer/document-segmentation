# PDF Segmentation Application

# About 

Document segmentation is the process of breaking a digital (or digitized) document into its constituent parts-- for example, splitting a scanned library catalog into individual records. Segmentation is a vital step in many digital humanities projects. Data are often trapped in PDF scans or photographs of materials that are not machine-actionable. Most OCR tools do _some_ degree of layout analysis, but those tools do not allow enough customization in the layout analysis process for them to be useful-- for example, they may find the paragraph boundaries but fail detect when a new "meaningful unit" of content occurs.

This application is a browser-based tool for segmenting non-OCRed PDFs into individual, machine-readable text files. It takes advantage of the huge role whitespace plays in human understanding of a page of text, walking the user through creating custom _rules_ about which bits of whitespace indicate a meaningful break in content, then acting on those rules to automate the separation of even very long documents.


This software was developed from Summer 2022-Spring 2023 as part of my dissertation project “Network Visualization and the Labor of Reference Work: Three Case Studies touching Medieval and Early-Modern Book History”
<br><br><img src="https://user-images.githubusercontent.com/7800842/233444209-71b86f45-5a35-460b-aa48-d02ed169b3d6.png" width="50%">

## License
This software is released under a GNU General Public License v3.0. See `LICENSE` for details.
## Credit

# Getting Started
## Requirements
- Docker
- A web browser -- tested with Firefox and Chrome, your mileage may vary with other browsers.

## Installation
- Clone this repository, or download and unzip the code in a location of your choosing
- Open a terminal/command prompt and navigate to this repository
- Run the command `docker compose up`
- In your browser, navigate to http://127.0.0.1:5000/ 

# User Guide
See the repository [wiki](https://github.com/lizfischer/document-segmentation/wiki/User-Guide) for a guide to using the tool.

# Accuracy
Preliminary ground-truth testing using inputs from four different source documents indicates this whitespace-based method of segmentation performs on average 57% better than textual pattern recognition (through regular expressions) alone. 
|           | Regex Only | Whitespace Segmentation |
| --------- | ---------- | ----------------------- |
| Precision | 45.12%     | 91.67%                  |
| Recall    | 75.51%     | 86.27%                  |
| F1        | 56.49%     | 88.89%                  |
