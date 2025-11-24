import pytest
from pytest_factoryboy import register
from tests.blog.factories import PostFactory

# Register factories globally
register(PostFactory)

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Global fixture to enable database access for all tests.
    This avoids having to mark every test with @pytest.mark.django_db.
    """
    pass
