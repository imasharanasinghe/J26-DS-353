"""Component 2 - GNN learner model with Monte Carlo Dropout.
Run:  pip install torch numpy matplotlib   then   python c2_model.py
"""
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import c2_data as D

torch.manual_seed(0); np.random.seed(0)
N, T_MC, DEVICE = 40, 30, "cpu"

class PedGNN(nn.Module):
    """Relation-aware GCN: separate weights for self / prerequisites / successors,
    so mastery information flows along the prerequisite structure (cold-start handling)."""
    def __init__(self, n, in_dim=3, emb=16, hid=64, layers=2, p=0.25, use_graph=True):
        super().__init__()
        self.emb = nn.Embedding(n, emb); self.use_graph = use_graph; self.p = p
        d = in_dim + emb
        self.self_w = nn.ModuleList(); self.pre_w = nn.ModuleList(); self.suc_w = nn.ModuleList()
        for _ in range(layers):
            self.self_w.append(nn.Linear(d, hid)); self.pre_w.append(nn.Linear(d, hid, bias=False))
            self.suc_w.append(nn.Linear(d, hid, bias=False)); d = hid
        self.out = nn.Linear(hid, 1)

    def forward(self, x, A_pre, A_suc):            # x: [B,N,3]
        h = torch.cat([x, self.emb.weight.expand(x.size(0), -1, -1)], -1)
        for s, p, u in zip(self.self_w, self.pre_w, self.suc_w):
            msg = s(h)
            if self.use_graph:
                msg = msg + p(torch.einsum("ij,bjf->bif", A_pre, h)) + u(torch.einsum("ij,bjf->bif", A_suc, h))
            h = F.dropout(F.relu(msg), self.p, training=True)   # dropout ALWAYS on -> MC Dropout
        return self.out(h).squeeze(-1)             # logits [B,N]

@torch.no_grad()
def mc_predict(model, x, A_pre, A_suc, T=T_MC):
    logits = torch.stack([model(x, A_pre, A_suc) for _ in range(T)])   # [T,B,N]
    probs = torch.sigmoid(logits)
    return probs.mean(0), probs.std(0), logits.mean(0)                # mastery, uncertainty, mean logit

def ece(p, y, bins=10):
    p, y = p.ravel(), y.ravel(); e = 0.0
    edges = np.linspace(0, 1, bins + 1)
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p > lo) & (p <= hi)
        if m.any(): e += m.mean() * abs(p[m].mean() - y[m].mean())
    return e

def auc(p, y):
    p, y = p.ravel(), y.ravel(); r = p.argsort().argsort() + 1
    n1 = y.sum(); n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)

def gather(M, TC):  # M [B,N], TC [B,K] -> [B,K]
    return np.take_along_axis(M, TC, 1)

def run(use_graph=True, epochs=40):
    A = D.make_graph(N)
    A_pre = torch.tensor(D.row_norm(A)); A_suc = torch.tensor(D.row_norm(A.T.copy()))
    C, Y = D.simulate_learners(A, 900)
    split = lambda a, b: (C[a:b], Y[a:b])
    tr, va, te = [D.build_samples(*split(a, b), N) for a, b in [(0, 600), (600, 750), (750, 900)]]
    model = PedGNN(N, use_graph=use_graph); opt = torch.optim.Adam(model.parameters(), 1e-3, weight_decay=1e-5)
    Xtr, TCtr, TYtr = map(torch.tensor, tr[:3])
    for ep in range(epochs):
        perm = torch.randperm(len(Xtr)); tot = 0
        for i in range(0, len(perm), 64):
            b = perm[i:i + 64]
            lg = torch.gather(model(Xtr[b], A_pre, A_suc), 1, TCtr[b])
            loss = F.binary_cross_entropy_with_logits(lg, TYtr[b])
            opt.zero_grad(); loss.backward(); opt.step(); tot += loss.item() * len(b)
        if ep % 10 == 0: print(f"  epoch {ep:02d} loss {tot/len(perm):.4f}")
    # temperature scaling on validation (calibration step)
    mu, sd, lg = mc_predict(model, torch.tensor(va[0]), A_pre, A_suc)
    lgv, yv = gather(lg.numpy(), va[1]), va[2]
    T = min(np.linspace(0.5, 3, 26), key=lambda t: F.binary_cross_entropy_with_logits(
        torch.tensor(lgv / t), torch.tensor(yv)).item())
    # test
    mu, sd, lg = mc_predict(model, torch.tensor(te[0]), A_pre, A_suc)
    p_raw = gather(mu.numpy(), te[1]); p_cal = 1 / (1 + np.exp(-gather(lg.numpy(), te[1]) / T))
    s = gather(sd.numpy(), te[1]); y = te[2]; K = te[3]
    print(f"\n[{'GNN' if use_graph else 'No-graph baseline'}]  T={T:.2f}")
    print(f"  AUC {auc(p_raw,y):.3f} | ECE raw {ece(p_raw,y):.3f} -> calibrated {ece(p_cal,y):.3f}")
    for k in sorted(set(K)):   # cold-start analysis
        m = K == k
        print(f"  prefix={k:>2}: AUC {auc(p_cal[m],y[m]):.3f}  ECE {ece(p_cal[m],y[m]):.3f}  mean uncertainty {s[m].mean():.3f}")
    return p_cal, y

if __name__ == "__main__":
    p, y = run(True); run(False)
    # reliability diagram for the slides
    edges = np.linspace(0, 1, 11); xs, ys = [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p > lo) & (p <= hi)
        if m.any(): xs.append(p[m].mean()); ys.append(y[m].mean())
    plt.plot([0, 1], [0, 1], "--", c="gray"); plt.plot(xs, ys, "o-")
    plt.xlabel("Predicted mastery"); plt.ylabel("Observed accuracy"); plt.title("Reliability diagram (calibrated)")
    plt.savefig("reliability.png", dpi=200, bbox_inches="tight"); print("saved reliability.png")
