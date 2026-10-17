"""Component 2 - final model + live demo.
 1) Train the final model once and save it (about 1-2 minutes):
      python c2_demo.py --data skill_builder_data_corrected_collapsed.csv --train
 2) See some unseen test learners:      python c2_demo.py --list
 3) Show one learner's mastery + uncertainty (fast):   python c2_demo.py --learner 12345 --k 20
Final setting: v2 features, dropout 0.1, 30 MC passes. Add --graph c1_edges.csv when Component 1's graph is ready.
"""
import argparse, copy, os, pickle, numpy as np, torch, torch.nn.functional as F
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import c2_assist_data as A, c2_data as D
from c2_model import PedGNN, mc_predict, gather

ap = argparse.ArgumentParser()
ap.add_argument("--data"); ap.add_argument("--graph", default=None); ap.add_argument("--train", action="store_true")
ap.add_argument("--list", action="store_true"); ap.add_argument("--learner", type=int); ap.add_argument("--k", type=int, default=20)
ap.add_argument("--dropout", type=float, default=0.1); ap.add_argument("--mc", type=int, default=30); ap.add_argument("--seed", type=int, default=0)
args = ap.parse_args()
CACHE, MODEL = "demo_cache.pkl", "demo_model.pt"; DEV = "cpu"

def train_final():
    seqs, N, names, sid = A.load_assistments(args.data)
    tr_s, va_s, te_s = A.split_users(seqs)
    adj = A.load_graph_csv(args.graph, sid) if args.graph else A.proxy_graph(tr_s, N)
    A_pre = torch.tensor(D.row_norm(adj)); A_suc = torch.tensor(D.row_norm(adj.T.copy()))
    tr, va = [A.make_samples(s, N, feat=D.node_features_v2) for s in (tr_s, va_s)]
    torch.manual_seed(args.seed); np.random.seed(args.seed)
    model = PedGNN(N, in_dim=9, p=args.dropout); opt = torch.optim.Adam(model.parameters(), 1e-3, weight_decay=1e-5)
    X, TC, TY = [torch.tensor(a) for a in tr[:3]]; best, state, bad = 1e9, None, 0
    for ep in range(60):
        perm = torch.randperm(len(X))
        for i in range(0, len(perm), 128):
            b = perm[i:i+128]
            lg = torch.gather(model(X[b], A_pre, A_suc), 1, TC[b])
            loss = F.binary_cross_entropy_with_logits(lg, TY[b]); opt.zero_grad(); loss.backward(); opt.step()
        mu, _, _ = mc_predict(model, torch.tensor(va[0]), A_pre, A_suc, 5)
        pv = np.clip(gather(mu.numpy(), va[1]), 1e-6, 1 - 1e-6)
        v = -np.mean(va[2] * np.log(pv) + (1 - va[2]) * np.log(1 - pv)); print(f"  epoch {ep:02d} val loss {v:.4f}")
        if v < best - 1e-4: best, state, bad = v, copy.deepcopy(model.state_dict()), 0
        else:
            bad += 1
            if bad >= 6: break
    torch.save({"state": state, "p": args.dropout, "N": N}, MODEL)
    pickle.dump(dict(N=N, names=names, adj=adj, test={u: (c, y) for u, c, y in te_s}), open(CACHE, "wb"))
    print("\nSaved demo_model.pt and demo_cache.pkl. Now run:  python c2_demo.py --list")

if args.train:
    train_final(); raise SystemExit
if not (os.path.exists(CACHE) and os.path.exists(MODEL)):
    raise SystemExit("Run first:  python c2_demo.py --data skill_builder_data_corrected_collapsed.csv --train")

cache = pickle.load(open(CACHE, "rb")); N, names, adj, test = cache["N"], cache["names"], cache["adj"], cache["test"]
ck = torch.load(MODEL); model = PedGNN(N, in_dim=9, p=ck["p"]); model.load_state_dict(ck["state"])
A_pre = torch.tensor(D.row_norm(adj)); A_suc = torch.tensor(D.row_norm(adj.T.copy()))

if args.list:
    print("Unseen test learners (learner id | number of recorded answers):")
    for u, (c, y) in list(test.items())[:15]: print(f"  {u} | {len(c)}")
    raise SystemExit
if args.learner is None: raise SystemExit("Use --list to see learner ids, then --learner <id>")

c, y = test[args.learner]; k = args.k
if len(c) < k + 10: raise SystemExit(f"Learner has only {len(c)} answers; use a smaller --k (needs at least k+10)")
f = D.node_features_v2(c[:k], y[:k], N)
with torch.no_grad():
    P = torch.stack([torch.sigmoid(model(torch.tensor(f[None]), A_pre, A_suc)) for _ in range(args.mc)])[:, 0].numpy()
mu, sd = P.mean(0), P.std(0, ddof=1)
att = np.zeros(N); cor = np.zeros(N)
for ci, yi in zip(c[:k], y[:k]): att[ci] += 1; cor[ci] += yi
seen = np.where(att > 0)[0]; seen = seen[np.argsort(-att[seen])][:10]
has_pre = [i for i in range(N) if att[i] == 0 and adj[i].sum() > 0 and (att[np.where(adj[i] > 0)[0]] > 0).any()]
unseen = sorted(has_pre, key=lambda i: -mu[i])[:4]
def nm(i):
    n = names.get(i)
    return (f"{n[:26]} [#{i}]" if isinstance(n, str) and n.strip() else f"skill [#{i}]")
print(f"\nLearner {args.learner} after {k} answers ({args.mc} MC Dropout passes)\n")
print(f"{'skill':36}{'answers':>8}{'past acc':>10}{'MASTERY':>9}{'UNCERTAINTY':>13}")
rows = [(i, True) for i in seen] + [(i, False) for i in unseen]
for i, s_ in rows:
    pa = f"{cor[i]/att[i]:.2f}" if att[i] else "never"
    print(f"{nm(i):36}{int(att[i]):>8}{pa:>10}{mu[i]:>9.2f}{sd[i]:>13.3f}")
tc, ty = c[k:k + 10], y[k:k + 10]
print(f"\nCheck on the learner's real next 10 answers: predicted correct {mu[tc].mean():.2f} | actual correct {ty.mean():.2f}")
print("(skills marked 'never' were not attempted yet: their mastery comes from prerequisite skills via the graph)")

idx = [i for i, _ in rows][::-1]
plt.figure(figsize=(7.5, 0.45 * len(idx) + 1.4))
plt.barh([nm(i) for i in idx], [mu[i] for i in idx], xerr=[2 * sd[i] for i in idx], capsize=3,
         color=["#4c78a8" if att[i] else "#f58518" for i in idx])
plt.xlim(0, 1); plt.xlabel("Predicted mastery (bar) with uncertainty (whisker = 2 x std)")
plt.title(f"Learner {args.learner} after {k} answers   (blue = attempted, orange = not attempted yet)", fontsize=9)
plt.savefig(f"demo_learner_{args.learner}.png", dpi=200, bbox_inches="tight"); print(f"saved demo_learner_{args.learner}.png")
