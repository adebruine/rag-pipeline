"""
LLM generation utilities for RAG pipeline.
"""
import anthropic
from typing import List, Dict, Any, Optional

from config import Config


def build_context_string(retrieved_chunks: List[dict], max_chunks: Optional[int] = None) -> str:
    """
    Send only useful metadata to the LLM.

    Args:
        retrieved_chunks: List of retrieved chunk dictionaries
        max_chunks: Maximum number of chunks to include (for filter-only search)

    Returns:
        Formatted context string for LLM
    """
    context_string = ""
    if not retrieved_chunks:
        return "No documents were retrieved."

    matches_to_process = retrieved_chunks  # standard search
    if max_chunks is not None:  # filter-only search, only send the first N chunks to LLM
        matches_to_process = matches_to_process[:max_chunks]

    for i, match in enumerate(matches_to_process):
        metadata = match.get('metadata', {})
        score = match.get('score', 0)

        chunk_text = metadata.get('text', 'N/A')
        state = metadata.get('state', 'N/A')
        county = metadata.get('county', 'N/A')
        section = metadata.get('section', 'N/A')
        print(f"chunk_text: {chunk_text}")

        tags = []
        if metadata.get('obligation') == 'Y':
            tags.append("Obligation")
        if metadata.get('penalty') == 'Y':
            tags.append("Penalty")
        if metadata.get('permission') == 'Y':
            tags.append("Permission")
        if metadata.get('prohibition') == 'Y':
            tags.append("Prohibition")

        context_string += f"[Chunk {i+1}]\n"
        context_string += f"Score: {score:.4f}\n"
        context_string += f"State: {state}\n"
        context_string += f"County: {county}\n"
        context_string += f"Section: {section}\n"

        if tags:
            context_string += f"Tags: {', '.join(tags)}\n"

        context_string += f"Text: \"{chunk_text}\"\n\n"

    return context_string


def generate_llm_response(query_text: str, context_string: str) -> str:
    """
    Generate LLM response for standard search queries.

    Args:
        query_text: User's query
        context_string: Context from retrieved chunks

    Returns:
        Generated response text
    """
    system_prompt = """
    You are a highly intelligent program evaluation analyst with a scientific background. Your goal is to help a 
    user understand the scientific research your organization has funded.
    You will be given the user's original question and a list of 'Retrieved Chunks' from the organization's database.

    Your task is to generate a natural language response. You MUST follow these rules:
    1. Base your answer *ONLY* on the information inside the "Retrieved Chunks". Do not use any outside knowledge.
    Do your best to answer the question based solely on the information provided. Let the user know if you need further
    information to provide a better answer.
  """

    user_prompt = f"""
    **User's Question:**
    {query_text}

    **Retrieved Chunks:**
    {context_string}
  """

    client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=Config.CLAUDE_MODEL,
        max_tokens=Config.MAX_NEW_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return message.content[0].text


def generate_llm_response_filter_only_search(
    query_text: str,
    context_string: str,
    num_total_chunks: int
) -> str:
    """
    Generate LLM response for filter-only searches.

    Args:
        query_text: User's query (empty for filter-only)
        context_string: Context from retrieved chunks sample
        num_total_chunks: Total number of chunks retrieved

    Returns:
        Generated response text with summary
    """
    system_prompt = """
    You are a highly intelligent legal analyst.
    You will be given a *sample* of the top-retrieved legal documents.
    Your task is to **provide a high-level summary of the main themes** found in this sample.

    - DO NOT try to answer a question.
    - DO NOT say "I cannot find an answer."
    - Simply summarize what you see. Group similar topics together.
    - Start your response with: "The documents in this sample primarily discuss..."
  """

    user_prompt = f"""
    **Retrieved Chunks (Sample):**
    {context_string}
  """

    client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=Config.CLAUDE_MODEL,
        max_tokens=Config.MAX_NEW_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    response_text = message.content[0].text

    return (
        f"Found {num_total_chunks} laws matching your filters. "
        f"A full list is available in the generated CSV file.\n\n"
        f"Here is a quick summary of the first 10 results:\n\n"
        f"{response_text}"
    )