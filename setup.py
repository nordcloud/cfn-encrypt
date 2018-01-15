try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

REQUIREMENTS = [i.strip() for i in open("requirements.txt").readlines()]
setup(
    name="cfn_encrypt",
    version="0.0.10",
    description="Lambda cloudformation custom resource that use KMS encrypt",
    long_description=open("README.md").read(),
    author="Martin Kaberg",
    author_email="martin.kaberg@nordcloud.com",
    url="https://bitbucket.org/nordcloud/cfn_encrypt",
    packages=["cfn_encrypt"],
    install_requires=REQUIREMENTS,
    license = "Apache Common 2.0",
    zip_safe=False,

)
