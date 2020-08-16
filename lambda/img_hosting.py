import os
from datetime import datetime, timedelta

import boto3
from botocore.signers import CloudFrontSigner
import rsa

from utils import encode_in_base64

IMG_FORMAT = "webp"


def rsa_signer(message):
    private_key = os.getenv("CLOUD_FRONT_KEY_SECRET")
    return rsa.sign(
        message,
        rsa.PrivateKey.load_pkcs1(private_key.encode('utf8')),
        'SHA-1')


cloudfront_signer = CloudFrontSigner(os.getenv("CLOUD_FRONT_KEY_ID", ""), rsa_signer)
BUCKET = "manga-scraping-img"
S3_REGION = "eu-west-1"  # Must corresponds to terraform provider region!


def build_serie_img_viewer_url(serie_id: str, days_to_live: int = 3) -> str:
    """ build the image full path for html creation """
    cdn_domain = os.getenv("CLOUD_FRONT_DISTRIBUTION_DOMAIN")
    if cdn_domain is None:
        raise EnvironmentError(f'Cloud front distribution not found when dealing with serie {serie_id}')
    path = build_url_path(serie_id)
    url = f"https://{cdn_domain}/{path}"
    return cloudfront_signer.generate_presigned_url(
        url=url, date_less_than=datetime.now() + timedelta(days=days_to_live))


def build_url_path(serie_id: str):
    """ build the relative path to the serie """
    return f"i{encode_in_base64(serie_id)}.{IMG_FORMAT}"


def expose_image(serie_id: str, image_file_path: str) -> None:
    """ host the image on the bucket exposed via the cdn """
    from PIL import Image  # this is not imported at the top level as this library is used only for cli
    local_img = Image.open(image_file_path)
    formatted_img_path = os.path.join(os.path.dirname(os.path.abspath(image_file_path)),
                                      f"formatted_img_{serie_id}.webp")
    local_img.convert("RGB").save(formatted_img_path, "webp", quality=50)

    s3_client = boto3.client("s3")
    s3_client.upload_file(Filename=image_file_path,
                          Bucket=BUCKET,
                          Key=build_url_path(serie_id))


def delete_image(serie_id: str) -> None:
    """ delete the image on the bucket """
    s3_client = boto3.client("s3")
    s3_client.delete_object(
        Bucket=BUCKET,
        Key=build_url_path(serie_id))
