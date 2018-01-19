
# README #



### What is this repository for? ###

* To encrypt values in cloudformation
* To Create secure ssm parameters in cloudformation
* To Retrieve secure ssm paramters in cloudformation



### What does it do? ###

The repo provides two simple lambda functions
* simple_encrypt.py: exposes the kms encrypt api to cloudformation.
It does this by a custom resource called Encrypt.
* ssm_parameter.py: Makes it possible to create ssm parameters of
type SecureString in cloudformation. It does this by a custom resource
called SecureParameter


#### Encrypt ####

The custom resource expects base64 encoded input and outputs base64
encrypted blob

It supports encryption context

#### SecureParameter ####
Takes name, value, description and KeyId

If the parameter name was not created in this stack update will fail

### How do I get set up? ###

* install the module in via pip
~~~~
  pip install cfn-encrypt
~~~~


### template.py ###
This is the template that provision the lambda function.

It takes two parameters

#### Parameter: KmsKeyArn ####
This is the arn of the kms key you want to use for encryption.  If the
key is located in another AWS account make sure that it allows the
account you create the stack in *Encrypt* action on the key.


#### Parameter: PlainText ####
This is just a string that will test the encryption and secure parameter
functionality.

### If the stack creation fails ###
Check the log group /aws/lambda/*stack name*


### generate the template ###
~~~~
 python template.py > /tmp/encrypt.template
~~~~
* create a stack using `/tmp/encrypt.template`
* Make sure you do not rollback on failure, since that will delete the
log group that might contain valuable information
* Supply the KMS key arn that you want to use, and optionally a value that
you want to encrypt.
* outputs: `KmsKeyArn, LambdaArn, EncryptedValue`
* exports: all outputs are exported and their names are prepended with
the name of the stack



### How do i use it other stacks? ###

Use the example template to provision the lambda function. The example
template will export the arn of the lambdas


##### simple encrypt usage #####
Import the custom resource class
~~~~
from cfn_encrypt import Encrypt, EncryptionContext
~~~~


Create a parameter so you can reference to the template the lambda was
created in
~~~~
encrypt_lambda_stack = t.add_parameter(Parameter(
    "EncryptLambdaStack",
    Type="String",
    Description="Stack name of the encryption lambda"
))
~~~~

Import KmsKeyArn and LambdaArn from the lambda stack
~~~~
kms_key_arn = ImportValue(Sub("${EncryptLambdaStack}-KmsKeyArn"))
lambda_arn = ImportValue(Sub("${EncryptLambdaStack}-EncryptLambdaArn"))
~~~~


Add a parameter for the value you want to encrypt, make sure you set
NoEcho to True
~~~~
my_secret = t.add_parameter(Parameter(
    "MySecret",
    Type="String",
    Description="Enter your secret",
    NoEcho=True
))
~~~~


Invoke the lambda
~~~~
encrypted_secret = t.add_resource(Encrypt(
    "EncryptedSecret",
    ServiceToken=lambda_arn,
    Base64Data=Base64(Ref(my_secret)),
    KmsKeyArn=kms_key_arn
))
~~~~

If you want to use encryption context.
* Note that encryption context should not be sensitive values.
~~~~
 my_encrypted_value_with_context = t.add_resource(Encrypt(
    "MyEncryptedValueWithContext",
    ServiceToken=lambda_arn,
    Base64Data=Base64(Ref(plain_text)),
    KmsKeyArn=kms_key_arn,
    EncryptionContext=EncryptionContext(
        Name="Test",
        Value="Test"
    )
))
~~~~
The the encrypted parameter can be retrieved base64 encoded using GetAtt
~~~~
GetAtt(encrypted_secret, "CiphertextBase64"),
~~~~



#### ssm parameter usage ####

Import the custom resource class
~~~~
from cfn_encrypt import SecureParameter
~~~~


Create a parameter so you can reference to the template the lambda was
created in
~~~~
encrypt_lambda_stack = t.add_parameter(Parameter(
    "EncryptLambdaStack",
    Type="String",
    Description="Stack name of the encryption lambda"
))
~~~~

Import KmsKeyArn and LambdaArn from the lambda stack
~~~~
kms_key_arn = ImportValue(Sub("${EncryptLambdaStack}-KmsKeyArn"))
lambda_arn = ImportValue(Sub("${EncryptLambdaStack}-EncryptLambdaArn"))
~~~~


Add a parameter for the value you want to encrypt, make sure you set
NoEcho to True
~~~~
my_secret = t.add_parameter(Parameter(
    "MySecret",
    Type="String",
    Description="Enter your secret",
    NoEcho=True
))
~~~~


Invoke the lambda
~~~~

my_secure_parameter = t.add_resource(SecureParameter(
    "MySecureParameter",
    ServiceToken=lambda_arn,
    Name="MySecureParameter",
    Description="Testing secure parameter",
    Value=Ref(my_secret),
    KeyId=kms_key_arn
))

~~~~




#### get ssm parameter ####


Import the custom resource class
~~~~
from cfn_encrypt import GetSsmValue
~~~~


Create a parameter so you can reference to the template the lambda was
created in
~~~~
encrypt_lambda_stack = t.add_parameter(Parameter(
    "EncryptLambdaStack",
    Type="String",
    Description="Stack name of the encryption lambda"
))
~~~~

Import KmsKeyArn and LambdaArn from the lambda stack
~~~~
kms_key_arn = ImportValue(Sub("${EncryptLambdaStack}-KmsKeyArn"))
lambda_arn = ImportValue(Sub("${EncryptLambdaStack}-EncryptLambdaArn"))
~~~~




Invoke the lambda
~~~~
my_decrypted_value = t.add_resource(GetSsmValue(
    "MyDecryptedValue",
    ServiceToken=lambda_arn,
    Name="/My/Parameter/Name",
    KeyId=kms_key_arn,
    Version=5 # Optional

))

Use GetAtt  to get information about the parameter
 'Name': 'string',
 'Type': 'String'|'StringList'|'SecureString',
 'KeyId': 'string',
'LastModifiedDate': datetime(2015, 1, 1),
'LastModifiedUser': 'string',
'Description': 'string',
'Value': 'string',
'AllowedPattern': 'string',
'Version': 123

~~~~



### How to contribute and report bugs ###

You can contribute by sending a PR to the repo. 

1. Fork the repository
2. Make changes
3. Issue a PR

Every PR should be backed by an issue requesting a change. 


