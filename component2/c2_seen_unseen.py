"""Component 2 - does the graph help most on skills the learner has NEVER attempted? (cold-start at skill level)
Usage: python c2_seen_unseen.py --data skill_builder_data_corrected_collapsed.csv --seeds 0 1 2
Trains GNN (graph) and the same network without graph; scores test targets split by seen/unseen skill."""
import argparse, copy, numpy as np, pandas as pd, torch, torch.nn.functional as F
import c2_assist_data as A, c2_data as D
from c2_model import PedGNN, ece, auc, gather, mc_predict

ap = argparse.ArgumentParser()
ap.add_argument("--data", required=True); ap.add_argument("--graph", default=None)
ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2]); ap.add_argument("--dropout", type=float, default=0.1)
ap.add_argument("--mc", type=int, default=30); ap.add_argument("--epochs", type=int, default=60)
args = ap.parse_args(); DEV = "cpu"

seqs, N, names, sid = A.load_assistments(args.data)
tr_s, va_s, te_s = A.split_users(seqs)
adj = A.load_graph_csv(args.graph, sid) if args.graph else A.proxy_graph(tr_s, N)
A_pre = torch.tensor(D.row_norm(adj)); A_suc = torch.tensor(D.row_norm(adj.T.copy()))
tr, va, te = [A.make_samples(s, N, feat=D.node_features_v2) for s in (tr_s, va_s, te_s)]
unseen = gather(te[0][:, :, 2], te[1]).ravel() == 0          # target skill had 0 attempts in the prefix
y = te[2].ravel()
print(f"test targets: {len(y)} | on never-attempted skills: {unseen.sum()} ({100*unseen.mean():.0f}%) | on attempted skills: {(~unseen).sum()}")

def predict(model, X, T):
    out = []
    for i in range(0, len(X), 256):
        m, _, _ = mc_predict(model, torch.tensor(X[i:i+256]), A_pre, A_suc, T); out.append(m)
    return torch.cat(out).numpy()

def train(use_graph, seed):
    torch.manual_seed(seed); np.random.seed(seed)
    model = PedGNN(N, in_dim=9, p=args.dropout, use_graph=use_graph); opt = torch.optim.Adam(model.parameters(), 1e-3, weight_decay=1e-5)
    X, TC, TY = [torch.tensor(a) for a in tr[:3]]; best, state, bad = 1e9, None, 0
    for ep in range(args.epochs):
        perm = torch.randperm(len(X))
        for i in range(0, len(perm), 128):
            b = perm[i:i+128]; lg = torch.gather(model(X[b], A_pre, A_suc), 1, TC[b])
            loss = F.binary_cross_entropy_with_logits(lg, TY[b]); opt.zero_grad(); loss.backward(); opt.step()
        pv = np.clip(gather(predict(model, va[0], 5), va[1]), 1e-6, 1 - 1e-6)
        v = -np.mean(va[2] * np.log(pv) + (1 - va[2]) * np.log(1 - pv))
        if v < best - 1e-4: best, state, bad = v, copy.deepcopy(model.state_dict()), 0
        else:
            bad += 1
            if bad >= 6: break
    model.load_state_dict(state); return model

rows = []
for sd in args.seeds:
    print(f"seed {sd} ...")
    for use_graph in (True, False):
        p = gather(predict(train(use_graph, sd), te[0], args.mc), te[1]).ravel()
        for grp, m in (("never-attempted skills", unseen), ("attempted skills", ~unseen)):
            rows.append(dict(seed=sd, model="GNN (graph)" if use_graph else "No graph", group=grp,
                             AUC=auc(p[m], y[m]), ECE=ece(p[m], y[m]), Brier=float(np.mean((p[m] - y[m]) ** 2))))
df = pd.DataFrame(rows); df.to_csv("seen_unseen_results.csv", index=False)
g = df.groupby(["group", "model"])[["AUC", "ECE", "Brier"]].agg(["mean", "std"]); g.columns = [f"{a}_{b}" for a, b in g.columns]
print("\n=== GRAPH vs NO GRAPH, by whether the learner had attempted the target skill (mean/std over seeds) ===")
print(g.round(4).to_string())
for grp in ("never-attempted skills", "attempted skills"):
    a = df[(df.group == grp) & (df.model == "GNN (graph)")].set_index("seed")["AUC"]
    b = df[(df.group == grp) & (df.model == "No graph")].set_index("seed")["AUC"]
    d = (a - b); print(f"AUC gain from the graph on {grp}: {d.mean():+.4f} (per seed: {', '.join(f'{x:+.4f}' for x in d)})")
