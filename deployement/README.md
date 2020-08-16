# Deployment

This terraforms defines almost everything that should be deployed.

The solution hosts images on a s3 bucket and exposes them via a secured cloudfront distribution.
This is necessary to display them in mails.

Since the access is secured, you need to manage cloudfront keys for which AWS does not offer an API.

To deploy you must :
- Go [in the console](https://console.aws.amazon.com/iam/home#/security_credentials) and generate a cloudfront key pair.
- Fill the secrets.tf file with the key info
- launch in the current folder :
```
terraform init --backend-config backend.tfvars
terraform apply -var-file backend.tfvars -var-file secrets.tfvars -var-file public-environment-config.tfvars
```
