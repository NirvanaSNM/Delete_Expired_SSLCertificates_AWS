# Delete_Expired_SSLCertificates_AWS
Cloudformation Template with Lambda Functions to delete Expired SSL Certificates

DetachAndRemoveExpiredCertificates with trigger optimized Template:

This code is an AWS CloudFormation template written in YAML format. It defines a CloudFormation stack that provisions AWS Lambda functions and other related resources to remove expired SSL certificates from the AWS Certificate Manager (ACM) and associated AWS Elastic Load Balancers (ELBs).

1. `AWSTemplateFormatVersion` specifies the version of AWS CloudFormation template format being used.
2. `Description` provides a description of the template.
3. `Resources` section defines the AWS resources to be created.

In the `Resources` section:

- `LambdaACMRole` defines an IAM role for the Lambda functions. It allows the Lambda functions to assume the role and provides necessary permissions to interact with ACM, ELB, CloudWatch Logs, SNS, and IAM.
- `DetachExpiredCerts` is an AWS Lambda function that detaches expired certificates from ELB listeners. It uses the Python runtime and contains code that iterates over regions, lists certificates, and removes the expired ones from associated ELB listeners.
- `RemoveExpiredCerts` is another AWS Lambda function that removes expired certificates from the ACM. It also uses the Python runtime and contains code that iterates over regions, lists certificates, and deletes the expired ones.
- `DetachExpiredCertsRule` is an AWS Events rule that triggers the `DetachExpiredCerts` Lambda function on a scheduled basis. It is scheduled to run once a month (`cron(0 0 1 * ? *)`).
- `InvokeDetachLambdaPermission` grants permission to the AWS Events service to invoke the `DetachExpiredCerts` Lambda function.
- `DetachExpiredCertsEventInvokeConfig` configures an event invoke configuration for the `DetachExpiredCerts` Lambda function. It specifies the destination (the `RemoveExpiredCerts` Lambda function) to which the function's success and failure events are sent.

Each Lambda function has properties defined, such as its code, description, handler (entry point), runtime, memory size, timeout, role (the `LambdaACMRole`), and function name.

The code within the Lambda functions uses the Boto3 library to interact with AWS services. The `DetachExpiredCerts` function iterates over regions, retrieves certificate information, checks for expiration, and removes certificates from ELB listeners if they are expired. The `RemoveExpiredCerts` function also iterates over regions, retrieves certificate information, checks for expiration, and deletes expired certificates from ACM.

Overall, this CloudFormation template sets up a scheduled task to regularly remove expired certificates from ACM and ELB listeners using Lambda functions and other related resources.

------------------
DetachExpiredCertificatesFromListenersOptimized Function:
Lambda function that checks for expired SSL/TLS certificates in the AWS Certificate Manager (ACM) and removes them from the listeners of the associated Elastic Load Balancers (ELBs).

Code Analysis

Inputs
event: The event data passed to the Lambda function.
context: The runtime information of the Lambda function.

Flow
The code initializes a session and retrieves the available regions for the ACM service.
It then iterates over each region.
For each region, it clears the list of expired certificates.
It creates an ACM client and a paginator to retrieve the list of certificates.
It checks the expiration date of each certificate and adds the ARN of expired certificates to the expired_certs list.
For each expired certificate, it retrieves the details and checks if it is in use by any load balancer.
If the certificate is in use, it retrieves the load balancer's ARN and removes the certificate from its listeners.
If the certificate is not in use, it prints a message indicating that it is not in use.
If any errors occur during the process, it prints an error message with the corresponding region and error code.

Outputs
The code snippet prints messages indicating the status of each certificate and its removal from the load balancer listeners.

---------------
RemoveExpiredCertificatesOptimized Funtion:
Lambda function that checks for expired SSL certificates in AWS ACM (Amazon Certificate Manager) and deletes them if necessary. It also publishes a failure message to an SNS (Simple Notification Service) topic if any errors occur during the process.

Code Analysis

Inputs
event: The event data passed to the Lambda function.
context: The runtime information of the Lambda function.

Flow
The code defines three helper functions: get_all_regions(), get_elb_arn(region), and publish_to_sns(topic_arn, subject, message).
It retrieves the available regions using the get_all_regions() function.
It initializes some variables, including deleted_certs, expired_certs, topic_name, and error_messages.
It retrieves the ARN of the SNS topic specified by topic_name.
It iterates over each region and clears the expired_certs list.
For each region, it retrieves the ACM client and paginator.
It paginates through the list of certificates in ACM and checks if any of them have expired.
If an expired certificate is found, it checks if it has already been deleted. If not, it deletes the certificate using the ACM client and adds it to the deleted_certs list.
If no certificates have been deleted, it prints a message indicating that no expired certificates were found.
If any errors occur during the process, it captures the error message and appends it to the error_messages list.
If there are any error messages, it publishes a failure message to the SNS topic with the details.
It prints a message indicating that the failure message has been published.

Outputs
The code prints messages indicating the status of the certificate deletion process and the publishing of the failure message.

