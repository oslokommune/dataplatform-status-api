import pytest
from okdata.resource_auth import ResourceAuthorizer

import test.test_data as test_data


@pytest.fixture()
def mock_auth(monkeypatch):
    def has_access_mock(
        self, bearer_token, scope, resource_name=None, use_whitelist=False
    ):
        return (
            bearer_token == test_data.bearer_token_with_access
            and resource_name.startswith("okdata:dataset:")
            and scope == "okdata:dataset:write"
            and use_whitelist
        )

    monkeypatch.setattr(ResourceAuthorizer, "has_access", has_access_mock)
