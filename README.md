# Capstone Project
- Author: Michelle Mark
- For: Bachelors of Science in Computer Science, SUNY Poly
- Copyright: All rights reserved, 2025

## Central New York Real Estate Trends and Analytics App

### Goal 1:
Build an automated ETL pipeline to pull in available free data on
real estate in the Central New York area.  Clean and normalize the
data into an SQLite database.  Train a machine learning
model to draw further trends and statistics from the data,
and add values to the database.  Present analytics in a user-friendly 
interface that provides both graphs for visualization and filtering.  

Options to filter data should include at least:
1. Property type, (ie: single family vs multifamily, etc.)
2. Zip code
3. School district

### Goal 2:

After each automated ETL / ML pipeline run data is updated in user interface.

### Goal 3:
Saving a change to main branch of repository will deploy to production environment.

### Goal 4:
Optionally, make the app available publicly with no ongoing cost.

## Implementation Choices Made

## Open NY APIs

New York State makes a wide variety of data available to the public via APIs, including 
the property assessment data we will use for the main bulk of the data imported by this
project, as it is free.

https://dev.socrata.com/consumers/getting-started.html

The ETL pipeline will be collecting data for CNY Counties from:
- [Property Assessment Data from Local Assessment Rolls](https://dev.socrata.com/foundry/data.ny.gov/7vem-aaz7)
- [Residential Assessment Ratios](https://dev.socrata.com/foundry/data.ny.gov/bsmp-6um6)


### What NY counties will make up CNY for purposes of this project?

The [Central New York Regional Planning & Development Board](https://www.cnyrpdb.org/region.asp) defines Central New York as

- Cayuga
- Cortland
- Madison
- Onondaga
- Oswego

### GitHub Actions

GitHub Actions usage is free for standard GitHub-hosted runners in public repositories, such as this.  
The ETL ML Pipeline is run in GitHub actions, where it can be executed for no ongoing cost.
It is set up to be manually executed, but it could easily be scheduled, if that were needed.


### AWS Data Storage

The generated SQLite database is stored in an AWS s3 bucket for a trivially small ongoing cost.
Database estimated to stay below 250Mb in size, so an estimate of ongoing costs would be:

**S3 Standard Storage Rates**: **$0.023 per GB per month**

    1 GB = 1024 MB so 250 MB is 250 ÷ 1024 or about 0.2441 GB

**Ongoing Cost:**

    0.2441 * 0.023 ≈ 0.0056 per month (about half of a cent)
    0.0056 * 12 ≈ 0.07 cents per year

## Development
This repository has been developed using Python 3.12.  
To install all required modules in your Python 3.12 virtual environment run command:
```
pip install -r requirements.txt
```

### Unit Tests

Unit testing has been set up using pytest and tox and should be run with the command
```
tox
```

### Local development:

To run the workflow locally:

- Activate your python 3.12 venv with `requirements.txt` installed
- Set needed environment variables:
``` python
AWS_ACCESS_KEY_ID # For an AWS user with permissions on your desired s3 bucket to use
AWS_SECRET_ACCESS_KEY # For an AWS user with permissions on your desired s3 bucket to use
AWS_REGION # Region the s3 bucket you wish to use is located in
OPEN_DATA_APP_TOKEN # Your free app token for Open NY API access
```

Then run the ETL workflow with:
```
python -m etl.etl_ml_flow
```
