"""Component 2 - train + evaluate on ASSISTments.
Usage:
  python c2_train_assistments.py --data skill_builder_data_corrected.csv
  python c2_train_assistments.py --data ... --graph c1_edges.csv      # when Component 1's graph is ready
Outputs: results table (console), mastery_uncertainty.csv, reliability.png, uncertainty_vs_accuracy.png
"""
import argparse, copy, numpy as np, pandas as pd, torch, torch.nn.functional as F
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import c2_assist_data as A
from c2_model import PedGNN, mc_predict, ece, auc, gather

ap = argparse.ArgumentParser()
ap.add_argument("--data", required=True); ap.add_argument("--graph", default=None)
ap.add_argument("--epochs", type=int, default=60); ap.add_argument("--mc", type=int, default=30)
ap.add_argument("--mc_sweep", action="store_true"); ap.add_argument("--features", choices=["v1", "v2"], default="v1"); ap.add_argument("--seed", type=int, default=0)
args = ap.parse_args()
torch.manual_seed(args.seed); np.random.seed(args.seed)
DEV = "cuda" if torch.cuda.is_available() else "cpu"

seqs, N, names, sid = A.load_assistments(args.data)
tr_s, va_s, te_s = A.split_users(seqs)
print(f"learners {len(seqs)} (train {len(tr_s)}/val {len(va_s)}/test {len(te_s)}), skills {N}")
adj = A.load_graph_csv(args.graph, sid) if args.graph else A.proxy_graph(tr_s, N)
print(f"graph: {'Component 1' if args.graph else 'PROXY (data-derived)'} | edges {int(adj.sum())}")
import c2_data as D
A_pre = torch.tensor(D.row_norm(adj)).to(DEV); A_suc = torch.tensor(D.row_norm(adj.T.copy())).to(DEV)
FEAT = D.node_features_v2 if args.features == "v2" else D.node_features
IN = 9 if args.features == "v2" else 3
TAG = f"{args.features}_s{args.seed}"
print("features:", args.features, "| seed:", args.seed)
tr, va, te = [A.make_samples(s, N, feat=FEAT) for s in (tr_s, va_s, te_s)]
print("samples", len(tr[0]), len(va[0]), len(te[0]))

def predict(model, X, T):
    mu, sd, lg = [], [], []
    for i in range(0, len(X), 256):
        m, s, l = mc_predict(model, torch.tensor(X[i:i+256]).to(DEV), A_pre, A_suc, T)
        mu.append(m.cpu()); sd.append(s.cpu()); lg.append(l.cpu())
    return [torch.cat(z).numpy() for z in (mu, sd, lg)]

def train(use_graph):
    model = PedGNN(N, in_dim=IN, use_graph=use_graph).to(DEV)
    opt = torch.optim.Adam(model.parameters(), 1e-3, weight_decay=1e-5)
    X, TC, TY = [torch.tensor(a) for a in tr[:3]]
    best, best_state, bad = 1e9, None, 0
    for ep in range(args.epochs):
        perm = torch.randperm(len(X)); tot = 0
        for i in range(0, len(perm), 128):
            b = perm[i:i+128]
            lg = torch.gather(model(X[b].to(DEV), A_pre, A_suc), 1, TC[b].to(DEV))
            loss = F.binary_cross_entropy_with_logits(lg, TY[b].to(DEV))
            opt.zero_grad(); loss.backward(); opt.step(); tot += loss.item() * len(b)
        mu, _, _ = predict(model, va[0], 5)
        pv = np.clip(gather(mu, va[1]), 1e-6, 1 - 1e-6)
        vloss = -np.mean(va[2] * np.log(pv) + (1 - va[2]) * np.log(1 - pv))
        print(f"  [{'GNN' if use_graph else 'noGraph'}] epoch {ep:02d} train {tot/len(perm):.4f} val {vloss:.4f}")
        if vloss < best - 1e-4: best, best_state, bad = vloss, copy.deepcopy(model.state_dict()), 0
        else:
            bad += 1
            if bad >= 6: break
    model.load_state_dict(best_state); return model

def temperature(model):
    _, _, lg = predict(model, va[0], args.mc); lv = gather(lg, va[1])
    return min(np.linspace(0.5, 3, 26), key=lambda t: F.binary_cross_entropy_with_logits(
        torch.tensor(lv / t), torch.tensor(va[2])).item())

def evaluate(name, p, y):
    return dict(model=name, AUC=auc(p, y), ECE=ece(p, y), Brier=np.mean((p - y) ** 2))

gnn = train(True); T = temperature(gnn)
base = train(False)
y = te[2]; K = te[3]
mu, sd, lg = predict(gnn, te[0], args.mc)
p_raw = gather(mu, te[1]); p_cal = 1 / (1 + np.exp(-gather(lg, te[1]) / T)); s = gather(sd, te[1])
mu_b, _, lg_b = predict(base, te[0], args.mc); p_base = gather(mu_b, te[1])
p_skill = gather(te[0][:, :, 1], te[1])                       # smoothed per-skill accuracy so far
p_glob = np.full_like(y, tr[2].mean())
from c2_dkt import train_dkt, dkt_prefix_probs
dkt = train_dkt(tr_s, va_s, N, DEV)
p_dkt = dkt_prefix_probs(dkt, te_s, te[4], te[3], te[1], N, DEV)

res = pd.DataFrame([evaluate("Global mean", p_glob, y), evaluate("Per-skill accuracy", p_skill, y),
                    evaluate("DKT (LSTM)", p_dkt, y), evaluate("MC-Dropout NN (no graph)", p_base, y),
                    evaluate("GNN (raw)", p_raw, y), evaluate(f"GNN + temp scaling (T={T:.2f})", p_cal, y)])
print("\n=== TEST RESULTS ===\n", res.round(4).to_string(index=False))

print("\n=== COLD-START (by # past interactions) ===")
for k in sorted(set(K)):
    m = K == k
    print(f"k={k:>2}: GNN AUC {auc(p_cal[m], y[m]):.3f} | per-skill AUC {auc(p_skill[m], y[m]):.3f} | DKT AUC {auc(p_dkt[m], y[m]):.3f} "
          f"| ECE {ece(p_cal[m], y[m]):.3f} | mean uncertainty {s[m].mean():.3f}")

print("\n=== DOES UNCERTAINTY MEAN ANYTHING? (quartiles of std) ===")
q = np.quantile(s, [0.25, 0.5, 0.75]); bins = np.digitize(s, q); xs, accs = [], []
for b in range(4):
    m = bins == b; a_ = auc(p_cal[m], y[m]); err = np.abs(p_cal[m] - y[m]).mean(); xs.append(s[m].mean()); accs.append(a_)
    print(f"Q{b+1}: mean std {s[m].mean():.3f}  AUC {a_:.3f}  mean|p-y| {err:.3f}  ECE {ece(p_cal[m], y[m]):.3f}")

# Panel suggestion: does the number of MC Dropout passes (default 30) matter? No retraining needed:
# T is only used when predicting. Each T is repeated 5 times to see how much the answer "wobbles".
if args.mc_sweep:
    print("\n=== MC DROPOUT: NUMBER OF PASSES (T) SWEEP ===")
    sweep = []
    for Tmc in [2, 5, 10, 20, 30, 50, 100]:
        pm, ps = [], []
        for r in range(5):
            torch.manual_seed(1000 + r)
            m_, s_, _ = predict(gnn, te[0], Tmc)
            pm.append(gather(m_, te[1])); ps.append(gather(s_, te[1]))
        pm, ps = np.stack(pm), np.stack(ps); p_ = pm.mean(0)
        sweep.append(dict(T=Tmc, AUC=auc(p_, y), ECE=ece(p_, y), mean_uncertainty=ps.mean(),
                          mastery_wobble=pm.std(0).mean(), uncertainty_wobble=ps.std(0).mean(),
                          unc_vs_error_corr=np.corrcoef(ps.mean(0).ravel(), np.abs(p_ - y).ravel())[0, 1]))
    sw = pd.DataFrame(sweep); print(sw.round(4).to_string(index=False)); sw.to_csv(f"mc_sweep_{TAG}.csv", index=False)

# Deliverable: the two values (mastery, uncertainty) per learner-concept
mask = te[3] == 20; rows = []
for i in np.where(mask)[0]:
    for c in range(N):
        if te[0][i, c, 2] > 0:                                # concepts the learner has attempted
            rows.append((te[4][i], names.get(c, c), round(float(mu[i, c]), 3), round(float(sd[i, c]), 3)))
pd.DataFrame(rows, columns=["learner", "skill", "mastery", "uncertainty"]).to_csv(f"mastery_uncertainty_{TAG}.csv", index=False)

edges = np.linspace(0, 1, 11); rx, ry = [], []
for lo, hi in zip(edges[:-1], edges[1:]):
    m = (p_cal > lo) & (p_cal <= hi)
    if m.any(): rx.append(p_cal[m].mean()); ry.append(y[m].mean())
plt.figure(); plt.plot([0, 1], [0, 1], "--", c="gray"); plt.plot(rx, ry, "o-")
plt.xlabel("Predicted mastery"); plt.ylabel("Observed accuracy"); plt.title("Reliability (ASSISTments, test)")
plt.savefig(f"reliability_{TAG}.png", dpi=200, bbox_inches="tight")
plt.figure(); plt.plot(xs, accs, "o-"); plt.xlabel("Mean MC-Dropout std"); plt.ylabel("AUC")
plt.title("Higher uncertainty -> lower AUC?"); plt.savefig(f"uncertainty_vs_auc_{TAG}.png", dpi=200, bbox_inches="tight")
print(f"\nsaved outputs with tag {TAG}")
