# PDF Segmentation Application

# About 

(what this tool is for, what it does)
(what need is this filling)

This software was developed from Summer 2022-Spring 2023 as part of Liz Fischer's dissertation project.

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

# Creating a Project
From the application home page, select the New Project button, then choose a PDF to upload.
Once your PDF is uploaded, you will be taken to the Project page. By default, your project will take the name of the PDF you uploaded. To rename your project, click the pencil icon near the project name. 

![Screenshot of the project page](https://user-images.githubusercontent.com/7800842/233429711-88031fe3-9056-414e-9d66-087d7fe89c14.png)

# Basic Method
## Detecting Whitespace
## Classifying Whitespace

# PDF Segmentation Pipeline
![image](https://user-images.githubusercontent.com/7800842/233430310-903f4995-a114-4e3c-8fad-e6b4f6fd3bb2.png)

## Extract Images
![image](https://user-images.githubusercontent.com/7800842/233430358-f7734064-a8b0-446b-879a-1cfc8bf428ba.png)

## Split Pages
![image](https://user-images.githubusercontent.com/7800842/233430550-0f4f56a0-fac6-4fd0-831f-eb52c7da608e.png)
![image](https://user-images.githubusercontent.com/7800842/233430641-b74ae447-8dac-41c0-93a5-be51e919d2f9.png)

## Binarize
![image](https://user-images.githubusercontent.com/7800842/233430859-4bb75b7b-d40a-4f3f-ba22-105a5613491f.png)

## Experiment with Thresholds
![image](https://user-images.githubusercontent.com/7800842/233444209-71b86f45-5a35-460b-aa48-d02ed169b3d6.png)

## Build Rules & Separate
![image](https://user-images.githubusercontent.com/7800842/233445028-867a8a65-b204-4500-b1b6-eb1c4b8be06e.png)

## Export Data
![image](https://user-images.githubusercontent.com/7800842/233445647-f2afe7cb-055d-438e-87b2-fff6bc44b47b.png)
![image](https://user-images.githubusercontent.com/7800842/233445754-41ac7b0c-9d20-4304-96d8-90baae06ee17.png)

## Edit Entries
![image](https://user-images.githubusercontent.com/7800842/233446492-6ac29ea0-874d-4759-ba19-aac761a422f1.png)

![image](https://user-images.githubusercontent.com/7800842/233446291-040c1f0f-449b-4ecc-9801-306677be81b8.png)

![image](https://user-images.githubusercontent.com/7800842/233445876-d9af2629-cddb-48ec-9c13-fd66a4af868e.png)
![image](https://user-images.githubusercontent.com/7800842/233446145-1506862b-4298-4fb2-abe7-9ba3206a5668.png)
