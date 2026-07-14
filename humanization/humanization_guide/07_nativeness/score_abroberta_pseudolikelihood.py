#!/usr/bin/env python
"""
Pseudo-likelihood scoring of antibody sequences with HuggingFace `mogam-ai/Ab-RoBERTa`.

For each sequence, every position is masked in turn (one residue at a time),
the model predicts a distribution over the vocabulary for that masked
position, and we record log P(true residue | rest of sequence unmasked).
This is the standard "pseudo-log-likelihood" (PLL) used to score BERT-style
masked language models on fixed sequences (Wang & Cho 2019 style scoring,
as commonly used for ESM/AbLang/AntiBERTy/Ab-RoBERTa humanness comparisons).

Usage (as a library):
    from score_abroberta_pseudolikelihood import score_sequence, score_paired

    per_pos, mean_logp, ppl = score_sequence("QVQLQ...VSS")
    result = score_paired(vh_seq, vl_seq)

Usage (CLI):
    python score_abroberta_pseudolikelihood.py \
        --fasta variants.fasta --out scores.csv

    where variants.fasta has records named like ">parental_VH", ">parental_VL",
    ">sapiens_VH", ">sapiens_VL", etc. Records are paired by stripping the
    trailing _VH/_VL suffix from the record id to compute the "paired" score
    (mean over the concatenated VH+VL per-position log-probs).

Notes / gotchas:
- mogam-ai/Ab-RoBERTa's tokenizer is a clean 1-residue-per-token vocabulary
  (20 canonical amino acids + <s>/</s>/<pad>/<unk>/<mask>), verified by
  encoding a 120-residue VH and getting exactly 122 input ids (120 + 2
  special). This makes single-residue masking exact -- no BPE merge
  ambiguity like some other protein/antibody tokenizers.
- log-prob is computed over the FULL model vocabulary (not renormalised to
  the 20 canonical AAs), which is the standard PLL definition. Since the
  true residue is always one of the 20 AA tokens this only matters in that
  the reported probability already implicitly discounts probability mass
  the model places on special tokens (a tiny effect in practice).
- perplexity = exp(-mean_logp), reported in natural-log units.
"""
import argparse
import csv
import math
import sys

import torch
from transformers import AutoModelForMaskedLM, AutoTokenizer

MODEL_NAME = "mogam-ai/Ab-RoBERTa"

_model = None
_tokenizer = None


def _load():
    global _model, _tokenizer
    if _model is None:
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForMaskedLM.from_pretrained(MODEL_NAME)
        _model.eval()
    return _model, _tokenizer


@torch.no_grad()
def score_sequence(seq: str):
    """Mask each position of `seq` in turn; return (per_position_logp, mean_logp, perplexity).

    per_position_logp is a list of (1-based position, residue, log_prob) tuples.
    """
    model, tokenizer = _load()
    vocab = tokenizer.get_vocab()
    base_ids = [tokenizer.bos_token_id] + [vocab[ch] for ch in seq] + [tokenizer.eos_token_id]
    n = len(seq)
    # Batch all masked variants together: one row per masked position.
    input_ids = torch.tensor(base_ids).unsqueeze(0).repeat(n, 1)
    for i in range(n):
        input_ids[i, i + 1] = tokenizer.mask_token_id
    logits = model(input_ids=input_ids).logits  # [n, L, vocab]
    logprobs = torch.log_softmax(logits, dim=-1)
    per_position = []
    total = 0.0
    for i in range(n):
        true_id = base_ids[i + 1]
        lp = logprobs[i, i + 1, true_id].item()
        per_position.append((i + 1, seq[i], lp))
        total += lp
    mean_logp = total / n
    ppl = math.exp(-mean_logp)
    return per_position, mean_logp, ppl


def score_paired(vh_seq: str, vl_seq: str):
    """Score VH and VL independently, then combine into a single 'paired' mean log-prob
    (mean over the concatenated VH+VL per-position log-probs, i.e. length-weighted mean
    of the two chain means)."""
    vh_pos, vh_mean, vh_ppl = score_sequence(vh_seq)
    vl_pos, vl_mean, vl_ppl = score_sequence(vl_seq)
    n_vh, n_vl = len(vh_seq), len(vl_seq)
    paired_mean = (vh_mean * n_vh + vl_mean * n_vl) / (n_vh + n_vl)
    paired_ppl = math.exp(-paired_mean)
    return {
        "VH": {"per_position": vh_pos, "mean_logp": vh_mean, "perplexity": vh_ppl, "n": n_vh},
        "VL": {"per_position": vl_pos, "mean_logp": vl_mean, "perplexity": vl_ppl, "n": n_vl},
        "paired": {"mean_logp": paired_mean, "perplexity": paired_ppl, "n": n_vh + n_vl},
    }


def _read_fasta(path):
    records = {}
    name = None
    chunks = []
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith(">"):
                if name is not None:
                    records[name] = "".join(chunks)
                name = line[1:].strip()
                chunks = []
            elif line:
                chunks.append(line)
        if name is not None:
            records[name] = "".join(chunks)
    return records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fasta", required=True, help="FASTA with records named <variant>_VH / <variant>_VL")
    ap.add_argument("--out", required=True, help="output CSV path (summary, one row per variant/chain/paired)")
    ap.add_argument("--per_position_out", default=None, help="optional CSV path for full per-position log-probs")
    args = ap.parse_args()

    records = _read_fasta(args.fasta)
    variants = {}
    for name, seq in records.items():
        if name.endswith("_VH"):
            variants.setdefault(name[:-3], {})["VH"] = seq
        elif name.endswith("_VL"):
            variants.setdefault(name[:-3], {})["VL"] = seq
        else:
            print(f"WARNING: skipping record '{name}' (no _VH/_VL suffix)", file=sys.stderr)

    summary_rows = []
    per_pos_rows = []
    for variant, chains in sorted(variants.items()):
        if "VH" not in chains or "VL" not in chains:
            print(f"WARNING: variant '{variant}' missing VH or VL, skipping paired score", file=sys.stderr)
            continue
        result = score_paired(chains["VH"], chains["VL"])
        for chain in ("VH", "VL"):
            summary_rows.append({
                "variant": variant, "chain": chain,
                "mean_logp": result[chain]["mean_logp"],
                "perplexity": result[chain]["perplexity"],
                "n_residues": result[chain]["n"],
            })
            for pos, res, lp in result[chain]["per_position"]:
                per_pos_rows.append({"variant": variant, "chain": chain, "position_1based": pos, "residue": res, "log_prob": lp})
        summary_rows.append({
            "variant": variant, "chain": "paired",
            "mean_logp": result["paired"]["mean_logp"],
            "perplexity": result["paired"]["perplexity"],
            "n_residues": result["paired"]["n"],
        })
        print(f"{variant}: VH mean_logp={result['VH']['mean_logp']:.4f}  VL mean_logp={result['VL']['mean_logp']:.4f}  "
              f"paired mean_logp={result['paired']['mean_logp']:.4f}  paired_ppl={result['paired']['perplexity']:.4f}")

    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["variant", "chain", "mean_logp", "perplexity", "n_residues"])
        w.writeheader()
        w.writerows(summary_rows)

    if args.per_position_out:
        with open(args.per_position_out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["variant", "chain", "position_1based", "residue", "log_prob"])
            w.writeheader()
            w.writerows(per_pos_rows)


if __name__ == "__main__":
    main()
