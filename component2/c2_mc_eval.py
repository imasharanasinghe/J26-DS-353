"""Component 2 - dedicated MC Dropout evaluation (GNN, v2 features). Version 2: compares several uncertainty measures
(MC std, MC logit-std, mutual information) against a probability-only baseline, incl. a within-probability-band test.
Answers: (1) does MC Dropout beat a single deterministic pass?  (2) is the uncertainty useful for spotting
errors?  (3) does it carry information BEYOND the predicted probability itself?  (4) effect of dropout rate.
Usage:
  python c2_mc_eval.py --data skill_builder_data_corrected_collapsed.csv --dropouts 0.25 --seeds 0 1 2
  python c2_mc_eval.py --data skill_builder_data_corrected_collapsed.csv --dropouts 0.1 0.4 --seeds 0 1 2
"""
import argparse, copy, time, numpy as np, pandas as pd, torch, torch.nn.functional as F
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import c2_assist_data as A, c2_data as D
from c2_model import PedGNN, ece, auc, gather, mc_predict

ap = argparse.ArgumentParser()
ap.add_argument("--data", required=True); ap.add_argument("--graph", default=None)
ap.add_argument("--dropouts", type=float, nargs="+", default=[0.25]); ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
ap.add_argument("--mc", type=int, default=30); ap.add_argument("--epochs", type=int, default=60)
args = ap.parse_args()
DEV = "cuda" if torch.cuda.is_available() else "cpu"
TAG = "p" + "_".join(str(d) for d in args.dropouts)

seqs, N, names, sid = A.load_assistments(args.data)
tr_s, va_s, te_s = A.split_users(seqs)
adj = A.load_graph_csv(args.graph, sid) if args.graph else A.proxy_graph(tr_s, N)
A_pre = torch.tensor(D.row_norm(adj)).to(DEV); A_suc = torch.tensor(D.row_norm(adj.T.copy())).to(DEV)
tr, va, te = [A.make_samples(s, N, feat=D.node_features_v2) for s in (tr_s, va_s, te_s)]
print(f"learners {len(seqs)} | skills {N} | graph {'Component 1' if args.graph else 'PROXY'} edges {int(adj.sum())} | samples {len(tr[0])}/{len(va[0])}/{len(te[0])}")

def predict(model, X, T):
    mu, sd = [], []
    for i in range(0, len(X), 256):
        m, s, _ = mc_predict(model, torch.tensor(X[i:i+256]).to(DEV), A_pre, A_suc, T)
        mu.append(m.cpu()); sd.append(s.cpu())
    return torch.cat(mu).numpy(), torch.cat(sd).numpy()

@torch.no_grad()
def det_predict(model, X):                       # ONE pass with dropout switched OFF
    old = model.p; model.p = 0.0; out = []
    for i in range(0, len(X), 256):
        out.append(torch.sigmoid(model(torch.tensor(X[i:i+256]).to(DEV), A_pre, A_suc)).cpu())
    model.p = old; return torch.cat(out).numpy()

def train_gnn(p, seed):
    torch.manual_seed(seed); np.random.seed(seed)
    model = PedGNN(N, in_dim=9, p=p).to(DEV); opt = torch.optim.Adam(model.parameters(), 1e-3, weight_decay=1e-5)
    X, TC, TY = [torch.tensor(a) for a in tr[:3]]; best, state, bad = 1e9, None, 0
    for ep in range(args.epochs):
        perm = torch.randperm(len(X))
        for i in range(0, len(perm), 128):
            b = perm[i:i+128]
            lg = torch.gather(model(X[b].to(DEV), A_pre, A_suc), 1, TC[b].to(DEV))
            loss = F.binary_cross_entropy_with_logits(lg, TY[b].to(DEV)); opt.zero_grad(); loss.backward(); opt.step()
        mu, _ = predict(model, va[0], 5); pv = np.clip(gather(mu, va[1]), 1e-6, 1 - 1e-6)
        v = -np.mean(va[2] * np.log(pv) + (1 - va[2]) * np.log(1 - pv))
        if v < best - 1e-4: best, state, bad = v, copy.deepcopy(model.state_dict()), 0
        else:
            bad += 1
            if bad >= 6: break
    model.load_state_dict(state); print(f"    trained {ep+1} epochs, best val loss {best:.4f}"); return model

def spearman(a, b):
    return np.corrcoef(a.argsort().argsort().astype(float), b.argsort().argsort().astype(float))[0, 1]

def brier(p, y): return float(np.mean((p - y) ** 2))

def keep_lowest(score, frac):                     # indices of the `frac` most-confident predictions
    return np.argsort(score, kind="stable")[: max(int(frac * len(score)), 50)]

def within_band_auroc(score, wrong, p, bands=5):
    """Error-detection AUROC *inside* narrow probability bands: does the score know anything the probability doesn't?"""
    edges = np.quantile(p, np.linspace(0, 1, bands + 1)); out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p >= lo) & (p <= hi)
        if m.sum() > 50 and 0 < wrong[m].sum() < m.sum(): out.append(auc(score[m], wrong[m]))
    return float(np.mean(out)) if out else float("nan")

@torch.no_grad()
def mc_passes(model, X, T):
    out = []
    for i in range(0, len(X), 256):
        xb = torch.tensor(X[i:i+256]).to(DEV)
        out.append(torch.stack([torch.sigmoid(model(xb, A_pre, A_suc)) for _ in range(T)]).cpu())
    return torch.cat(out, 1).numpy()                                   # [T, B, N]

def _ent(q): return -(q * np.log(q) + (1 - q) * np.log(1 - q))

def evaluate(model, seed):
    torch.manual_seed(1000 + seed)
    y = te[2].ravel(); Kt = np.repeat(te[3], te[1].shape[1])
    G = lambda M: gather(M, te[1]).ravel()
    p_det = G(det_predict(model, te[0]))
    P = mc_passes(model, te[0], args.mc); Pc = np.clip(P, 1e-6, 1 - 1e-6)
    mu = P.mean(0); lg = np.log(Pc / (1 - Pc))
    mi = _ent(np.clip(mu, 1e-6, 1 - 1e-6)) - _ent(Pc).mean(0)           # mutual information (epistemic part)
    p = G(mu)
    unc = {"mc_std": G(P.std(0, ddof=1)), "mc_logit_std": G(lg.std(0, ddof=1)), "mc_MI": G(mi), "prob_only": 1 - np.abs(2 * p - 1)}
    unc["rand"] = np.random.default_rng(seed).random(len(p))
    wrong = ((p > 0.5) != (y > 0.5)).astype(float)
    r = dict(AUC_det=auc(p_det, y), ECE_det=ece(p_det, y), Brier_det=brier(p_det, y),
             AUC_mc=auc(p, y), ECE_mc=ece(p, y), Brier_mc=brier(p, y), Brier_full=brier(p, y))
    for nm, sc in unc.items():
        r[f"errAUROC_{nm}"] = auc(sc, wrong); r[f"band_{nm}"] = within_band_auroc(sc, wrong, p)
        r[f"Brier@60_{nm}"] = brier(p[keep_lowest(sc, 0.6)], y[keep_lowest(sc, 0.6)])
        if nm in ("mc_std", "mc_MI"):
            r[f"{nm}_k5"] = sc[Kt == 5].mean(); r[f"{nm}_k40"] = sc[Kt == 40].mean()
    return r, dict(p=p, p_det=p_det, y=y, unc=unc)

rows, first = [], None
for d in args.dropouts:
    for sd_ in args.seeds:
        print(f"\n--- dropout {d} | seed {sd_} ---"); t0 = time.time()
        m = train_gnn(d, sd_); r, arr = evaluate(m, sd_); r.update(dropout=d, seed=sd_); rows.append(r)
        if first is None: first = arr
        print(f"    done in {time.time()-t0:.0f}s | AUC det {r['AUC_det']:.4f} -> MC {r['AUC_mc']:.4f} | errAUROC std {r['errAUROC_mc_std']:.3f} MI {r['errAUROC_mc_MI']:.3f} prob-only {r['errAUROC_prob_only']:.3f}")

df = pd.DataFrame(rows); df.to_csv(f"mc_eval_runs_{TAG}.csv", index=False)
pd.set_option("display.width", 220)
def table(cols, title):
    g = df.groupby("dropout")[cols].agg(["mean", "std"]); g.columns = [f"{a}_{b}" for a, b in g.columns]
    print(f"\n=== {title} (mean/std over seeds; rows = dropout rate) ==="); print(g.round(4).to_string())
table(["AUC_det", "AUC_mc", "ECE_det", "ECE_mc", "Brier_det", "Brier_mc"], "1. MC DROPOUT vs SINGLE DETERMINISTIC PASS")
table([f"errAUROC_{n}" for n in ("mc_std", "mc_logit_std", "mc_MI", "prob_only", "rand")], "2. ERROR DETECTION AUROC (0.5 = useless)")
table([f"band_{n}" for n in ("mc_std", "mc_logit_std", "mc_MI", "prob_only")], "3. WITHIN-PROBABILITY-BAND AUROC (>0.5 = info BEYOND the probability)")
table([f"Brier@60_{n}" for n in ("mc_std", "mc_logit_std", "mc_MI", "prob_only", "rand")], "4. BRIER KEEPING THE 60% MOST CONFIDENT (lower = better)")
table(["mc_std_k5", "mc_std_k40", "mc_MI_k5", "mc_MI_k40"], "5. COLD-START CHECK: uncertainty should be HIGHER with 5 past answers than with 40")

cov = np.linspace(0.3, 1.0, 8); plt.figure(figsize=(6, 4.2))
for nm, lab in (("mc_std", "MC std"), ("mc_logit_std", "MC logit-std"), ("mc_MI", "MC mutual information"), ("prob_only", "Probability only"), ("rand", "Random")):
    sc = first["unc"][nm]; plt.plot(cov * 100, [brier(first["p"][keep_lowest(sc, c)], first["y"][keep_lowest(sc, c)]) for c in cov], "o-", label=lab)
plt.xlabel("Coverage: % of predictions kept (most confident first)"); plt.ylabel("Brier score (lower = better)")
plt.title("Risk-coverage"); plt.legend(fontsize=8); plt.savefig(f"mc_risk_coverage_{TAG}.png", dpi=200, bbox_inches="tight")
plt.figure(figsize=(5, 4)); plt.plot([0, 1], [0, 1], "--", c="gray"); e = np.linspace(0, 1, 11)
for lab, pp in (("Single pass (no MC)", first["p_det"]), (f"MC Dropout ({args.mc} passes)", first["p"])):
    xs, ys = zip(*[(pp[m].mean(), first["y"][m].mean()) for lo, hi in zip(e[:-1], e[1:]) if (m := (pp > lo) & (pp <= hi)).any()])
    plt.plot(xs, ys, "o-", label=lab)
plt.xlabel("Predicted mastery"); plt.ylabel("Observed accuracy"); plt.title("Reliability"); plt.legend()
plt.savefig(f"mc_reliability_{TAG}.png", dpi=200, bbox_inches="tight")
print(f"\nsaved mc_eval_runs_{TAG}.csv, mc_risk_coverage_{TAG}.png, mc_reliability_{TAG}.png")
