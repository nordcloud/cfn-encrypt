import cfnresponse, logging, traceback, boto3, base64


def handler(event, context):
    logger = logging.getLogger("crypto_cfn")
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    logger.addHandler(ch)
    try:
        args = dict()

        if event["ResourceProperties"].get("EncryptionContext") is not None:
            args["EncryptionContext"] = {
                event["ResourceProperties"].get("EncryptionContext")["Name"]:
                    event["ResourceProperties"].get("EncryptionContext")["Value"]
            }

        args["KeyId"] = event["ResourceProperties"]["KmsKeyArn"]
        args["Plaintext"] = base64.b64decode(event["ResourceProperties"]["Base64Data"])

        if event["RequestType"] in ["Create", "Update"]:
            encrypted = boto3.client('kms').encrypt(**args)
            response = dict()
            response["CiphertextBase64"] = base64.b64encode(encrypted["CiphertextBlob"])
            response["KeyId"] = encrypted["KeyId"]
            cfnresponse.send(event, context, cfnresponse.SUCCESS, response, "1")
            logger.info("Successfully encrypted value")
        else:
            cfnresponse.send(event, context, cfnresponse.SUCCESS, None, "1")
            logger.info("Successfully deleted")

    except Exception as ex:
        logger.error("Faild to encrypt value: %s", ex.message)
        logger.debug("Stack trace %s", traceback.format_exc())

        if event["RequestType"] in ["Create", "Update"]:
            cfnresponse.send(event, context, cfnresponse.FAILED, None, "0")
        else:
            cfnresponse.send(event, context, cfnresponse.SUCCESS, None, "0")
