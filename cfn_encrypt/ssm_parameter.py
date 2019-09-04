import cfnresponse, logging, traceback, boto3
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
    value = None

    try:
        if event["RequestType"] in ["Create", "Update"]:
            if event["RequestType"] == "Create" and parameter_exist(name):
                raise NameError("A Parameter named {} already exists".format(name))

            generate_password = event["ResourceProperties"]["GeneratePassword"] if "GeneratePassword" in event["ResourceProperties"] else None
            value = event["ResourceProperties"]["Value"] if "Value" in event["ResourceProperties"] else None

            if value and generate_password in ['true', 'True', '1', True, 1]:
                raise ValueError("Property Value and GeneratePassword cannot be used at the same time")

            if generate_password in ['true', 'True', '1', True, 1]:

                password_length = event["ResourceProperties"]["GeneratePasswordLength"] if "GeneratePasswordLength" in event["ResourceProperties"] else None
                allow_specials = event["ResourceProperties"]["GeneratePasswordAllowSpecialCharacters"] if "GeneratePasswordAllowSpecialCharacters" in event["ResourceProperties"] else None
                if not password_length:
                    raise ValueError("The Resource property GeneratePasswordLength is required")

                try:
                    password_length = int(password_length)
                except:
                    raise ValueError("The Resource property GeneratePasswordLength must be an integer or castable to an integer")


                charset = ascii_uppercase + ascii_lowercase + digits
                if allow_specials and allow_specials in ['true', 'True', '1', True, 1]:
                    charset = charset + "!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"

                value = ''.join(choice(charset) for i in range(password_length))

            if not value:
                raise ValueError("Either generate a password or set a value")

            print(value)
            response = boto3.client('ssm').put_parameter(
                Name=name,
                Description=event["ResourceProperties"]["Description"],
                Value=value,
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
