#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF → Parquet extractor (local paths OR S3 prefixes)
- Recursively lists PDFs under an S3 prefix
- Extracts page text with layout-aware ordering + optional OCR fallback
- WRITES OUTPUT to:
    s3://<bucket>/env=prod/zone=text/state=<STATE>/county=<COUNTY>/<filename>_text.parquet
  where <STATE> and <COUNTY> are parsed from the INPUT S3 KEY.

Args:
  --input : local file/folder OR s3://bucket/prefix OR s3://bucket/file.pdf
  --out   : s3://bucket/env=prod[/] (recommended)  OR a local dir (for local runs)
  --env/--zone/--state/--county : optional metadata (still written into parquet)
  --no-ocr : disable OCR fallback
  --s3-max : limit number of PDFs processed from S3 (0 = no limit)

Notes:
- For LOCAL inputs, --out is treated as a directory/prefix and we’ll write <stem>.parquet (no state/county mapping).
- For S3 inputs, the output path is derived from INPUT KEY’s state=... and county=...
"""

import argparse
import hashlib
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import re
import tempfile
import shutil

import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Optional pyarrow fs for s3 write
try:
    import pyarrow.fs as pafs
except Exception:
    pafs = None

import boto3
from botocore.exceptions import ClientError

# ------------------------ Tunables ------------------------

MIN_TEXT_LEN   = int(os.getenv("MIN_TEXT_LEN", "60"))   # OCR trigger threshold
OCR_DPI        = int(os.getenv("OCR_DPI", "250"))
OCR_LANG       = os.getenv("OCR_LANG", "eng")
OCR_TIMEOUT_S  = int(os.getenv("OCR_TIMEOUT_S", "12"))
MAX_OCR_PAGES  = int(os.getenv("MAX_OCR_PAGES", "20"))
ALLOW_OCR      = os.getenv("ALLOW_OCR", "true").lower() != "false"  # --no-ocr overrides

# Two-column detection (tuned)
MIN_GAP_RATIO         = 0.12     # ~12% of page width
EDGE_MARGIN_RATIO     = 0.15     # ignore mids near outer 15% bands
MIN_BLOCKS_PER_COLUMN = 4        # require more evidence per column

# Extra guards
GUTTER_MID_BAND       = (0.35, 0.65)  # require mid in central 35–65% of width
TRIM_TOP_BOTTOM_RATIO = 0.08          # ignore top/bottom 8% of items when finding gutter

Y_TOL = 2.0  # row grouping tolerance (points)

APPLY_ENUMERATOR_CLEAN = True

# ------------------------ Small helpers ------------------------

def sha256_text(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def as_str(s: Optional[str]) -> Optional[str]:
    if s is None: return None
    s2 = str(s).strip()
    return s2 if s2 else None

def is_s3_uri(uri: str) -> bool:
    return uri.strip().lower().startswith("s3://")

def split_s3_uri(uri: str) -> Tuple[str, str]:
    u = uri.strip()[5:]  # drop s3://
    parts = u.split("/", 1)
    bucket = parts[0]
    key = parts[1] if len(parts) == 2 else ""
    return bucket, key

def slugify_filename(name: str) -> str:
    base = os.path.basename(name)
    base = re.sub(r"[^\w\-. ]+", "_", base)
    return base

# ------------------------ OCR ------------------------

def ocr_page_to_text(page: fitz.Page, dpi: int = OCR_DPI, lang: str = OCR_LANG) -> str:
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    try:
        txt = pytesseract.image_to_string(img, lang=lang, timeout=OCR_TIMEOUT_S) or ""
    except RuntimeError:
        return ""
    return txt.replace("\r\n", "\n").replace("\r", "\n").strip()

# ------------------------ Layout-aware extraction ------------------------

def _collect_items_dict(page: fitz.Page):
    d = page.get_text("dict") or {}
    items = []
    for b_idx, b in enumerate(d.get("blocks", [])):
        if b.get("type", 0) != 0:
            continue
        for ln in b.get("lines", []):
            spans = ln.get("spans", [])
            if not spans:
                continue
            x0, y0, x1, y1 = ln.get("bbox", (0, 0, 0, 0))
            txt = "".join((s.get("text") or "") for s in spans)
            txt = txt.replace("\r\n", "\n").replace("\r", "\n")
            if not txt.strip():
                continue
            items.append({"bidx": b_idx, "y": y0, "x": x0, "x1": x1, "text": txt.rstrip()})
    return items

def _items_to_columns(items: List[dict], page_width: float):
    # Need enough signals to even consider a split
    need = max(4, 2 * MIN_BLOCKS_PER_COLUMN)
    if len(items) < need:
        return items, [], None

    # Trim top/bottom bands to avoid headers/footers polluting gutter search
    ys = sorted(it["y"] for it in items)
    if ys:
        k = int(len(ys) * TRIM_TOP_BOTTOM_RATIO)
        y_lo = ys[k] if k < len(ys) else ys[0]
        y_hi = ys[-k-1] if k > 0 else ys[-1]
        trimmed = [it for it in items if y_lo <= it["y"] <= y_hi]
        if len(trimmed) >= need:
            work = trimmed
        else:
            work = items
    else:
        work = items

    # Use true line centers (x0+x1)/2. Fallback to x if x1 missing.
    centers = []
    for it in work:
        x0 = it.get("x", 0.0)
        x1 = it.get("x1", None)
        c  = 0.5 * (x0 + x1) if isinstance(x1, (int, float)) else float(x0)
        centers.append(c)

    if len(centers) < need:
        return items, [], None

    centers.sort()
    max_gap, mid = 0.0, None
    for i in range(len(centers) - 1):
        gap = centers[i+1] - centers[i]
        if gap > max_gap:
            max_gap = gap
            mid = 0.5 * (centers[i+1] + centers[i])

    if mid is None:
        return items, [], None

    # Stronger interior checks
    if not (EDGE_MARGIN_RATIO * page_width < mid < (1.0 - EDGE_MARGIN_RATIO) * page_width):
        return items, [], None

    lo_band, hi_band = GUTTER_MID_BAND
    if not (lo_band * page_width <= mid <= hi_band * page_width):
        return items, [], None

    if max_gap < (MIN_GAP_RATIO * page_width):
        return items, [], None

    # Split by center (not x+100)
    left, right = [], []
    for it in items:
        x0 = it.get("x", 0.0)
        x1 = it.get("x1", None)
        c  = 0.5 * (x0 + x1) if isinstance(x1, (int, float)) else float(x0)
        (left if c <= mid else right).append(it)

    if len(left) < MIN_BLOCKS_PER_COLUMN or len(right) < MIN_BLOCKS_PER_COLUMN:
        return items, [], None

    return left, right, mid


def _sort_items(items: List[dict]):
    if not items:
        return []
    items = sorted(items, key=lambda it: it["y"])
    rows, cur = [], []
    last_y = None
    for it in items:
        if last_y is None or abs(it["y"] - last_y) <= Y_TOL:
            cur.append(it)
            last_y = it["y"] if last_y is None else (last_y + it["y"]) / 2.0
        else:
            cur.sort(key=lambda z: (round(z["x"], 2), z["bidx"]))
            rows.append(cur)
            cur = [it]
            last_y = it["y"]
    if cur:
        cur.sort(key=lambda z: (round(z["x"], 2), z["bidx"]))
        rows.append(cur)
    return [it for row in rows for it in row]

def page_text_layout(page: fitz.Page) -> str:
    items = _collect_items_dict(page)
    if not items:
        return ""
    left, right, gutter = _items_to_columns(items, page.rect.width)

    def join_items(its: List[dict]) -> str:
        ordered = _sort_items(its)
        return "\n".join(it["text"] for it in ordered if it["text"].strip())

    if gutter is None:
        return join_items(items).strip()
    return "\n\n".join(s for s in (join_items(left), join_items(right)) if s).strip()

# ------------------------ Enumerator cleaner ------------------------

_BARE_ENUM_RE = re.compile(
    r'^([A-Z]\.|\([A-Za-z]\)|\d+\.|\([0-9]{1,3}\)|[ivxlcdm]+\.|\([ivxlcdm]+\))\s*$',
    re.IGNORECASE
)

def remove_orphan_enumerators(text: str) -> str:
    lines = str(text or "").splitlines()
    out, i, n = [], 0, len(lines)

    def is_bare_enum(s: str) -> bool:
        return bool(_BARE_ENUM_RE.match(s.strip()))

    def next_nonempty(j: int):
        k = j
        while k < n and not lines[k].strip():
            k += 1
        return k if k < n else None

    while i < n:
        raw = lines[i]
        if is_bare_enum(raw):
            k = next_nonempty(i + 1)
            if k is None:
                i += 1
                continue
            nxt = lines[k].strip()
            if is_bare_enum(nxt):
                i += 1
                continue
            out.append(raw)
            i += 1
            continue
        out.append(raw)
        i += 1
    return "\n".join(out)

# ------------------------ Extraction core ------------------------

def extract_pdf_to_records(pdf_path: Path,
                           env: Optional[str],
                           zone: Optional[str],
                           state: Optional[str],
                           county: Optional[str]) -> List[Dict]:
    source_name = pdf_path.name
    doc_id = hashlib.sha1(str(pdf_path).encode("utf-8")).hexdigest()[:20]
    ts = now_iso()
    records: List[Dict] = []
    ocr_used = 0

    with fitz.open(str(pdf_path)) as doc:
        for i in range(doc.page_count):
            page = doc.load_page(i)
            page_num = i + 1

            txt = page_text_layout(page)
            is_ocr = False

            needs_ocr = (
                ALLOW_OCR
                and len(txt.strip()) < MIN_TEXT_LEN
                and ocr_used < MAX_OCR_PAGES
            )
            if needs_ocr:
                items = _collect_items_dict(page)
                if len(items) <= 2:
                    txt_ocr = ocr_page_to_text(page, OCR_DPI, OCR_LANG)
                    if len(txt_ocr.strip()) > len(txt.strip()):
                        txt = txt_ocr
                        is_ocr = True
                        ocr_used += 1

            if APPLY_ENUMERATOR_CLEAN and txt:
                txt = remove_orphan_enumerators(txt)

            rec = {
                "doc_id": doc_id,
                "source_name": source_name,
                "page": page_num,
                "text": txt,
                "is_ocr": is_ocr,
                "char_len": len(txt),
                "sha256": sha256_text(f"{source_name}|{page_num}|{txt}"),
                "extracted_at": ts,
                "env": as_str(env),
                "zone": as_str(zone),
                "state": as_str(state),
                "county": as_str(county),
            }
            records.append(rec)

    return records

# ------------------------ Parquet write ------------------------

def write_parquet(records: List[Dict], out_path: str):
    if not records:
        print(f"[warn] No records to write for {out_path}")
        return
    df = pd.DataFrame.from_records(records)
    for col in ("env", "zone", "state", "county", "source_name"):
        if col in df.columns:
            df[col] = df[col].astype("string")
    table = pa.Table.from_pandas(df, preserve_index=False)

    if out_path.startswith("s3://"):
        if pafs is None:
            raise RuntimeError("pyarrow.fs is not available; cannot write to S3")
        _, _, rest = out_path.partition("s3://")
        bucket, _, key = rest.partition("/")
        fs = pafs.S3FileSystem(
            region=os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1")),
            access_key=os.getenv("AWS_ACCESS_KEY_ID"),
            secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
        with fs.open_output_stream(f"{bucket}/{key}") as sink:
            pq.write_table(table, sink)
        print(f"[ok] wrote {len(df)} rows → {out_path}")
    else:
        out_path = str(Path(out_path))
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        pq.write_table(table, out_path)
        print(f"[ok] wrote {len(df)} rows → {out_path}")

# ------------------------ S3 helpers ------------------------

def discover_local_pdfs(input_path: Path) -> List[Path]:
    if input_path.is_file() and input_path.suffix.lower() == ".pdf":
        return [input_path]
    if input_path.is_dir():
        return sorted(p for p in input_path.rglob("*.pdf"))
    return []

def list_s3_pdfs(bucket: str, prefix: str) -> List[str]:
    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1")))
    keys = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []) or []:
            k = obj["Key"]
            if k.lower().endswith(".pdf"):
                keys.append(k)
    return keys

def download_s3_object(bucket: str, key: str, local_dir: Path) -> Path:
    local_dir.mkdir(parents=True, exist_ok=True)
    local_file = local_dir / slugify_filename(os.path.basename(key))
    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1")))
    s3.download_file(bucket, key, str(local_file))
    return local_file

# ------------------------ Output mapping for S3 inputs ------------------------

def parse_state_county_from_key(key: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse state=<state> and county=<county> from an S3 key path.
    Returns (state, county) or (None, None) if not found.
    """
    state = county = None
    parts = key.strip("/").split("/")
    for seg in parts:
        if seg.startswith("state="):
            state = seg.split("=", 1)[1]
        elif seg.startswith("county="):
            county = seg.split("=", 1)[1]
    return state, county

def build_out_key_from_input(input_bucket: str, input_key: str, out_base: str) -> str:
    """
    out_base should be like: s3://<bucket>/env=prod[/]
    Builds: s3://<same-bucket-or-out_base bucket>/env=prod/zone=text/state=STATE/county=COUNTY/<filename>_text.parquet
    """
    # Decide output bucket from out_base
    if not out_base.startswith("s3://"):
        raise ValueError("--out must be s3://... when using S3 input to auto-map env/state/county")
    out_bucket, out_key_base = split_s3_uri(out_base)

    # Ensure env=prod root in out_key_base (user might pass s3://bucket/env=prod or s3://bucket/env=prod/)
    out_key_base = out_key_base.strip("/")
    if not out_key_base:
        raise ValueError("Provide an --out like s3://<bucket>/env=prod/")
    # Pull state/county from INPUT key
    state, county = parse_state_county_from_key(input_key)
    if not state or not county:
        raise ValueError(f"Could not parse state/county from input key: {input_key}")

    # Build output key
    filename = os.path.basename(input_key)
    stem = os.path.splitext(filename)[0] + "_text.parquet"
    out_key = f"{out_key_base}/zone=text/state={state}/county={county}/{stem}"
    return f"s3://{out_bucket}/{out_key}"

# ------------------------ CLI ------------------------

def main():
    ap = argparse.ArgumentParser(description="PDF → Parquet (local path OR S3 prefix)")
    ap.add_argument("--input", required=True, help="Local file/folder OR s3://bucket/prefix OR s3://bucket/file.pdf")
    ap.add_argument("--out",   required=True, help="For S3 input, use s3://bucket/env=prod[/]; for local input, a dir or s3 prefix")
    ap.add_argument("--env",   default=None)
    ap.add_argument("--zone",  default=None)
    ap.add_argument("--state", default=None)
    ap.add_argument("--county", default=None)
    ap.add_argument("--no-ocr", action="store_true", help="Disable OCR fallback entirely")
    ap.add_argument("--s3-max", type=int, default=0, help="Limit PDFs processed from S3 prefix (0 = no limit)")
    args = ap.parse_args()

    global ALLOW_OCR
    if args.no_ocr:
        ALLOW_OCR = False

    total_pdfs = 0
    total_pages = 0
    t0 = time.time()

    tmp_root = Path(tempfile.mkdtemp(prefix="pdf-extract-"))
    tmp_in = tmp_root / "in"
    tmp_in.mkdir(parents=True, exist_ok=True)

    try:
        tasks: List[Tuple[Path, Optional[str], Optional[str]]] = []
        # Each task: (local_pdf_path, s3_bucket_if_any, s3_key_if_any)

        if is_s3_uri(args.input):
            in_bucket, in_key = split_s3_uri(args.input)
            if in_key and in_key.lower().endswith(".pdf"):
                print(f"[info] downloading single PDF from s3://{in_bucket}/{in_key}")
                local = download_s3_object(in_bucket, in_key, tmp_in)
                tasks.append((local, in_bucket, in_key))
            else:
                prefix = in_key if in_key.endswith("/") else (in_key + "/") if in_key else ""
                print(f"[info] listing PDFs under s3://{in_bucket}/{prefix} ...")
                keys = list_s3_pdfs(in_bucket, prefix)
                if args.s3_max and args.s3_max > 0:
                    keys = keys[:args.s3_max]
                print(f"[info] found {len(keys)} PDFs under prefix")
                for k in keys:
                    try:
                        local = download_s3_object(in_bucket, k, tmp_in)
                        tasks.append((local, in_bucket, k))
                    except ClientError as e:
                        print(f"[error] failed to download s3://{in_bucket}/{k}: {e}")
        else:
            in_path = Path(args.input)
            for p in discover_local_pdfs(in_path):
                tasks.append((p, None, None))

        if not tasks:
            print(f"[error] No PDFs found for input: {args.input}", file=sys.stderr)
            sys.exit(2)

        # If --out is a single parquet file but multiple inputs -> error
        out_is_single_parquet = (
            args.out.lower().endswith(".parquet") and not args.out.startswith("s3://")
        ) or (
            args.out.startswith("s3://") and args.out.lower().endswith(".parquet")
        )
        if out_is_single_parquet and len(tasks) > 1:
            print("[error] --out is a single file but multiple PDFs found. "
                  "Use an s3 prefix like s3://bucket/env=prod/ or a local directory.", file=sys.stderr)
            sys.exit(3)

        for local_pdf, src_bucket, src_key in tasks:
            total_pdfs += 1
            print(f"[info] extracting: {local_pdf}")
            try:
                # Extract records
                records = extract_pdf_to_records(local_pdf, args.env, args.zone, args.state, args.county)

                # Decide output path
                if src_bucket and src_key:
                    # S3 input: build out path from input key + out base (env=prod)
                    out_path = build_out_key_from_input(src_bucket, src_key, args.out)
                else:
                    # Local input: generic behavior
                    stem = Path(local_pdf).stem + "_text.parquet"
                    if args.out.startswith("s3://"):
                        out_bucket, out_key_base = split_s3_uri(args.out)
                        out_key_base = out_key_base.strip("/")
                        if out_key_base and not out_key_base.endswith("/"):
                            out_key_base = out_key_base + "/"
                        out_path = f"s3://{out_bucket}/{out_key_base}{stem}"
                    else:
                        outdir = Path(args.out)
                        outdir.mkdir(parents=True, exist_ok=True)
                        out_path = str(outdir / stem)

                # Write parquet
                write_parquet(records, out_path)
                total_pages += len(records)

            except Exception as e:
                print(f"[error] failed on {local_pdf}: {e}", file=sys.stderr)

        dt = time.time() - t0
        print(f"[done] processed {total_pdfs} PDFs, {total_pages} pages in {dt:.1f}s")

    finally:
        try:
            shutil.rmtree(tmp_root)
        except Exception:
            pass

if __name__ == "__main__":
    main()

