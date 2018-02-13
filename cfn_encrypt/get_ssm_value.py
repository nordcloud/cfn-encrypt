import cfnresponse, logging, traceback, boto3, datetime, json
from dateutil.tz import tzlocal


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


def date_2_string(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()


def handler(event, context):
    logger = logging.getLogger("crypto_cfn")
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    logger.addHandler(ch)
    name = event["ResourceProperties"]["Name"]
    try:

        if event["RequestType"] in ["Create", "Update"]:
            if not parameter_exist(name):
                raise NameError("A Parameter named {} does not exists".format(name))

            response = boto3.client('ssm').get_parameter_history(
                Name=name,
                WithDecryption=True,
            )

            ret_value = None
            if event["ResourceProperties"].get("Version") is not None:
                for param in response["Parameters"]:
                    if param["Version"] == int(event["ResourceProperties"].get("Version")):
                        ret_value = param
                        break
            else:
                ret_value = response["Parameters"][-1]

            if ret_value is None:
                raise LookupError("Parameter not found")
            logger.info("Successfully retrieved parameter {}".format(name))

            cfnresponse.send(event, context, cfnresponse.SUCCESS,
                             json.loads(json.dumps(ret_value, default=date_2_string)),
                             name + str(ret_value["Version"]))
        else:
            cfnresponse.send(event, context, cfnresponse.SUCCESS, None, name)

    except Exception as ex:
        logger.error("Faild get parameter value: %s", name)
        logger.debug("Stack trace %s", traceback.format_exc())
        if event["RequestType"] in ["Create", "Update"]:
            cfnresponse.send(event, context, cfnresponse.FAILED, None, "0")
        else:
            cfnresponse.send(event, context, cfnresponse.SUCCESS, None, "0")
