import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

load_dotenv()

def init_pinecone(index_name: str, dimension: int = 1024, region: str = 'us-east-1', metric = 'dotproduct'):


    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY is not set in environment variables")

    pc = Pinecone(api_key=api_key)

    if not pc.has_index(index_name):
        pc.create_index(
            name=index_name,
            vector_type='dense',
            dimension=dimension,
            metric=metric,
            spec=ServerlessSpec(
                cloud='aws',
                region=region,
            )
        )

    index = pc.Index(index_name)
    return pc, index
