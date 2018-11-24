from typing import List

import boto3
from botocore.exceptions import ClientError

from config import SENDING_EMAIL, RECEIVING_EMAIL, AWS_REGION, SES_CONFIGURATION_SET

from release_formating import FormattedScrappedReleases

client = boto3.client('ses', region_name=AWS_REGION)

CHARSET = "UTF-8"


def build_body(
        formatted_scrapped_releases: List[FormattedScrappedReleases],
        triggered_warnings: List[Warning]) -> str:
    pass


def send(subject: str, html_body: str, text_body: str, recipients: List[str]=None):
    if recipients is None:
        recipients = [RECEIVING_EMAIL]
    # ConfigurationSetName=CONFIGURATION_SET argument below.

    BODY_TEXT = ("Amazon SES Test (Python)\r\n"
                 "This email was sent with Amazon SES using the "
                 "AWS SDK for Python (Boto).")

    # The HTML body of the email.
    BODY_HTML = """
    <html>
    <head></head>
    <body>
      <h1>Amazon SES Test (SDK for Python)</h1>
      <p>This email was sent with
        <a href='https://aws.amazon.com/ses/'>Amazon SES</a> using the
        <a href='https://aws.amazon.com/sdk-for-python/'>
          AWS SDK for Python (Boto)</a>.</p>
    </body>
    </html>
     """

    try:
        # Provide the contents of the email.
        response = client.send_email(
            Destination={ 'ToAddresses': recipients},
            Message={
                'Body': { 'Html': { 'Charset': CHARSET, 'Data': html_body },
                          'Text': { 'Charset': CHARSET, 'Data': text_body } },
                'Subject': { 'Charset': CHARSET, 'Data': subject }},
            Source=SENDING_EMAIL,
            # If you are not using a configuration set, comment or delete the
            # following line
            ConfigurationSetName=SES_CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])