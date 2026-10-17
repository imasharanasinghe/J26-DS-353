"""Component 2 - ASSISTments loading + graph (pandas/numpy only).
Dataset: ASSISTments 2009-2010 'skill builder' (skill_builder_data_corrected.csv).
Also works with ASSISTments 2012 (needs user_id, skill_id, correct, start_time).
"""
import numpy as np, pandas as pd
import c2_data as D

def load_assistments(path, min_len=25, max_len=300):
    df = pd.read_csv(path, encoding="latin-1", low_memory=False)
    order = "order_id" if "order_id" in df.columns else "start_time"
    df = df.dropna(subset=["skill_id"])
    df = df[df["correct"].isin([0, 1])].sort_values(["user_id", order])
    skills = sorted(df["skill_id"].unique()); sid = {s: i for i, s in enumerate(skills)}
    df["c"] = df["skill_id"].map(sid)
    names = {}
    if "skill_name" in df.columns:
        names = {sid[s]: n for s, n in df.drop_duplicates("skill_id")[["skill_id", "skill_name"]].values}
    seqs = []
    for u, g in df.groupby("user_id"):
        if len(g) >= min_len:
            seqs.append((u, g["c"].values[:max_len].astype(np.int64), g["correct"].values[:max_len].astype(np.float32)))
    return seqs, len(skills), names, sid

def proxy_graph(seqs, n, min_pair=30, thresh=0.65, max_parents=3):
    """PLACEHOLDER prerequisite graph inferred from the order in which skills FIRST appear.
    Replace with Component 1's graph (see load_graph_csv). Build from TRAIN users only."""
    before = np.zeros((n, n))
    for _, c, _ in seqs:
        first = np.full(n, np.inf)
        u, idx = np.unique(c, return_index=True); first[u] = idx
        seen = first < np.inf
        before += (first[:, None] < first[None, :]) & seen[:, None] & seen[None, :]
    tot = before + before.T
    score = np.divide(before, tot, out=np.zeros_like(before), where=tot > 0)
    A = np.zeros((n, n), dtype=np.float32)          # A[b, a] = 1  <=>  a is a prerequisite of b
    for b in range(n):
        cand = [(score[a, b], a) for a in range(n) if a != b and tot[a, b] >= min_pair and score[a, b] >= thresh]
        for _, a in sorted(cand, reverse=True)[:max_parents]:
            A[b, a] = 1
    return A

def load_graph_csv(path, sid):
    """Component 1 export: CSV with columns prereq,skill (dataset skill_ids)."""
    e = pd.read_csv(path); n = len(sid); A = np.zeros((n, n), dtype=np.float32)
    for p, s in e[["prereq", "skill"]].values:
        if p in sid and s in sid: A[sid[s], sid[p]] = 1
    return A

def split_users(seqs, seed=0, frac=(0.7, 0.15, 0.15)):
    """Split BY LEARNER so no learner appears in two splits."""
    idx = np.random.default_rng(seed).permutation(len(seqs))
    a, b = int(frac[0] * len(seqs)), int((frac[0] + frac[1]) * len(seqs))
    pick = lambda ii: [seqs[i] for i in ii]
    return pick(idx[:a]), pick(idx[a:b]), pick(idx[b:])

def make_samples(seqs, n, cuts=(5, 10, 20, 40), n_targets=10, feat=None):
    feat = feat or D.node_features
    X, TC, TY, K, U = [], [], [], [], []
    for u, c, y in seqs:
        for k in cuts:
            if len(c) >= k + n_targets:
                X.append(feat(c[:k], y[:k], n))
                TC.append(c[k:k + n_targets]); TY.append(y[k:k + n_targets]); K.append(k); U.append(u)
    return np.array(X, np.float32), np.array(TC), np.array(TY, np.float32), np.array(K), np.array(U)
