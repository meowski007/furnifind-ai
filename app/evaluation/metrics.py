import math


def precision_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int = 5) -> float:
    if k <= 0:
        return 0.0
    if len(relevant_ids) == 0:
        # Negative control query: if zero retrieved in top_k, precision is 1.0 (correctly rejected)
        return 1.0 if len(retrieved_ids) == 0 else 0.0

    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0

    hits = sum(1 for pid in top_k if pid in relevant_ids)
    return hits / float(k)


def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int = 5) -> float:
    if len(relevant_ids) == 0:
        # Negative control query: 1.0 if correctly no items retrieved, 0.0 if fabricated matches
        return 1.0 if len(retrieved_ids) == 0 else 0.0

    top_k = retrieved_ids[:k]
    hits = sum(1 for pid in top_k if pid in relevant_ids)
    return hits / float(len(relevant_ids))


def dcg_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int = 5) -> float:
    top_k = retrieved_ids[:k]
    score = 0.0
    for idx, pid in enumerate(top_k):
        rel = 1.0 if pid in relevant_ids else 0.0
        score += (2.0**rel - 1.0) / math.log2(idx + 2.0)
    return score


def ndcg_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int = 5) -> float:
    if len(relevant_ids) == 0:
        return 1.0 if len(retrieved_ids) == 0 else 0.0

    actual_dcg = dcg_at_k(retrieved_ids, relevant_ids, k)

    # Ideal DCG: all relevant items ranked first
    n_rel = min(k, len(relevant_ids))
    ideal_retrieved = list(relevant_ids)[:n_rel]
    ideal_dcg = dcg_at_k(ideal_retrieved, relevant_ids, k)

    if ideal_dcg == 0.0:
        return 0.0
    return actual_dcg / ideal_dcg


def reciprocal_rank(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    if len(relevant_ids) == 0:
        return 1.0 if len(retrieved_ids) == 0 else 0.0

    for idx, pid in enumerate(retrieved_ids):
        if pid in relevant_ids:
            return 1.0 / (idx + 1.0)
    return 0.0
