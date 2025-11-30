import boto3
import polars as pl
from io import BytesIO
from typing import Optional, List


def load_parquet_from_s3(
    bucket: str,
    prefix: Optional[str] = None,
    single_key: Optional[str] = None,
    region: str = "us-east-1",
) -> pl.DataFrame:
    """
    Load parquet data from S3.

    Mode A: if `single_key` is provided -> load just that parquet file
    Mode B: if prefix provided and no single_key -> walk prefix, concat all parquet files

    Returns: Polars DataFrame
    """
    s3_client = boto3.client('s3', region_name=region)

    # Mode A: single file
    if single_key:
        obj = s3_client.get_object(Bucket=bucket, Key=single_key)
        parquet_data = obj['Body'].read()
        return pl.read_parquet(BytesIO(parquet_data))

    # Mode B: multiple files
    parquet_files = []
    continuation_token = None
    while True:
        list_params = {
            'Bucket': bucket
            }

        if prefix:
            list_params['Prefix'] = prefix

        if continuation_token:
            list_params['ContinuationToken'] = continuation_token

        response = s3_client.list_objects_v2(**list_params)
        if "Contents" not in response:
            raise FileNotFoundError(f"No parquet files found in S3://{bucket}/{prefix}")

        for obj in response['Contents']:
            key = obj['Key']
            if key.endswith('.parquet'):
                parquet_files.append(key)

        if response.get("IsTruncated", False):
            continuation_token = response.get("NextContinuationToken", None)
        else:
            break

    if not parquet_files:
        raise FileNotFoundError(f"No parquet files found in S3://{bucket}/{prefix}")

    dfs = []
    for key in parquet_files:
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        parquet_data = obj['Body'].read()
        dfs.append(pl.read_parquet(BytesIO(parquet_data)))

    return pl.concat(dfs, how='vertical')
