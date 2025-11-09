"""
LLM generation utilities for RAG pipeline.
"""
import torch
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

        chunk_text = metadata.get('chunk_text', 'N/A')
        state = metadata.get('state', 'N/A')
        county = metadata.get('county', 'N/A')
        section = metadata.get('section', 'N/A')

        tags = []
        if metadata.get('obligation') == 'Y':
            tags.append("Obligation")
        if metadata.get('penalty') == 'Y':
            tags.append("Penalty")
        if metadata.get('permission') == 'Y':
            tags.append("Permission")
        if metadata.get('prohibition') == 'Y':
            tags.append("Prohibition")

        # --- Build the new, enriched context string ---
        context_string += f"[Chunk {i+1}]\n"
        context_string += f"Score: {score:.4f}\n"
        context_string += f"State: {state}\n"
        context_string += f"County: {county}\n"
        context_string += f"Section: {section}\n"

        if tags:
            context_string += f"Tags: {', '.join(tags)}\n"

        context_string += f"Text: \"{chunk_text}\"\n\n"

    return context_string


def generate_llm_response(query_text: str, context_string: str, tokenizer: Any, model: Any) -> str:
    """
    Generate LLM response for standard search queries.
    
    Args:
        query_text: User's query
        context_string: Context from retrieved chunks
        tokenizer: LLM tokenizer
        model: LLM model
        
    Returns:
        Generated response text
    """
    system_prompt = """
    You are a highly intelligent legal analyst. Your goal is to help a user understand the legal information provided.
    You will be given the user's original question and a list of 'Retrieved Chunks' from a legal database.

    Your task is to generate a natural language response. You MUST follow these rules:
    1. Base your answer *ONLY* on the information inside the "Retrieved Chunks". Do not use any outside knowledge.
    2. Use the 'Score, State, County, Section, Tags' fields for quick understanding, but use the full 'Text' field to find the specific answer.
    3. If the chunks do not contain a clear answer to the user's question, you MUST respond *only* with the text: 'The information was not found in the provided documents.'
    4. If the chunks *do* contain an answer, summarize it and use the template below to explain the generation process.

    ---
    TEMPLATE FOR A SUCCESSFUL ANSWER:
    ### Summary of Findings
    [Your summary of the answer found in the chunks. Cite the chunks, e.g., "The law prohibits owners from letting their dog disturb the peace [Chunk 1]."]

    ### How This Was Generated
    To answer your question, this tool performed a search on the UnBarred 2.0 legal database. The "Retrieved Chunks" (which are provided in your CSV file) represent the top 10 most relevant sections of the law found by our search. This summary is based *only* on the information in those chunks. You can review the full text of each chunk in the CSV to verify the information for yourself.
    ---
  """

    user_prompt = f"""
    **User's Question:**
    {query_text}

    **Retrieved Chunks:**
    {context_string}
  """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    input_ids = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(model.device)

    terminators = [
        tokenizer.eos_token_id,
        tokenizer.convert_tokens_to_ids("<|eot_id|>")
    ]

    attention_mask = torch.ones_like(input_ids).to(model.device)
    pad_token_id = tokenizer.eos_token_id

    outputs = model.generate(
        input_ids,
        attention_mask=attention_mask,
        pad_token_id=pad_token_id,
        max_new_tokens=Config.MAX_NEW_TOKENS,
        eos_token_id=terminators,
        do_sample=Config.DO_SAMPLE
    )

    response = outputs[0][input_ids.shape[-1]:]
    response_text = tokenizer.decode(response, skip_special_tokens=True)

    return response_text


def generate_llm_response_filter_only_search(
    query_text: str, 
    context_string: str, 
    tokenizer: Any, 
    model: Any, 
    num_total_chunks: int
) -> str:
    """
    Generate LLM response for filter-only searches.
    
    Args:
        query_text: User's query (empty for filter-only)
        context_string: Context from retrieved chunks sample
        tokenizer: LLM tokenizer
        model: LLM model
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

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    input_ids = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(model.device)

    terminators = [
        tokenizer.eos_token_id,
        tokenizer.convert_tokens_to_ids("<|eot_id|>")
    ]

    attention_mask = torch.ones_like(input_ids).to(model.device)
    pad_token_id = tokenizer.eos_token_id

    outputs = model.generate(
        input_ids,
        attention_mask=attention_mask,
        pad_token_id=pad_token_id,
        max_new_tokens=Config.MAX_NEW_TOKENS,
        eos_token_id=terminators,
        do_sample=Config.DO_SAMPLE
    )

    response = outputs[0][input_ids.shape[-1]:]
    response_text = tokenizer.decode(response, skip_special_tokens=True)

    llm_output = (
        f"Found {num_total_chunks} laws matching your filters. "
        f"A full list is available in the generated CSV file.\n\n"
        f"Here is a quick summary of the first 10 results:\n\n"
        f"{response_text}"
    )

    return llm_output
