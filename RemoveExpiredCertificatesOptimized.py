import boto3
import datetime

def lambda_handler(event, context):
    def get_all_regions():
        session = boto3.session.Session()
        return session.get_available_regions('acm')

    def get_elb_arn(region):
        client = boto3.client("elbv2", region_name=region)
        response = client.describe_load_balancers()
        elb_arns = [lb["LoadBalancerArn"] for lb in response["LoadBalancers"]]
        return elb_arns

    def publish_to_sns(topic_arn, subject, message):
        sns_client = boto3.client('sns')
        sns_client.publish(TopicArn=topic_arn, Subject=subject, Message=message)

    regions = get_all_regions()
    deleted_certs = []
    expired_certs = []
    topic_name = "OpsGenie-OpsTeam"
    error_messages = []

    sns_client = boto3.client('sns')
    topic_arn = ""
    response = sns_client.list_topics()

    for topic in response['Topics']:
        if topic['TopicArn'].endswith(':' + topic_name):
            topic_arn = topic['TopicArn']
            break

    if not topic_arn:
        print(f"SNS topic '{topic_name}' not found. Unable to publish failure message.")
        return

    for region in regions:
        # Clear the expired_certs list before each region is iterated over.
        expired_certs.clear()

        client = boto3.client("acm", region_name=region)
        paginator = client.get_paginator("list_certificates")

        try:
            for response in paginator.paginate():
                for cert in response["CertificateSummaryList"]:
                    cert_arn = cert["CertificateArn"]
                    cert_detail = client.describe_certificate(CertificateArn=cert_arn)
                    expiration_date = cert_detail["Certificate"]["NotAfter"]
                    now = datetime.datetime.now(datetime.timezone.utc)

                    if expiration_date < now:
                        expired_certs.append(cert_arn)

            if expired_certs:
                for cert_arn in expired_certs:
                    if cert_arn in deleted_certs:
                        print(f"The certificate {cert_arn} has been deleted.")
                    else:
                        print(f"The certificate {cert_arn} has expired on {expiration_date}. Deleting...")
                        # Comment the following line for testing without deleting certificates
                        client.delete_certificate(CertificateArn=cert_arn)
                        deleted_certs.append(cert_arn)
            else:
                # Only print this message if no certificates have been deleted.
                if not deleted_certs:
                    print("No expired certificates found.")
        except Exception as e:
            error_message = f"An error occurred while processing region {region}: {e}"
            print(error_message)
            if isinstance(e, boto3.exceptions.botocore.client.ClientError) and e.response['Error']['Code'] == 'ResourceInUseException':
                elb_arns = get_elb_arn(region)
                if elb_arns:
                    elb_arns_str = ", ".join(elb_arns)
                    error_message += f" (ELB ARN: {elb_arns_str})"
                error_messages.append(error_message)

    if error_messages:
        subject = "Failed to delete an expired SSL certificate"
        error_message = "\n".join(error_messages)
        publish_to_sns(topic_arn, subject, error_message)
        print(f"Published message to SNS topic: {error_message}")
