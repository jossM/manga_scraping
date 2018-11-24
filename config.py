import os

ERROR_FLAG = 'ERROR'
SENDING_EMAIL = 'manga.scrapping@gmail.com'
RECEIVING_EMAIL = os.environ.get('EMAIL_PERSO')  # email is is env variable as this code is public
AWS_REGION = os.environ.get('AWS_REGION_SCRAPPING')
SES_CONFIGURATION_SET = 'scrapping_manga'
