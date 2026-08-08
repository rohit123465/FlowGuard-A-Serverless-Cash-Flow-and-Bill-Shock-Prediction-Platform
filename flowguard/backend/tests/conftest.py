from __future__ import annotations

import json
import secrets
import string
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

import boto3
import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("flowguard-aws")
    group.addoption(
        "--run-aws-tests",
        action="store_true",
        help="Run integration and system tests against the deployed AWS stack.",
    )
    group.addoption("--aws-profile", default="flowguard-dev")
    group.addoption("--aws-region", default="eu-west-2")
    group.addoption("--stack-name", default="flowguard-dev")


@dataclass(frozen=True)
class ApiResponse:
    status: int
    body: dict[str, Any] | None


class ApiClient:
    def __init__(self, base_url: str, access_token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        expected_status: int = 200,
    ) -> ApiResponse:
        headers = {"Authorization": f"Bearer {self.access_token}"}
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode("utf-8")

        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                status = response.status
                raw_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            status = error.code
            raw_body = error.read().decode("utf-8")

        parsed_body = json.loads(raw_body) if raw_body else None
        assert status == expected_status, (
            f"{method} {path} returned {status}, expected {expected_status}: "
            f"{raw_body}"
        )
        return ApiResponse(status=status, body=parsed_body)


@dataclass
class AwsTestEnvironment:
    cognito: Any
    user_pool_id: str
    user_pool_client_id: str
    api_url: str
    usernames: list[str]

    def create_user(self, label: str) -> ApiClient:
        unique = f"{int(time.time())}-{secrets.randbelow(1_000_000)}"
        email = f"flowguard-{label}-{unique}@example.com"
        alphabet = string.ascii_letters + string.digits
        password = "Fg!" + "".join(secrets.choice(alphabet) for _ in range(24))

        response = self.cognito.admin_create_user(
            UserPoolId=self.user_pool_id,
            Username=email,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "email_verified", "Value": "true"},
            ],
            MessageAction="SUPPRESS",
            TemporaryPassword=password,
        )
        username = response["User"]["Username"]
        self.usernames.append(username)
        self.cognito.admin_set_user_password(
            UserPoolId=self.user_pool_id,
            Username=username,
            Password=password,
            Permanent=True,
        )
        auth = self.cognito.initiate_auth(
            ClientId=self.user_pool_client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": email, "PASSWORD": password},
        )
        return ApiClient(
            self.api_url,
            auth["AuthenticationResult"]["AccessToken"],
        )


@pytest.fixture(scope="session")
def aws_environment(request: pytest.FixtureRequest) -> AwsTestEnvironment:
    if not request.config.getoption("--run-aws-tests"):
        pytest.skip("use --run-aws-tests to test the deployed AWS stack")

    profile = request.config.getoption("--aws-profile")
    region = request.config.getoption("--aws-region")
    stack_name = request.config.getoption("--stack-name")
    session = boto3.Session(profile_name=profile, region_name=region)
    cloudformation = session.client("cloudformation")
    stack = cloudformation.describe_stacks(StackName=stack_name)["Stacks"][0]
    outputs = {
        output["OutputKey"]: output["OutputValue"]
        for output in stack.get("Outputs", [])
    }
    required = {"HttpApiUrl", "UserPoolId", "UserPoolClientId"}
    assert required <= outputs.keys(), "deployed stack is missing required outputs"

    environment = AwsTestEnvironment(
        cognito=session.client("cognito-idp"),
        user_pool_id=outputs["UserPoolId"],
        user_pool_client_id=outputs["UserPoolClientId"],
        api_url=outputs["HttpApiUrl"],
        usernames=[],
    )
    yield environment

    for username in environment.usernames:
        try:
            environment.cognito.admin_delete_user(
                UserPoolId=environment.user_pool_id,
                Username=username,
            )
        except environment.cognito.exceptions.UserNotFoundException:
            pass


@pytest.fixture
def api_client(aws_environment: AwsTestEnvironment) -> ApiClient:
    return aws_environment.create_user("integration")
