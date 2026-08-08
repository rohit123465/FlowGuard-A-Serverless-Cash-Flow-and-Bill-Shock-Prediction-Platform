import urllib.error
import urllib.request

import pytest

from tests.conftest import AwsTestEnvironment


pytestmark = [pytest.mark.aws, pytest.mark.system]


def test_api_rejects_requests_without_a_jwt(
    aws_environment: AwsTestEnvironment,
) -> None:
    request = urllib.request.Request(
        f"{aws_environment.api_url.rstrip('/')}/commitments",
        method="GET",
    )
    with pytest.raises(urllib.error.HTTPError) as error:
        urllib.request.urlopen(request, timeout=30)
    assert error.value.code == 401
