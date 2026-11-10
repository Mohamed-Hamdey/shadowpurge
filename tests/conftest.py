import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch


@pytest.fixture
def mock_platforms():
    return [
        {
            "name": "TestPlatform",
            "url_template": "https://test.com/{}",
            "category": "Social",
            "deletion_url": "https://test.com/delete",
            "removal_instructions": "Go to settings and click delete",
            "automation_supported": True
        },
        {
            "name": "AnotherPlatform",
            "url_template": "https://another.com/user/{}",
            "category": "Developer",
            "deletion_url": "https://another.com/settings/delete",
            "removal_instructions": "Contact support",
            "automation_supported": False
        }
    ]


@pytest.fixture
def sample_username():
    return "testuser123"


@pytest.fixture
def sample_email():
    return "testuser@example.com"


@pytest.fixture
def sample_phone():
    return "+15551234567"