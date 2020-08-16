# Manga Scraping
Scraping baka-updates on lambda to receive custom news letter on the series in db.
Adds links pointing to likely link of the release using qwant.
Main is located in lambda_function.

## Local Development:
 - create a 3.6 python virtualenv and activate it
 - install `pip install -r requirements.txt && pip install -r requirements-dev.txt`
 - get credentials for the service account from aws
 - set variables according to your choice of runner
    - **NEWSLETTER_SENDER** (the email added in aws ses that will be used to send info)
    - **EMAIL_PERSO** (the email which will receive the mail)
    - **AWS_REGION_SCRAPPING** the region that has the lambda function and the dynamo-db table

 then either :
 - **either** run a notebook which you use `os.environ[...]=` for variables
 - **or** `export` variables and run `python main.py` 
 
## Deployement:
On ubuntu vm for deployment.
- `scp -i <certificate> cloudfront-secret.key ubuntu@<dns-instance-address>:~/cloudfront-secret.key`
- `ssh -i <certificate> ubuntu@<dns-instance-address> `
- `sudo apt-get update`
- `sudo apt-get install git python3.6 zip`
- `sudo apt-get install python-setuptools python-dev build-essential python3-pip virtualenv awscli`
- `git clone https://github.com/jossM/manga_scraping.git`
- `mv cloudfront-secret.key manga_scraping/lambda/`
- `cd manga_scraping/lambda`
- `virtualenv -p python3.6 venv`
- `source venv/bin/activate`
- `pip3 install -t . -r requirements.txt --upgrade`
- `zip -r ~/manga_scraping.zip *`
- `aws s3 cp ~/manga_scraping.zip s3://<bucket>/code.zip`
# todo: créer une image docker pour faire ça.

## Architecture
- Created a Dynamodb table for db.
- Using a lambda function to execute with code from zip on s3. (see zip creation above).

- /!\ Could not set the lambda in a VPC with an internet gateway as the gateway was unavailable to the lambda worker.

## Data Model
The code uses a single data table on dynamodb that contains a sorted list of all chapters for a serie within an object.
For precise definition of all fields, see `page_mark_db file.

## Code organisation logic
### structure
Each function corresponds to one of the following types:
- logic (lgq): applies logic on input but does not call function or external services
- service (srv): calls external services and may apply basic logic related to that service but cannot do anything else
- orchestration (orc): main equivalent. calls functions (from the previous 2 types or lower level orchestration function) 
to perform some kind of functionality.

Each file should only contain one kind of function type.
### functionality
The different functionalities used in the project are:
- email sending -> `emailing`
- data retrieval via scrapping -> `skraper`
- data clean up to avoid sending irrelevant information -> `release_formating` 
- data (base) storage -> `page_mark_db`
- system administration tools -> `serie_watcher` (temporary name)