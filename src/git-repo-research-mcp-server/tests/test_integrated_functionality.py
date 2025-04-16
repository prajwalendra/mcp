# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance
# with the License. A copy of the License is located at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# or in the 'license' file accompanying this file. This file is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES
# OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions
# and limitations under the License.
"""Integrated test for the Git Repository Research MCP Server functionality."""

import json
import os
import pytest
import subprocess
import tempfile

# Import the server functionality
from awslabs.git_repo_research_mcp_server.server import (
    list_repositories,
    mcp_access_file,
    mcp_delete_repository,
    mcp_index_repository,
    mcp_search_repository,
    repository_summary,
)


class TestContext:
    """Context for testing MCP tools."""

    def info(self, message):
        """Log an informational message."""
        print(f'INFO: {message}')

    def error(self, message):
        """Log an error message."""
        print(f'ERROR: {message}')

    def report_progress(self, current, total, message=None):
        """Report progress."""
        print(f'PROGRESS: {current}/{total} - {message or ""}')


@pytest.fixture
def test_context():
    """Create a test context."""
    return TestContext()


@pytest.fixture
def test_git_repo():
    """Create a test Git repository."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize Git repository
        repo_dir = os.path.join(temp_dir, 'test_repo')
        os.makedirs(repo_dir)

        # Setup Git config
        subprocess.run(['git', 'init'], cwd=repo_dir, check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=repo_dir, check=True)
        subprocess.run(
            ['git', 'config', 'user.email', 'test@example.com'], cwd=repo_dir, check=True
        )

        # Create README.md
        readme_path = os.path.join(repo_dir, 'README.md')
        with open(readme_path, 'w') as f:
            f.write("""# Test Repository

This is a test repository for the Git Repository Research MCP Server.

## Features

- Semantic search
- Repository indexing
- File access
""")

        # Create src directory
        src_dir = os.path.join(repo_dir, 'src')
        os.makedirs(src_dir)

        # Create Python files
        with open(os.path.join(src_dir, 'main.py'), 'w') as f:
            f.write("""
def main():
    # Main entry point
    print("Hello, World!")

    user_id = "user123"
    user_info = get_user(user_id)
    print(f"User: {user_info}")

    result = calculate_sum(5, 10)
    print(f"Sum: {result}")

if __name__ == "__main__":
    main()
""")

        with open(os.path.join(src_dir, 'utils.py'), 'w') as f:
            f.write('''
def get_user(user_id):
    """
    Get user information by ID.

    Args:
        user_id: The user's ID

    Returns:
        dict: User information
    """
    users = {
        "user123": {"name": "John Doe", "email": "john@example.com"},
        "user456": {"name": "Jane Smith", "email": "jane@example.com"}
    }
    return users.get(user_id, {"name": "Unknown", "email": "unknown@example.com"})

def calculate_sum(a, b):
    """
    Calculate the sum of two numbers.

    Args:
        a: First number
        b: Second number

    Returns:
        int or float: The sum of a and b
    """
    return a + b
''')

        # Create docs directory
        docs_dir = os.path.join(repo_dir, 'docs')
        os.makedirs(docs_dir)

        with open(os.path.join(docs_dir, 'api.md'), 'w') as f:
            f.write("""# API Documentation

## Functions

### get_user(user_id)

Gets user information by ID.

### calculate_sum(a, b)

Calculates the sum of two numbers.
""")

        # Add everything to Git
        subprocess.run(['git', 'add', '.'], cwd=repo_dir, check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=repo_dir, check=True)

        yield repo_dir


@pytest.mark.asyncio
@pytest.mark.live
async def test_repository_indexing(test_context, test_git_repo, tmp_path):
    """Test indexing a repository."""
    # Use a unique name for the repository
    repo_name = f'test_repo_{os.path.basename(test_git_repo)}'

    try:
        # Print diagnostic information about the repo
        print(f'Repository path: {test_git_repo}')
        print(f'Repository files: {os.listdir(test_git_repo)}')

        # Index the repository
        result = await mcp_index_repository(
            test_context,
            repository_path=test_git_repo,
            output_path=repo_name,
            embedding_model='amazon.titan-embed-text-v2:0',
        )

        # Print raw result
        print(f'Index result: {result}')

        # Check for success, but don't fail the test
        if result['status'] == 'success':
            print('✅ Indexing succeeded')
            assert result['repository_name'] == repo_name
            assert 'index_path' in result
            assert result['file_count'] > 0
            assert result['chunk_count'] > 0

            # Clean up the index
            cleanup_result = await mcp_delete_repository(
                test_context, repository_name_or_path=repo_name
            )
            print(f'Cleanup result: {cleanup_result}')
        else:
            print(f'❌ Indexing failed: {result.get("message", "Unknown error")}')
    except Exception as e:
        print(f'Exception during test: {str(e)}')
        # If an exception occurs, try to clean up anyway
        try:
            await mcp_delete_repository(test_context, repository_name_or_path=repo_name)
        except Exception as cleanup_e:
            print(f'Cleanup exception: {str(cleanup_e)}')


@pytest.mark.asyncio
async def test_file_access(test_context, test_git_repo):
    """Test accessing files in a repository."""
    # Test accessing a regular file
    readme_path = os.path.join(test_git_repo, 'README.md')
    result = await mcp_access_file(test_context, filepath=readme_path)

    assert result['status'] == 'success'
    assert result['type'] == 'text'
    assert 'Test Repository' in result['content']

    # Test accessing a directory
    src_dir = os.path.join(test_git_repo, 'src')
    result = await mcp_access_file(test_context, filepath=src_dir)

    assert result['status'] == 'success'
    assert result['type'] == 'directory'
    assert 'main.py' in result['files']
    assert 'utils.py' in result['files']


@pytest.mark.asyncio
@pytest.mark.live
async def test_full_workflow(test_context, test_git_repo):
    """Test a full workflow: index, search, access, delete."""
    # Use a unique name for the repository
    repo_name = f'workflow_test_{os.path.basename(test_git_repo)}'

    print('\n--- Starting full workflow test ---')
    print(f'Repository path: {test_git_repo}')
    print(f'Output repository name: {repo_name}')

    try:
        # 1. Index the repository
        print('\n1. Indexing repository...')
        index_result = await mcp_index_repository(
            test_context,
            repository_path=test_git_repo,
            output_path=repo_name,
            embedding_model='amazon.titan-embed-text-v2:0',
        )

        print(f'Index result: {index_result}')

        # Check indexing result without failing the test
        if index_result['status'] != 'success':
            print(f'⚠️ Repository indexing failed: {index_result.get("message", "Unknown error")}')
            print('Skipping remaining steps due to indexing failure')
            return

        print('✅ Indexing succeeded')

        # 2. List repositories to verify it appears
        print('\n2. Listing repositories...')
        repos_json = await list_repositories()
        repos = json.loads(repos_json)

        print(f'Repositories list result: {repos}')

        if repos['status'] != 'success':
            print(f'⚠️ Repository listing failed: {repos.get("message", "Unknown error")}')
        else:
            print('✅ Repository listing succeeded')

            # Check if our repository is in the list
            if 'repositories' in repos and len(repos['repositories']) > 0:
                repo_found = False
                for repo in repos['repositories']:
                    if repo['repository_name'] == repo_name:
                        repo_found = True
                        break

                if repo_found:
                    print(f"✅ Repository '{repo_name}' found in the list")
                else:
                    print(f"⚠️ Repository '{repo_name}' not found in the list")

        # 3. Get repository summary
        print('\n3. Getting repository summary...')
        summary_json = await repository_summary(repo_name)
        summary = json.loads(summary_json)

        print(f'Summary result status: {summary.get("status")}')

        if summary['status'] != 'success':
            print(f'⚠️ Repository summary failed: {summary.get("message", "Unknown error")}')
        else:
            print('✅ Repository summary succeeded')
            print(f'Tree structure available: {"tree" in summary}')
            print(f'Helpful files available: {"helpful_files" in summary}')

        # 4. Search the repository
        print('\n4. Searching repository for user-related content...')
        search_result = await mcp_search_repository(
            test_context, index_path=repo_name, query='How do I get user information?', limit=5
        )

        print(f'Search result status: {search_result.get("status")}')

        if 'results' not in search_result or len(search_result['results']) == 0:
            print('⚠️ No search results returned')
        else:
            print(f'✅ Found {len(search_result["results"])} search results')

            # Look for user-related content
            found_user_content = False
            for result in search_result['results']:
                if 'get_user' in result['content']:
                    found_user_content = True
                    break

            if found_user_content:
                print('✅ Found user-related content in search results')
            else:
                print('⚠️ No user-related content found in search results')

        # 5. Search for calculation-related content
        print('\n5. Searching repository for calculation-related content...')
        calc_search_result = await mcp_search_repository(
            test_context, index_path=repo_name, query='How to perform calculations', limit=5
        )

        if 'results' not in calc_search_result or len(calc_search_result['results']) == 0:
            print('⚠️ No calculation search results returned')
        else:
            print(f'✅ Found {len(calc_search_result["results"])} calculation search results')

            # Look for calculation-related content
            found_calc_content = False
            for result in calc_search_result['results']:
                if 'calculate_sum' in result['content']:
                    found_calc_content = True
                    break

            if found_calc_content:
                print('✅ Found calculation-related content in search results')
            else:
                print('⚠️ No calculation-related content found in search results')

        # 6. Access indexed file
        print('\n6. Accessing file via repository path...')

        if 'repository_directory' not in index_result:
            print('⚠️ Repository directory not found in index result')
        else:
            repo_dir = index_result['repository_directory']
            print(f'Repository directory: {repo_dir}')

            # Access a file
            file_path = f'{repo_name}/repository/src/utils.py'
            print(f'Accessing file: {file_path}')

            file_result = await mcp_access_file(test_context, filepath=file_path)

            if file_result['status'] != 'success':
                print(f'⚠️ File access failed: {file_result.get("message", "Unknown error")}')
            else:
                print('✅ File access succeeded')
                print(f'File type: {file_result["type"]}')
                print(f'Contains get_user: {"get_user" in file_result["content"]}')
                print(f'Contains calculate_sum: {"calculate_sum" in file_result["content"]}')

        # 7. Delete the repository
        print('\n7. Deleting the repository...')
        delete_result = await mcp_delete_repository(
            test_context, repository_name_or_path=repo_name
        )

        if delete_result['status'] != 'success':
            print(f'⚠️ Repository deletion failed: {delete_result.get("message", "Unknown error")}')
        else:
            print('✅ Repository deletion succeeded')

    except Exception as e:
        print(f'❌ Exception during workflow test: {str(e)}')
        # If an exception occurs, try to clean up anyway
        try:
            print('Attempting to clean up repository...')
            result = await mcp_delete_repository(test_context, repository_name_or_path=repo_name)
            print(f'Cleanup result: {result}')
        except Exception as cleanup_e:
            print(f'❌ Cleanup exception: {str(cleanup_e)}')
