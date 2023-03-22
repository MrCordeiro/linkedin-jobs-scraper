# LinkedIn Job Scraper

This is a simple toolset for mining job postings. It is a work in progress, and is not yet ready for general use.

The idea is to search by company or keyword and save the results locally in a SQLite database.

Company information is saved as JSON files. This is because the schema is not yet know and I was constantly changing it.

## Setup

Create a `.env` file in the root directory with your LinkedIn credentials:

```.env
LINKEDIN_USERNAME = "your-username"
LINKEDIN_PASSWORD = "your password"
```

They will be used to log in to LinkedIn to collect company information.

## Jupyter Notebook

The `notebooks` directory contains some Jupyter notebooks that I was using to play around with the data. The idea is to eventually remove them.
