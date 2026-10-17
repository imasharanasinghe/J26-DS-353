"""Component 2 - data layer (numpy only).
Synthetic prerequisite graph + simulated learners so you can build/test NOW.
Swap make_graph()/simulate_learners() for Component 1's graph + a real dataset
(e.g. Junyi Academy, which ships prerequisite relations) later; keep the same shapes.
"""
import numpy as np

def make_graph(n=40, max_parents=2, seed=0):
    """Random DAG. A_pre[i, j] = 1 means j is a prerequisite of i."""
    rng = np.random.default_rng(seed)
    A = np.zeros((n, n), dtype=np.float32)
    for i in range(1, n):
        k = rng.integers(0, min(max_parents, i) + 1)
        if k:
            A[i, rng.choice(i, size=k, replace=False)] = 1
    return A

def simulate_learners(A_pre, n_learners=600, seq_len=60, seed=1):
    """Latent mastery respects prerequisites; returns concepts[L,T], correct[L,T]."""
    rng = np.random.default_rng(seed)
    n = A_pre.shape[0]
    C = np.zeros((n_learners, seq_len), dtype=np.int64)
    Y = np.zeros((n_learners, seq_len), dtype=np.float32)
    for l in range(n_learners):
        theta = rng.normal()
        m = np.zeros(n)
        for j in range(n):  # indices are topologically ordered
            base = 1 / (1 + np.exp(-(1.5 * theta + rng.normal(0, 0.5) - 0.5)))
            par = np.where(A_pre[j] > 0)[0]
            m[j] = min(base, m[par].mean() + 0.15) if len(par) else base
        for t in range(seq_len):
            c = rng.integers(n)
            p = 0.1 + 0.8 * m[c]
            y = float(rng.random() < p)
            m[c] += 0.08 * (1 - m[c]) if y else 0.02 * (1 - m[c])
            C[l, t], Y[l, t] = c, y
    return C, Y

def node_features(concepts_prefix, correct_prefix, n):
    """Per-concept learner state from an interaction prefix -> [n, 3]."""
    att = np.zeros(n, dtype=np.float32); cor = np.zeros(n, dtype=np.float32)
    for c, y in zip(concepts_prefix, correct_prefix):
        att[c] += 1; cor[c] += y
    return np.stack([np.log1p(att), (cor + 1) / (att + 2), (att > 0).astype(np.float32)], 1)

def build_samples(C, Y, n, prefix_lens=(3, 8, 15, 30), n_targets=10):
    """Each sample = learner state after k interactions; targets = next n_targets responses."""
    X, TC, TY, K = [], [], [], []
    for l in range(C.shape[0]):
        for k in prefix_lens:
            X.append(node_features(C[l, :k], Y[l, :k], n))
            TC.append(C[l, k:k + n_targets]); TY.append(Y[l, k:k + n_targets]); K.append(k)
    return (np.array(X, dtype=np.float32), np.array(TC), np.array(TY, dtype=np.float32), np.array(K))

def row_norm(A):
    d = A.sum(1, keepdims=True); d[d == 0] = 1
    return (A / d).astype(np.float32)


def node_features_v2(c, y, n):
    """v1 features + recency: last outcome, current streak, how recently touched,
    'is this the skill the learner is working on right now', and global recent accuracy/length. -> [n, 9]"""
    k = len(c)
    att = np.zeros(n, np.float32); cor = np.zeros(n, np.float32)
    last = np.full(n, 0.5, np.float32); streak = np.zeros(n, np.float32); gap = np.full(n, np.inf)
    for t, (ci, yi) in enumerate(zip(c, y)):
        att[ci] += 1; cor[ci] += yi; last[ci] = yi
        streak[ci] = streak[ci] + 1 if yi > 0 else 0
        gap[ci] = k - 1 - t
    rec = np.where(np.isfinite(gap), np.exp(-np.where(np.isfinite(gap), gap, 0) / 20.0), 0.0).astype(np.float32)
    is_last = np.zeros(n, np.float32)
    if k: is_last[c[-1]] = 1
    g_acc = np.full(n, np.mean(y[-10:]) if k else 0.5, np.float32)
    g_len = np.full(n, np.log1p(k) / 5, np.float32)
    return np.stack([np.log1p(att), (cor + 1) / (att + 2), (att > 0).astype(np.float32), last,
                     np.minimum(streak, 3) / 3, rec, is_last, g_acc, g_len], 1)
