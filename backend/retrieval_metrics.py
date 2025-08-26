#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compute Retrieval Accuracy: Recall@k and MRR@k

Input CSV must have columns:
- query_id: unique id per query (string or int)
- relevant_ids: semicolon-separated list of relevant doc ids
- retrieved_ids: semicolon-separated list of retrieved doc ids in ranked order (best first)

Example row:
42,"A;C","B;A;D;E"

Usage:
python retrieval_metrics.py --input data.csv --ks 1 3 5 10 --output metrics.csv
"""
import argparse
import csv
from collections import defaultdict
from typing import List, Dict, Tuple, Set

def parse_list(cell: str, sep: str = ';') -> List[str]:
    if cell is None:
        return []
    # Split, strip, drop empties
    return [x.strip() for x in str(cell).split(sep) if str(x).strip() != '']

def recall_at_k(relevant: Set[str], retrieved: List[str], k: int) -> float:
    if len(relevant) == 0:
        return 0.0
    topk = retrieved[:k]
    hit = sum(1 for r in topk if r in relevant)
    return hit / float(len(relevant))

def mrr_at_k(relevant: Set[str], retrieved: List[str], k: int) -> float:
    topk = retrieved[:k]
    for idx, doc_id in enumerate(topk, start=1):
        if doc_id in relevant:
            return 1.0 / idx
    return 0.0

def compute_metrics(rows: List[Dict[str, str]], ks: List[int], sep: str,
                    relevant_col: str, retrieved_col: str, query_col: str
                   ) -> Tuple[Dict[int, float], Dict[int, float]]:
    recalls = defaultdict(list)  # k -> list of per-query recall@k
    mrrs = defaultdict(list)     # k -> list of per-query mrr@k

    for row in rows:
        relevant = set(parse_list(row.get(relevant_col, ''), sep=sep))
        retrieved = parse_list(row.get(retrieved_col, ''), sep=sep)

        for k in ks:
            recalls[k].append(recall_at_k(relevant, retrieved, k))
            mrrs[k].append(mrr_at_k(relevant, retrieved, k))

    mean_recall = {k: (sum(v)/len(v) if v else 0.0) for k, v in recalls.items()}
    mean_mrr = {k: (sum(v)/len(v) if v else 0.0) for k, v in mrrs.items()}
    return mean_recall, mean_mrr

def load_rows(path: str) -> List[Dict[str, str]]:
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_summary(path: str, mean_recall: Dict[int, float], mean_mrr: Dict[int, float]) -> None:
    ks_sorted = sorted(set(list(mean_recall.keys()) + list(mean_mrr.keys())))
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['metric'] + [f'@{k}' for k in ks_sorted])
        writer.writerow(['Recall'] + [f'{mean_recall.get(k, 0.0):.6f}'] * len(ks_sorted))
        writer.writerow(['MRR'] + [f'{mean_mrr.get(k, 0.0):.6f}'] * len(ks_sorted))

def main():
    parser = argparse.ArgumentParser(description='Compute Recall@k and MRR@k for retrieval results.')
    parser.add_argument('--input', required=True, help='Path to input CSV.')
    parser.add_argument('--output', default='metrics_summary.csv', help='Path to output CSV.')
    parser.add_argument('--ks', nargs='+', type=int, default=[1,3,5,10],
                        help='List of k values, e.g., --ks 1 3 5 10')
    parser.add_argument('--sep', default=';', help='Separator used in list cells (default: ;)')
    parser.add_argument('--relevant_col', default='relevant_ids', help='Name of column with relevant ids.')
    parser.add_argument('--retrieved_col', default='retrieved_ids', help='Name of column with retrieved ids (ranked).')
    parser.add_argument('--query_col', default='query_id', help='Name of the query id column.')
    args = parser.parse_args()

    rows = load_rows(args.input)
    if not rows:
        print('No rows found in input.')
        return

    mean_recall, mean_mrr = compute_metrics(rows, args.ks, args.sep,
                                            args.relevant_col, args.retrieved_col, args.query_col)

    # Pretty print
    print('=== Retrieval Metrics ===')
    print('k\tRecall@k\tMRR@k')
    for k in sorted(args.ks):
        print(f'{k}\t{mean_recall.get(k, 0.0):.6f}\t{mean_mrr.get(k, 0.0):.6f}')

    # Save CSV summary
    save_summary(args.output, mean_recall, mean_mrr)
    print(f'\nSaved summary to: {args.output}')

if __name__ == '__main__':
    main()
