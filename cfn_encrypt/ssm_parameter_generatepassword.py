import cfnresponse, logging, traceback, boto3, random, string
from random import choice
from string import ascii_uppercase, ascii_lowercase, digits


def parameter_exist(name):
    response = boto3.client('ssm').describe_parameters(
        ParameterFilters=[{
            'Key': 'Name',
            'Values': [
                name
            ]
        }]
    )
    return len(response["Parameters"]) > 0


def handler(event, context):
    logger = logging.getLogger("crypto_cfn")
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    logger.addHandler(ch)
    name = event["ResourceProperties"]["Name"]
    try:

        if event["RequestType"] in ["Create", "Update"]:
            if event["RequestType"] == "Create" and parameter_exist(name):
                raise NameError("A Parameter named {} already exists".format(name))

            if not event["ResourceProperties"]["Length"]:
                raise ValueError("The Resource property Length is requried")

            try:
                password_length = int(event["ResourceProperties"]["Length"])
            except:
                raise ValueError("The Resource property Length must be an integer or castable to an integer")


            charset = ascii_uppercase + ascii_lowercase + digits
            if event["ResourceProperties"]["WithSpecialCharacters"] in ['true', 'True', '1', True, 1]:
                charset = charset + "!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"

            password = ''.join(choice(charset) for i in range(password_length))

            response = boto3.client('ssm').put_parameter(
                Name=name,
                Description=event["ResourceProperties"]["Description"],
                Value=password,
                Type="SecureString",
                KeyId=event["ResourceProperties"]["KeyId"],
                Overwrite=True
            )

            logger.info("Successfully stored parameter {}".format(name))

            cfnresponse.send(event, context, cfnresponse.SUCCESS, response, name)
        else:
            boto3.client('ssm').delete_parameter(
                Name=event["PhysicalResourceId"],
            )
            logger.info("Successfully deleted parameter: {}".format(name))
            cfnresponse.send(event, context, cfnresponse.SUCCESS, None, name)

    except Exception as ex:
        logger.error("Failed to %s parameter: %s", event["RequestType"], name)
        logger.debug("Stack trace %s", traceback.format_exc())
        if event["RequestType"] in ["Create", "Update"]:
            cfnresponse.send(event, context, cfnresponse.FAILED, None, "0")
        else:
            cfnresponse.send(event, context, cfnresponse.SUCCESS, None, "0")
