# Acquisition Workflow Automation

This project automates the process of gathering, processing, and documenting public acquisition data from the Romanian e-licitatie.ro platform. It's designed to streamline the workflow of collecting data from SICAP (Sistemul Electronic de Achiziții Publice), enriching it, and generating reports.

## About The Project

This project is a Python-based application that automates the entire acquisition workflow, from data extraction to document generation. It's built to be robust and resilient, with features like automatic browser crash recovery and detailed logging.

## Features

*   **Automated Data Scraping:** The project uses Selenium to automate the process of scraping acquisition data from the e-licitatie.ro website.
*   **Data Cleaning and Processing:** The project uses the pandas library to clean and process the scraped data, ensuring that it's accurate and consistent.
*   **Document Generation:** The project uses the docxtpl library to generate Word documents from templates, populating them with the processed data.
*   **Resilient Scraping:** The scraping process is designed to be resilient to browser crashes, with automatic recovery and retry mechanisms.
*   **Modular Architecture:** The project has a modular architecture, with separate components for scraping, data processing, and document generation.
*   **Web Interface and Asynchronous Tasks:** The project includes a Flask-based web interface and uses Celery and Redis for asynchronous task processing.

## Workflow

The project's workflow consists of the following steps:

1.  **Cleaning:** The workflow starts by cleaning an Excel file that contains a list of SICAP IDs.
2.  **Scraping:** The project then scrapes the e-licitatie.ro website to gather data for each SICAP ID.
3.  **Splitting:** The scraped data is split into separate files based on the CUI (Cod Unic de Înregistrare).
4.  **Beneficiary Scraping:** The project then scrapes beneficiary data from the PNRR (Planul Național de Redresare și Reziliență) website.
5.  **Document Generation:** Finally, the project generates Word documents from templates, populating them with the processed data.

## Technical Stack

The project is built using the following technologies:

*   **Python:** The core programming language used in the project.
*   **Selenium:** A web browser automation library used for scraping data from websites.
*   **Pandas:** A data manipulation and analysis library used for cleaning and processing the scraped data.
*   **Openpyxl:** A library for reading and writing Excel files.
*   **Docxtpl:** A library for generating Word documents from templates.
*   **Flask:** A web framework used for the project's web interface.
*   **Celery:** A distributed task queue used for asynchronous task processing.
*   **Redis:** An in-memory data store used as a message broker for Celery.

## Setup and Usage

To set up and run the project, you'll need to have Python and the required libraries installed. You can install the libraries using pip:

pip install -r requirements.txt

You'll also need to have a `.env` file with the following environment variables:

PNRR_EMAIL=your_email
PNRR_PASSWORD=your_password

To run the main workflow, you can execute the `run_workflow.py` script:

python run_workflow.py
