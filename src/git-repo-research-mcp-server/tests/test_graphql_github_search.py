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
"""Tests for GitHub GraphQL search functionality in the Git Repository Research MCP Server."""

import asyncio
import os
import pytest
import requests
import time
from unittest.mock import MagicMock, patch, AsyncMock

# Import the GitHub search functionality
from awslabs.git_repo_research_mcp_server.github_search import (
    github_graphql_request,
    github_repo_search_graphql,
    github_repo_search_wrapper,
)
from awslabs.git_repo_research_mcp_server.server import mcp_search_github_repos


class MockContext:
    """Mock context for testing."""

    def info(self, message):
        """Mock info method."""
        print(f'Info: {message}')

    def error(self, message):
        """Mock error method."""
        print(f'Error: {message}')


@pytest.fixture
def mock_graphql_response():
    """Create a mock GraphQL response."""
    return {
        "data": {
            "search": {
                "repositoryCount": 2,
                "edges": [
                    {
                        "node": {
                            "nameWithOwner": "awslabs/mcp",
                            "name": "mcp",
                            "owner": {
                                "login": "awslabs"
                            },
                            "url": "https://github.com/awslabs/mcp",
                            "description": "Model Context Protocol (MCP) is a protocol for communication between LLMs and tools.",
                            "stargazerCount": 100,
                            "updatedAt": "2023-01-01T00:00:00Z",
                            "primaryLanguage": {
                                "name": "Python"
                            },
                            "repositoryTopics": {
                                "nodes": [
                                    {
                                        "topic": {
                                            "name": "llm"
                                        }
                                    },
                                    {
                                        "topic": {
                                            "name": "ai"
                                        }
                                    }
                                ]
                            },
                            "licenseInfo": {
                                "name": "Apache License 2.0"
                            },
                            "forkCount": 20,
                            "openIssues": {
                                "totalCount": 5
                            },
                            "homepageUrl": "https://mcp.ai"
                        }
                    },
                    {
                        "node": {
                            "nameWithOwner": "aws-samples/aws-cdk-examples",
                            "name": "aws-cdk-examples",
                            "owner": {
                                "login": "aws-samples"
                            },
                            "url": "https://github.com/aws-samples/aws-cdk-examples",
                            "description": "Example projects using the AWS CDK",
                            "stargazerCount": 50,
                            "updatedAt": "2023-02-01T00:00:00Z",
                            "primaryLanguage": {
                                "name": "TypeScript"
                            },
                            "repositoryTopics": {
                                "nodes": [
                                    {
                                        "topic": {
                                            "name": "aws"
                                        }
                                    },
                                    {
                                        "topic": {
                                            "name": "cdk"
                                        }
                                    }
                                ]
                            },
                            "licenseInfo": {
                                "name": "MIT License"
                            },
                            "forkCount": 10,
                            "openIssues": {
                                "totalCount": 3
                            },
                            "homepageUrl": None
                        }
                    }
                ]
            }
        }
    }


@pytest.fixture
def mock_error_response():
    """Create a mock error response."""
    return {
        "errors": [
            {
                "message": "API rate limit exceeded",
                "type": "RATE_LIMITED"
            }
        ]
    }


def test_github_graphql_request_with_token(mock_graphql_response):
    """Test GitHub GraphQL request with a token."""
    with patch('requests.post') as mock_post:
        # Configure the mock
        mock_response = MagicMock()
        mock_response.json.return_value = mock_graphql_response
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Call the function with a token
        result = github_graphql_request(
            query="test query",
            variables={"test": "variable"},
            token="test_token"
        )

        # Verify the result
        assert result == mock_graphql_response
        
        # Verify the request was made with the correct parameters
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs['headers']['Authorization'] == 'Bearer test_token'
        assert kwargs['json']['query'] == "test query"
        assert kwargs['json']['variables'] == {"test": "variable"}


def test_github_graphql_request_without_token(mock_graphql_response):
    """Test GitHub GraphQL request without a token."""
    with patch('requests.post') as mock_post:
        # Configure the mock
        mock_response = MagicMock()
        mock_response.json.return_value = mock_graphql_response
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Call the function without a token
        result = github_graphql_request(
            query="test query",
            variables={"test": "variable"},
            token=None
        )

        # Verify the result
        assert result == mock_graphql_response
        
        # Verify the request was made with the correct parameters
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert 'Authorization' not in kwargs['headers']
        assert kwargs['json']['query'] == "test query"
        assert kwargs['json']['variables'] == {"test": "variable"}


def test_github_graphql_request_rate_limit_handling():
    """Test GitHub GraphQL request rate limit handling."""
    with patch('requests.post') as mock_post, \
         patch('time.sleep') as mock_sleep:
        # Configure the mock for rate limit response
        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 403
        rate_limit_response.text = "API rate limit exceeded"
        rate_limit_response.headers = {"X-RateLimit-Reset": str(int(time.time()) + 10)}
        
        # Configure the mock for success response after rate limit
        success_response = MagicMock()
        success_response.json.return_value = {"data": {"success": True}}
        success_response.status_code = 200
        
        # Set up the mock to return rate limit first, then success
        mock_post.side_effect = [rate_limit_response, success_response]

        # Call the function with a token (should retry after rate limit)
        result = github_graphql_request(
            query="test query",
            variables={"test": "variable"},
            token="test_token"
        )

        # Verify the result is from the second (successful) call
        assert result == {"data": {"success": True}}
        
        # Verify sleep was called for rate limiting
        mock_sleep.assert_called_once()
        
        # Verify post was called twice (initial + retry)
        assert mock_post.call_count == 2


def test_github_graphql_request_error_handling():
    """Test GitHub GraphQL request error handling."""
    with patch('requests.post') as mock_post:
        # Configure the mock to raise an exception
        mock_post.side_effect = requests.exceptions.RequestException("Test error")

        # Call the function and verify it raises the exception
        with pytest.raises(requests.exceptions.RequestException) as excinfo:
            github_graphql_request(
                query="test query",
                variables={"test": "variable"},
                token="test_token"
            )
        
        assert "Test error" in str(excinfo.value)


def test_github_repo_search_graphql(mock_graphql_response):
    """Test GitHub repository search using GraphQL."""
    with patch('awslabs.git_repo_research_mcp_server.github_search.github_graphql_request') as mock_request:
        # Configure the mock
        mock_request.return_value = mock_graphql_response

        # Call the function
        results = github_repo_search_graphql(
            keywords=["test", "repo"],
            organizations=["awslabs", "aws-samples"],
            num_results=2,
            token="test_token"
        )

        # Verify the results
        assert len(results) == 2
        
        # Check first result
        assert results[0]['url'] == "https://github.com/awslabs/mcp"
        assert results[0]['title'] == "awslabs/mcp"
        assert results[0]['description'] == "Model Context Protocol (MCP) is a protocol for communication between LLMs and tools."
        assert results[0]['organization'] == "awslabs"
        assert results[0]['stars'] == 100
        assert results[0]['language'] == "Python"
        assert "llm" in results[0]['topics']
        assert "ai" in results[0]['topics']
        assert results[0]['license'] == "Apache License 2.0"
        assert results[0]['forks'] == 20
        assert results[0]['open_issues'] == 5
        assert results[0]['homepage'] == "https://mcp.ai"
        
        # Check second result
        assert results[1]['url'] == "https://github.com/aws-samples/aws-cdk-examples"
        assert results[1]['title'] == "aws-samples/aws-cdk-examples"
        assert results[1]['organization'] == "aws-samples"


def test_github_repo_search_graphql_with_license_filter(mock_graphql_response):
    """Test GitHub repository search with license filter."""
    with patch('awslabs.git_repo_research_mcp_server.github_search.github_graphql_request') as mock_request:
        # Configure the mock
        mock_request.return_value = mock_graphql_response

        # Call the function with license filter that matches only the first repo
        results = github_repo_search_graphql(
            keywords=["test", "repo"],
            organizations=["awslabs", "aws-samples"],
            num_results=2,
            token="test_token",
            license_filter=["Apache License 2.0"]
        )

        # Verify only one result is returned (the one with Apache License)
        assert len(results) == 1
        assert results[0]['url'] == "https://github.com/awslabs/mcp"
        assert results[0]['license'] == "Apache License 2.0"


def test_github_repo_search_graphql_with_errors(mock_error_response):
    """Test GitHub repository search with API errors."""
    with patch('awslabs.git_repo_research_mcp_server.github_search.github_graphql_request') as mock_request:
        # Configure the mock to return an error response
        mock_request.return_value = mock_error_response

        # Call the function
        results = github_repo_search_graphql(
            keywords=["test", "repo"],
            organizations=["awslabs", "aws-samples"],
            num_results=2,
            token="test_token"
        )

        # Verify empty results are returned on error
        assert len(results) == 0


@pytest.mark.asyncio
@pytest.mark.github
async def test_mcp_search_github_repos_with_token():
    """Test the MCP server function for searching GitHub repositories with a token."""
    # Skip if no GitHub token is available
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        pytest.skip('Skipping test that requires GITHUB_TOKEN')
    
    ctx = MockContext()
    
    # Test with real token but mock the underlying function
    with patch('awslabs.git_repo_research_mcp_server.github_search.github_repo_search_wrapper') as mock_search:
        # Configure the mock to return sample results
        mock_search.return_value = [
            {
                'url': 'https://github.com/awslabs/mcp',
                'title': 'awslabs/mcp',
                'description': 'Model Context Protocol',
                'organization': 'awslabs',
                'stars': 100,
                'updated_at': '2023-01-01T00:00:00Z',
                'language': 'Python',
                'topics': ['llm', 'ai'],
                'license': 'Apache License 2.0',
                'forks': 20,
                'open_issues': 5,
                'homepage': 'https://mcp.ai'
            }
        ]
        
        # Call the MCP server function
        result = await mcp_search_github_repos(
            ctx,
            keywords=['mcp', 'protocol'],
            num_results=5
        )
        
        # Verify the result structure
        assert result['status'] == 'success'
        assert result['query'] == 'mcp protocol'
        assert len(result['results']) == 1
        assert result['total_results'] == 1
        assert 'execution_time_ms' in result
        
        # Verify the result content
        repo = result['results'][0]
        assert repo['url'] == 'https://github.com/awslabs/mcp'
        assert repo['title'] == 'awslabs/mcp'
        assert repo['organization'] == 'awslabs'
        assert repo['stars'] == 100
        assert repo['language'] == 'Python'
        
        # Verify the search wrapper was called with correct parameters
        mock_search.assert_called_once()
        args, kwargs = mock_search.call_args
        assert kwargs['keywords'] == ['mcp', 'protocol']
        assert kwargs['num_results'] == 5
        assert 'organizations' in kwargs
        assert 'aws-samples' in kwargs['organizations']
        assert 'awslabs' in kwargs['organizations']


@pytest.mark.asyncio
async def test_mcp_search_github_repos_without_token():
    """Test the MCP server function for searching GitHub repositories without a token."""
    ctx = MockContext()
    
    # Temporarily remove GITHUB_TOKEN from environment
    original_token = os.environ.get('GITHUB_TOKEN')
    if 'GITHUB_TOKEN' in os.environ:
        del os.environ['GITHUB_TOKEN']
    
    try:
        # Mock the underlying function
        with patch('awslabs.git_repo_research_mcp_server.github_search.github_repo_search_wrapper') as mock_search, \
             patch('awslabs.git_repo_research_mcp_server.server.github_repo_search_wrapper', new=mock_search):
            # Configure the mock to return sample results
            mock_search.return_value = [
                {
                    'url': 'https://github.com/awslabs/mcp',
                    'title': 'awslabs/mcp',
                    'description': 'Model Context Protocol',
                    'organization': 'awslabs',
                    'stars': 100,
                    'updated_at': '2023-01-01T00:00:00Z',
                    'language': 'Python',
                    'topics': ['llm', 'ai'],
                    'license': 'Apache License 2.0',
                    'forks': 20,
                    'open_issues': 5,
                    'homepage': 'https://mcp.ai'
                }
            ]
            
            # Call the MCP server function
            result = await mcp_search_github_repos(
                ctx,
                keywords=['mcp', 'protocol'],
                num_results=5
            )
            
            # Verify the result
            assert result['status'] == 'success'
            assert len(result['results']) == 1
            
            # Verify the search wrapper was called (should use REST API without token)
            mock_search.assert_called_once()
    
    finally:
        # Restore original token if it existed
        if original_token is not None:
            os.environ['GITHUB_TOKEN'] = original_token


@pytest.mark.asyncio
async def test_mcp_search_github_repos_error_handling():
    """Test error handling in the MCP server function for searching GitHub repositories."""
    ctx = MockContext()
    
    # Mock the error method to verify it's called with the error message
    error_mock = AsyncMock()
    ctx.error = error_mock
    
    # We need to directly patch the imported function in the server module with AsyncMock
    with patch('awslabs.git_repo_research_mcp_server.server.github_repo_search_wrapper', 
               new_callable=AsyncMock) as mock_search:
        # Configure the mock to raise an exception
        mock_search.side_effect = Exception("Test error")
        
        # Call the MCP server function and verify it handles the error
        with pytest.raises(Exception) as excinfo:
            await mcp_search_github_repos(
                ctx,
                keywords=['mcp', 'protocol'],
                num_results=5
            )
        
        # Verify the exception contains our error message
        assert "Test error" in str(excinfo.value)
        
        # Verify the error was logged
        error_mock.assert_called_once()
        assert "Test error" in error_mock.call_args[0][0]


if __name__ == '__main__':
    # This allows running the test directly for debugging
    pytest.main(['-xvs', __file__])
