# Manga Scraping
Scraping baka-updates on lambda to receive custom news letter on the series in db.
Adds links pointing to likely link of the release using qwant.
Main is located in lambda_function.

##Installation:
 - create a 3.6 python virtualenv
 - install `pip install -r requirements.txt`
 
##Deployement
On ubuntu vm for deployment.
- `ssh -i <certificate> ubuntu@<dns-instance-address> `
- `sudo apt-get update`
- `sudo apt-get install git python3.6 zip`
- `sudo apt-get install python-setuptools python-dev build-essential python3-pip virtualenv awscli`
- `git clone https://github.com/jossM/manga_scraping.git`
- `cd manga_scraping`
- `virtualenv -p python3.6 venv`
- `source venv/bin/activate`
- `pip3 install -t . -r requirements.txt --upgrade`
- `zip -r ~/manga_scraping.zip *`
- `aws s3 cp ~/manga_scraping.zip s3://manga-scraping/code.zip`

##Architecture
- Created several subnet with Internet Gateway in different AZ in us east 1.
- Using lambda to execute with code from zip on s3. (see zip creation above)
- Created a Dynamodb table and added an endpoint in the VPC for lambda to 
access it.  
- Created lambda using the file on s3 and set appropriate variable environment. 
(see full list in config.)