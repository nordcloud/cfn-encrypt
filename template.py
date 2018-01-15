import os

from awacs.aws import Policy, Allow, Statement, Principal, Action
from cfn_encrypt import Encrypt, EncryptionContext, SecureParameter
from troposphere import (Template, iam, GetAtt, Join, Ref, logs, Output, Sub, Parameter, awslambda,
                         Base64, Export)

t = Template()

kms_key_arn = t.add_parameter(Parameter(
    "KmsKeyArn",
    Type="String",
    Description="KMS alias ARN for lambda",
    Default="arn:aws:kms:eu-central-1:632826021673:key/df7da78d-4b19-42a3-bc94-acbb8eb22ae6"
))

plain_text = t.add_parameter(Parameter(
    "PlainText",
    Type="String",
    Description="Text that you want to encrypt ( Hello World )",
    Default="Hello World",
    NoEcho=True
))

# Create loggroup
log_group_ssm = t.add_resource(logs.LogGroup(
    "LogGroupSsm",
    LogGroupName=Join("", ["/aws/lambda/", Join("-", [Ref("AWS::StackName"), "ssm"])]),
    RetentionInDays=14
))

log_group_simple = t.add_resource(logs.LogGroup(
    "LogGroupSimple",
    LogGroupName=Join("", ["/aws/lambda/", Join("-", [Ref("AWS::StackName"), "simple"])]),
    RetentionInDays=14
))


def lambda_from_file(python_file):
    """
    Reads a python file and returns a awslambda.Code object
    :param python_file:
    :return:
    """
    lambda_function = []
    with open(python_file, 'r') as f:
        lambda_function.extend(f.read().splitlines())

    return awslambda.Code(ZipFile=(Join('\n', lambda_function)))


kms_policy = iam.Policy(
    PolicyName="encrypt",
    PolicyDocument=Policy(
        Version="2012-10-17",
        Statement=[
            Statement(
                Effect=Allow,
                Action=[
                    Action("kms", "Encrypt"),
                ],
                Resource=[Ref(kms_key_arn)]
            )
        ],
    )
)

ssm_policy = iam.Policy(
    PolicyName="ssm",
    PolicyDocument=Policy(
        Version="2012-10-17",
        Statement=[
            Statement(
                Effect=Allow,
                Action=[
                    Action("ssm", "PutParameter"),
                    Action("ssm", "DeleteParameter"),
                ],
                Resource=[Join("", ["arn:aws:ssm:", Ref("AWS::Region"), ":", Ref("AWS::AccountId"), ":parameter/*"])]
            ),
            Statement(
                Effect=Allow,
                Action=[
                    Action("ssm", "DescribeParameters")
                ],
                Resource=["*"]
            )
        ],
    )
)
encrypt_lambda_role = t.add_resource(iam.Role(
    "EncryptLambdaRole",
    AssumeRolePolicyDocument=Policy(
        Version="2012-10-17",
        Statement=[
            Statement(
                Effect=Allow,
                Principal=Principal("Service", "lambda.amazonaws.com"),
                Action=[Action("sts", "AssumeRole")]
            )
        ]),
    Path="/",
    ManagedPolicyArns=["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"],
    Policies=[
        kms_policy
    ]
))

ssm_lambda_role = t.add_resource(iam.Role(
    "SsmLambdaRole",
    AssumeRolePolicyDocument=Policy(
        Version="2012-10-17",
        Statement=[
            Statement(
                Effect=Allow,
                Principal=Principal("Service", "lambda.amazonaws.com"),
                Action=[Action("sts", "AssumeRole")]
            )
        ]),
    Path="/",
    ManagedPolicyArns=["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"],
    Policies=[
        kms_policy,
        ssm_policy
    ]
))

simple_encrypt_filename = os.path.join(os.path.dirname(__file__), "cfn_encrypt/simple_encrypt.py")

ssm_parameter_filename = os.path.join(os.path.dirname(__file__), "cfn_encrypt/ssm_parameter.py")

encrypt_lambda = t.add_resource(awslambda.Function(
    "EncryptLambda",
    FunctionName=Join("-", [Ref("AWS::StackName"), "simple"]),
    DependsOn=[log_group_simple.title],
    Handler="index.handler",
    Role=GetAtt(encrypt_lambda_role, "Arn"),
    Runtime="python2.7",
    Timeout=300,
    MemorySize=1536,
    Code=lambda_from_file(simple_encrypt_filename),
))

ssm_parameter_lambda = t.add_resource(awslambda.Function(
    "SsmParameterLambda",
    FunctionName=Join("-", [Ref("AWS::StackName"), "ssm"]),
    DependsOn=[log_group_ssm.title],
    Handler="index.handler",
    Role=GetAtt(ssm_lambda_role, "Arn"),
    Runtime="python2.7",
    Timeout=300,
    MemorySize=1536,
    Code=lambda_from_file(ssm_parameter_filename),
))

my_encrypted_value = t.add_resource(Encrypt(
    "MyEncryptedValue",
    ServiceToken=GetAtt(encrypt_lambda, "Arn"),
    Base64Data=Base64(Ref(plain_text)),
    KmsKeyArn=Ref(kms_key_arn)
))

my_encrypted_value_with_context = t.add_resource(Encrypt(
    "MyEncryptedValueWithContext",
    ServiceToken=GetAtt(encrypt_lambda, "Arn"),
    Base64Data=Base64(Ref(plain_text)),
    KmsKeyArn=Ref(kms_key_arn),
    EncryptionContext=EncryptionContext(
        Name="Test",
        Value="Test"
    )

))

my_secure_parameter = t.add_resource(SecureParameter(
    "MySecureParameter",
    ServiceToken=GetAtt(ssm_parameter_lambda, "Arn"),
    Name="MySecureParameter",
    Description="Testing secure parameter",
    Value=Ref(plain_text),
    KeyId=Ref(kms_key_arn)
))


t.add_output(Output(
    "MySecureParameter",
    Description="My secure parameter name",
    Value=Ref(my_secure_parameter)
))

t.add_output(Output(
    "EncryptedValue",
    Description="Encrypted value, base64 encoded",
    Value=GetAtt(my_encrypted_value, "CiphertextBase64"),
))

t.add_output(Output(
    "EncryptedValueWithContext",
    Description="Encrypted value, base64 encoded",
    Value=GetAtt(my_encrypted_value_with_context, "CiphertextBase64"),
))

t.add_output(Output(
    "EncryptLambdaArn",
    Description="lambda arn",
    Value=GetAtt(encrypt_lambda, "Arn"),
    Export=Export(
        Sub(
            "${AWS::StackName}-EncryptLambdaArn"
        )
    )
))

t.add_output(Output(
    "SsmParameterLambdaArn",
    Description="kms key arn",
    Value=GetAtt(ssm_parameter_lambda, "Arn"),
    Export=Export(
        Sub(
            "${AWS::StackName}-SsmParameterLambdaArn"
        )
    )
))

print(t.to_json())
