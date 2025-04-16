"""Embeddings generation for Git Repository Research MCP Server.

This module provides functionality for generating embeddings from text
using AWS Bedrock models via LangChain.
"""

import os
from awslabs.git_repo_research_mcp_server.models import EmbeddingModel
from langchain_aws import BedrockEmbeddings
from loguru import logger
from typing import List, Optional


class EmbeddingGenerator:
    """Generator for text embeddings using AWS Bedrock via LangChain.

    This class provides methods for generating embeddings from text
    using AWS Bedrock embedding models.
    """

    def __init__(
        self,
        model_id: str = EmbeddingModel.AMAZON_TITAN_EMBED_TEXT_V2,
        aws_region: Optional[str] = None,
        aws_profile: Optional[str] = None,
    ):
        """Initialize the embedding generator.

        Args:
            model_id: ID of the embedding model to use
            aws_region: AWS region to use (optional, uses default if not provided)
            aws_profile: AWS profile to use (optional, uses default if not provided)
        """
        self.model_id = model_id
        self.aws_region = aws_region or os.environ.get('AWS_REGION', 'us-west-2')

        # Create LangChain BedrockEmbeddings
        self.bedrock_embeddings = BedrockEmbeddings(
            model_id=model_id,
            region_name=self.aws_region,
            credentials_profile_name=aws_profile,
        )
        logger.info(f'Initialized BedrockEmbeddings with model: {model_id}')

    def generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding for a single text.

        Args:
            text: Text to generate an embedding for

        Returns:
            Embedding vector as a list of floats

        Raises:
            Exception: If embedding generation fails
        """
        if not text.strip():
            # Get embedding size by embedding a test string
            test_embedding = self.bedrock_embeddings.embed_query('test')
            # Return a zero vector for empty text
            return [0.0] * len(test_embedding)

        try:
            # Use LangChain's embed_query method
            embedding = self.bedrock_embeddings.embed_query(text)
            return embedding
        except Exception as e:
            logger.error(f'Error generating embedding: {e}')
            raise

    def generate_embeddings_batch(
        self, texts: List[str], batch_size: int = 10
    ) -> List[List[float]]:
        """Generate embeddings for a batch of texts.

        Args:
            texts: List of texts to generate embeddings for
            batch_size: Number of texts to process in each batch

        Returns:
            List of embedding vectors

        Raises:
            Exception: If embedding generation fails
        """
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            logger.info(
                f'Processing batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}'
            )

            try:
                # Use LangChain's embed_documents for batch processing if available
                if hasattr(self.bedrock_embeddings, 'embed_documents'):
                    batch_embeddings = self.bedrock_embeddings.embed_documents(batch)
                    embeddings.extend(batch_embeddings)
                else:
                    # Fall back to processing each text individually
                    for text in batch:
                        embedding = self.generate_embedding(text)
                        embeddings.append(embedding)
            except Exception as e:
                logger.error(f'Error processing batch: {e}')
                # Fall back to processing each text individually
                for text in batch:
                    try:
                        embedding = self.generate_embedding(text)
                        embeddings.append(embedding)
                    except Exception as e:
                        logger.error(f'Error generating embedding for text: {e}')
                        # Use a zero vector as fallback
                        if embeddings:
                            # Use the same dimension as previous embeddings
                            embeddings.append([0.0] * len(embeddings[0]))
                        else:
                            # Use default dimension
                            embeddings.append([0.0] * 1536)

        return embeddings


def get_embedding_generator(
    model_id: str = EmbeddingModel.AMAZON_TITAN_EMBED_TEXT_V2,
    aws_region: Optional[str] = None,
    aws_profile: Optional[str] = None,
) -> EmbeddingGenerator:
    """Get an embedding generator.

    Args:
        model_id: ID of the embedding model to use
        aws_region: AWS region to use (optional, uses default if not provided)
        aws_profile: AWS profile to use (optional, uses default if not provided)

    Returns:
        EmbeddingGenerator instance
    """
    return EmbeddingGenerator(model_id, aws_region, aws_profile)
