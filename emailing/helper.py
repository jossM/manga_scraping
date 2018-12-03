from math import ceil, floor
from typing import List

import boto3
from botocore.exceptions import ClientError

from config import SENDING_EMAIL, RECEIVING_EMAILS, AWS_REGION, SES_CONFIGURATION_SET
from logs import logger
from release_formating import FormattedScrappedReleases

client = boto3.client('ses', region_name=AWS_REGION)

CHARSET = "UTF-8"
SPACES_PER_TAB = 4


def build_html_body(
        formatted_scrapped_releases: List[FormattedScrappedReleases],
        triggered_warnings: List[Warning]) -> str:
    return 'ToDo'


def build_txt_body(
        formatted_scrapped_releases: List[FormattedScrappedReleases],
        triggered_warnings: List[Warning]) -> str:
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
        series_strings = []
        for formatted_scrapped_release in formatted_scrapped_releases:
            title_tab_number = \
                floor((len(formatted_scrapped_release.serie_title) - len(ninth_longuest_title)) / SPACES_PER_TAB)
            serie_string = formatted_scrapped_release.serie_title + '\t'*title_tab_number
            releases_strings = []
            for release in formatted_scrapped_release:
                release_string = ''
                if release.top:
                    release_string = ' Top -> '
                release_string += f'{release}\t{release.link}'
                releases_strings.append(release_string)
            serie_string += ('\t'*serie_name_tab_number + '\n').join(releases_strings)
            series_strings.append(serie_string)
        string_body += '\r\n'.join(series_strings)
    if triggered_warnings:
        string_body += '\n\t\t'.join(str(warning) for warning in triggered_warnings)
    return string_body


def send(subject: str, html_body: str, text_body: str, recipients: List[str]=None):
    if recipients is None:
        recipients = RECEIVING_EMAILS
    try:
        response = client.send_email(
            Destination={'ToAddresses': recipients},
            Message={
                'Body': {'Html': {'Charset': CHARSET, 'Data': html_body},
                         'Text': {'Charset': CHARSET, 'Data': text_body}},
                'Subject': {'Charset': CHARSET, 'Data': subject}},
            Source=SENDING_EMAIL,
            ConfigurationSetName=SES_CONFIGURATION_SET)
    except ClientError as e:
        logger.error(e.response['Error']['Message'])
    else:
        logger.info(f"Email sent! Message ID: {response['MessageId']}")
