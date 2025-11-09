"""
Model loading and initialization for RAG pipeline.
"""
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from sentence_transformers.cross_encoder import CrossEncoder
from huggingface_hub import login
from typing import Tuple

from config import Config


def initialize_llm() -> Tuple[AutoTokenizer, AutoModelForCausalLM]:
    """
    Initialize and load the LLM with quantization configuration.
    
    Returns:
        Tuple of (tokenizer, model)
    """
    print(f"Logging in to Hugging Face...")
    login(token=Config.HF_TOKEN)
    
    print(f"Loading LLM model: {Config.LLM_MODEL_ID}")
    
    # Configure 4-bit quantization
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=Config.LOAD_IN_4BIT,
        bnb_4bit_use_double_quant=Config.BNB_4BIT_USE_DOUBLE_QUANT,
        bnb_4bit_quant_type=Config.BNB_4BIT_QUANT_TYPE,
        bnb_4bit_compute_dtype=torch.bfloat16
    )
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(Config.LLM_MODEL_ID)
    
    # Load model with quantization
    model = AutoModelForCausalLM.from_pretrained(
        Config.LLM_MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto"
    )
    
    print("Model loaded successfully.")
    return tokenizer, model


def initialize_reranker() -> CrossEncoder:
    """
    Initialize and load the reranker model.
    
    Returns:
        CrossEncoder model for reranking
    """
    print(f"Loading reranker model: {Config.RERANKER_MODEL_ID}")
    reranker_model = CrossEncoder(Config.RERANKER_MODEL_ID)
    print("Reranker model loaded successfully.")
    return reranker_model
