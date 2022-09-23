#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


from typing import Any, Mapping, Optional, Union

from pydantic import BaseModel, Field

from .auth_methods.default_credentials_spec import DefaultCredentials
from .auth_methods.no_credentials_spec import NoCredentials
from .auth_methods.provided_credentials_spec import ProvidedCredentials
from .source_files_abstract.source import SourceFilesAbstract
from .source_files_abstract.spec import SourceFilesAbstractSpec
from .stream import IncrementalFileStreamS3


class SourceS3Spec(SourceFilesAbstractSpec, BaseModel):

    authentication: Union[DefaultCredentials, ProvidedCredentials, NoCredentials] = Field(
        default="default_credentials",
        title="Authentication Method",
        description="The authentication method to use for accessing the source.",
        order=3,
    )

    @staticmethod
    def change_authentication_to_oneOf(schema: dict) -> dict:
        props_to_change = ["authentication"]
        for prop in props_to_change:
            schema["properties"][prop]["type"] = "object"
            if "oneOf" in schema["properties"][prop]:
                continue
            schema["properties"][prop]["oneOf"] = schema["properties"][prop].pop("anyOf")
        return schema

    @classmethod
    def schema(cls, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """we're overriding the schema classmethod to enable some post-processing"""
        import json

        schema = super().schema(*args, **kwargs)
        print("\n\nPre-Schema: %s\n\n" % json.dumps(schema))
        schema = cls.change_authentication_to_oneOf(schema)
        print("\n\nPost-Schema: %s\n\n" % json.dumps(schema))
        return schema

    class Config:
        title = "S3 Source Spec"

    class S3Provider(BaseModel):
        class Config:
            title = "S3: Amazon Web Services"
            # SourceFilesAbstractSpec field are ordered 10 apart to allow subclasses to insert their own spec's fields interspersed
            schema_extra = {"order": 11, "description": "Use this to load files from S3 or S3-compatible services"}

        bucket: str = Field(description="Name of the S3 bucket where the file(s) exist.", order=0)

        aws_access_key_id: Optional[str] = Field(
            default=None,
            description="In order to access private Buckets stored on AWS S3, this connector requires credentials "
            "with the proper permissions. If accessing publicly available data, this field is not necessary.",
            airbyte_secret=True,
            order=1,
        )
        aws_secret_access_key: Optional[str] = Field(
            default=None,
            description="In order to access private Buckets stored on AWS S3, this connector requires credentials "
            "with the proper permissions. If accessing publicly available data, this field is not necessary.",
            airbyte_secret=True,
            order=2,
        )

        path_prefix: str = Field(
            default="",
            description="By providing a path-like prefix (e.g. myFolder/thisTable/) under which all the relevant files sit, "
            "we can optimize finding these in S3. This is optional but recommended if your bucket contains many "
            "folders/files which you don't need to replicate.",
            order=3,
        )

        endpoint: str = Field("", description="Endpoint to an S3 compatible service. Leave empty to use AWS.", order=4)
        use_ssl: bool = Field(
            default=None,
            title="Use TLS",
            description="Whether the remote server is using a secure SSL/TLS connection. Only relevant if using an S3-compatible, "
            "non-AWS server",
            order=5,
        )
        verify_ssl_cert: bool = Field(
            default=None,
            title="Verify TLS Certificates",
            description="Set this to false to allow self signed certificates. Only relevant if using an S3-compatible, non-AWS server",
            order=6,
        )

    provider: S3Provider


class SourceS3(SourceFilesAbstract):
    stream_class = IncrementalFileStreamS3
    spec_class = SourceS3Spec
    documentation_url = "https://docs.airbyte.io/integrations/sources/s3"

    def read_config(self, config_path: str) -> Mapping[str, Any]:
        config: Mapping[str, Any] = super().read_config(config_path)
        if config.get("format", {}).get("delimiter") == r"\t":
            config["format"]["delimiter"] = "\t"
        return config
