import os

ERROR_FLAG = 'ERROR'
SENDING_EMAIL = os.environ.get('NEWSLETTER_SENDER')
RECEIVING_EMAILS = [os.environ.get('EMAIL_PERSO')]  # email is is env variable as this code is public
AWS_REGION = os.environ.get('AWS_REGION_SCRAPPING')
CLOUD_FRONT_SECRET_KEY = os.path.join(os.path.dirname(os.path.realpath(__file__)), "cloudfront-secret.key")
SES_CONFIGURATION_SET = 'scrapping_config_set'
EMAIL_VALIDITY = 7
