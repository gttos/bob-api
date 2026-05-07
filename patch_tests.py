import re

with open('tests/unit/test_image_use_cases.py', 'r') as f:
    content = f.read()

# Add mock_space_repo fixture
fixture = """@pytest.fixture
def mock_space_repo():
    repo = AsyncMock()
    return repo

@pytest.fixture"""
content = content.replace('@pytest.fixture\ndef mock_thumbnail_service()', fixture + '\ndef mock_thumbnail_service()')

# Update test definitions to include mock_space_repo
content = content.replace('(mock_image_repo, mock_project_repo, mock_storage, mock_thumbnail_service)', '(mock_image_repo, mock_project_repo, mock_space_repo, mock_storage, mock_thumbnail_service)')

# Update UploadImageUseCase instantiation
content = content.replace('project_repo=mock_project_repo,', 'project_repo=mock_project_repo,\n        space_repo=mock_space_repo,')

with open('tests/unit/test_image_use_cases.py', 'w') as f:
    f.write(content)
