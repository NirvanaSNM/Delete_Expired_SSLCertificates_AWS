import boto3
import datetime
import botocore

def lambda_handler(event, context):
    session = boto3.Session()
    regions = session.get_available_regions('acm')
    expired_certs = []

    for region in regions:
        expired_certs.clear()

        try:
            client = boto3.client("acm", region_name=region)
            paginator = client.get_paginator("list_certificates")

            for response in paginator.paginate():
                for cert in response["CertificateSummaryList"]:
                    cert_arn = cert["CertificateArn"]
                    cert_detail = client.describe_certificate(CertificateArn=cert_arn)
                    expiration_date = cert_detail["Certificate"]["NotAfter"]
                    now = datetime.datetime.now(datetime.timezone.utc)

                    if expiration_date < now:
                        expired_certs.append(cert_arn)

            for cert_arn in expired_certs:
                cert_detail = client.describe_certificate(CertificateArn=cert_arn)
                in_use_by = cert_detail["Certificate"].get("InUseBy")
                if in_use_by:
                    in_use_by = in_use_by[0]
                    client_elbv2 = boto3.client("elbv2", region_name=region)
                    response = client_elbv2.describe_listeners(LoadBalancerArn=in_use_by)
                    for listener in response["Listeners"]:
                        try:
                            client_elbv2.remove_listener_certificates(
                                ListenerArn=listener["ListenerArn"],
                                Certificates=[
                                    {
                                        'CertificateArn': cert_arn,
                                    },
                                ]
                            )
                            print(f"The certificate {cert_arn} is in use by the load balancer {in_use_by}.")
                            print(f"The listener {listener['ListenerArn']} is using this certificate.")
                            print(f"The certificate {cert_arn} will be removed from the listener {listener['ListenerArn']}.")
                        except botocore.exceptions.ClientError as e:
                            error_code = e.response.get("Error", {}).get("Code")
                            if error_code == "OperationNotPermitted":
                                print(f"Error: {error_code} - Default certificate cannot be removed.")
                                print(f"Load Balancer ARN: {in_use_by}")
                                print(f"Certificate ARN: {cert_arn}")
                            else:
                                raise e
                else:
                    print(f"The certificate {cert_arn} is not in use by any load balancer.")
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            error_message = e.response.get("Error", {}).get("Message")
            print(f"Error occurred in region {region}: {error_code} - {error_message}")
