from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name="status-api",
    version="0.0.1",
    author="Origo Dataplattform",
    author_email="dataplattform@oslo.kommune.no",
    description="API for managing file upload statuses",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/oslokommune/dataplatform-status-api",
    install_requires=[
        "aws-xray-sdk",
        "boto3",
        "okdata-aws>=0.3.3",
        "okdata-resource-auth",
        "okdata-sdk>=0.9.1",
        "requests",
        "simplejson",
    ],
)
