from datetime import datetime
from math import ceil, floor
import os
from typing import List

import boto3
from botocore.exceptions import ClientError
from jinja2 import Environment, FileSystemLoader

from config import SENDING_EMAIL, RECEIVING_EMAILS, AWS_REGION, SES_CONFIGURATION_SET
from logs import logger
from release_formating import FormattedSerieReleases

ses_client = boto3.client('ses', region_name=AWS_REGION)

CHARSET = "UTF-8"
SPACES_PER_TAB = 4
THIS_DIR = os.path.dirname(os.path.abspath(__file__))


def _make_todays_date() -> str:
    """ build today's date as a standard format """
    return datetime.now().strftime("%a %d-%b")


def build_html_body(formatted_scrapped_releases: List[FormattedSerieReleases],
                    serie_number: int) -> str:
    """ creates an email body to be sent """
    j2_env = Environment(loader=FileSystemLoader(THIS_DIR),
                         trim_blocks=True,
                         lstrip_blocks=True)
    log_link = f"https://console.aws.amazon.com/cloudwatch/home?region={AWS_REGION}" \
               f"#logStream:group=/aws/lambda/manga_scrapping;streamFilter=typeLogStreamPrefix"
    return j2_env.get_template('mail_template.html').render(
        date_str=_make_todays_date(),
        serie_number=serie_number,
        all_series_releases=formatted_scrapped_releases,
        log_link=log_link)


def build_txt_body(formatted_scrapped_releases: List[FormattedSerieReleases]) -> str:
    """ builds a string as default display in case the html body was bad """
    string_body = "Hello,\n"
    if not formatted_scrapped_releases:
        string_body += 'no new release were available for your series.\n'
    else:
        titles = sorted([serie.serie_title for serie in formatted_scrapped_releases],
                        key=lambda title: len(title), reverse=True)
        if titles:
            ninth_longuest_title = titles[floor(len(titles)*.9)]
        else:
            ninth_longuest_title = ''
        serie_name_tab_number = int(ceil(float(len(ninth_longuest_title)) / SPACES_PER_TAB))
        line_start = '\n' + '\t'*serie_name_tab_number
        series_strings = []
        for formatted_scrapped_release in formatted_scrapped_releases:
            title_tab_number = \
                floor((len(formatted_scrapped_release.serie_title) - len(ninth_longuest_title)) / SPACES_PER_TAB)
            serie_string = formatted_scrapped_release.serie_title + '\t'*title_tab_number
            releases_strings = []
            for release in formatted_scrapped_release:
                release_string = ''
                if release.top:
                    release_string = 'Top -> '
                release_string += f'{release}\t\t{release.link}'
                releases_strings.append(release_string)
            serie_string += line_start + line_start.join(releases_strings)
            series_strings.append(serie_string)
        string_body += '\r\n'.join(series_strings)
    return string_body


def send_newsletter(html_body: str, text_body: str):
    recipients = RECEIVING_EMAILS
    try:
        response = ses_client.send_email(
            Destination={'ToAddresses': recipients},
            Message={
                'Body': {'Html': {'Charset': CHARSET, 'Data': html_body},
                         'Text': {'Charset': CHARSET, 'Data': text_body}},
                'Subject': {'Charset': CHARSET, 'Data': f'Manga Newsletter - {_make_todays_date()}'}},
            Source=SENDING_EMAIL,
            ConfigurationSetName=SES_CONFIGURATION_SET)
    except ClientError as e:
        logger.error(e.response['Error']['Message'], exc_info=True)
    else:
        logger.info(f"Email sent! Message ID: {response['MessageId']}")
