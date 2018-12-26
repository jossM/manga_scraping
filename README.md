# Manga Scraping
Scraping baka-updates on lambda to receive custom news letter on the series I like.
Adds links pointing to likely link of the release.
Main is located in lambda_function.

##Installation:
 - create a 3.6 python virtualenv
 - install `pip install -r requirements.txt`
 
##Limitations
As Google CSE only permits 100 requests per day. There is only so much manga that can be followed.

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
- `aws s3 cp ~/manga_scraping.zip s3://<bucket>/code.zip`

Then deploy lambda using the file on s3 and set appropriate variable environment.