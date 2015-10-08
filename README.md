# Item-catalog

## Intro
The Item catalog project consists of web site to manipulate a product item catalog

## Requirements
The application requires a python instalation in the host machine. The recommended version is the 2.7 
Also the following python package are required in orer to run the application
- Flask == 0.9
- SQLAlchemy == 0.8.4
- httplib2 == 0.9.1
- Requests == 2.7.0
- dicttoxml == 1.6.6
- google_api_python_client == 1.4.1

## Installation and Set Up
The application files are located inside the folder AppCode. In order to install the application do the following
- Download the repository
- Open a command console
- Change your current directory to the folder ***item-catalog/AppCode***
- Run ***pip install -r requirements.txt*** in order to install the application's requirenment
- Run ***python database_setup.py*** in order to create the database
- Run ***python some_items.py*** in order to add some items to the database
- Run ***python application.py***

## How to run
Open a browser and navigate to ***http://localhost:8000***

## Usage
The main page display the catalag's category on the right side of the screen and on the left the lastest
items defined in the catalog. From the main page you can do the following actions:
- Click on a category, displays all the items inside this category
- Click on an item, display a page with the intem;s information
- After login you can create items using the Add button in the main page
- After login you can Edit and Delete ietem from the item's detail page