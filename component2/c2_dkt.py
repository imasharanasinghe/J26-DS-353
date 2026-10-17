"""Deep Knowledge Tracing (LSTM) baseline, evaluated under the SAME protocol as the GNN:
state after k interactions -> per-skill probability -> score the next 10 responses."""
import copy, numpy as np, torch, torch.nn as nn, torch.nn.functional as F

class DKT(nn.Module):
    def __init__(self, n, hid=100, p=0.3):
        super().__init__()
        self.emb = nn.Embedding(2 * n + 1, hid, padding_idx=2 * n)
        self.rnn = nn.LSTM(hid, hid, batch_first=True)
        self.drop = nn.Dropout(p); self.out = nn.Linear(hid, n)
    def forward(self, x):
        h, _ = self.rnn(self.emb(x)); return self.out(self.drop(h))      # [B,T,N]

def _pad(seqs, n, L=300):
    X = np.full((len(seqs), L), 2 * n, dtype=np.int64); C = np.full((len(seqs), L), -1, dtype=np.int64)
    Y = np.zeros((len(seqs), L), dtype=np.float32)
    for i, (_, c, y) in enumerate(seqs):
        l = min(len(c), L); X[i, :l] = c[:l] + n * y[:l].astype(np.int64); C[i, :l] = c[:l]; Y[i, :l] = y[:l]
    return torch.tensor(X), torch.tensor(C), torch.tensor(Y)

def _loss(model, X, C, Y, dev):
    lg = model(X.to(dev))[:, :-1]; C1 = C[:, 1:].to(dev); m = C1 >= 0
    sel = torch.gather(lg, 2, C1.clamp(min=0).unsqueeze(-1)).squeeze(-1)
    return F.binary_cross_entropy_with_logits(sel[m], Y[:, 1:].to(dev)[m])

def train_dkt(tr_s, va_s, n, dev, epochs=40, patience=5):
    model = DKT(n).to(dev); opt = torch.optim.Adam(model.parameters(), 1e-3)
    Xt, Ct, Yt = _pad(tr_s, n); Xv, Cv, Yv = _pad(va_s, n)
    best, state, bad = 1e9, None, 0
    for ep in range(epochs):
        model.train(); perm = torch.randperm(len(Xt)); tot = 0
        for i in range(0, len(perm), 32):
            b = perm[i:i + 32]; loss = _loss(model, Xt[b], Ct[b], Yt[b], dev)
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 5.0); opt.step()
            tot += loss.item() * len(b)
        model.eval()
        with torch.no_grad(): v = _loss(model, Xv, Cv, Yv, dev).item()
        print(f"  [DKT] epoch {ep:02d} train {tot/len(perm):.4f} val {v:.4f}")
        if v < best - 1e-4: best, state, bad = v, copy.deepcopy(model.state_dict()), 0
        else:
            bad += 1
            if bad >= patience: break
    model.load_state_dict(state); return model

@torch.no_grad()
def dkt_prefix_probs(model, seqs, U, K, TC, n, dev):
    model.eval(); X, _, _ = _pad(seqs, n); row = {u: i for i, (u, _, _) in enumerate(seqs)}
    probs = torch.sigmoid(model(X.to(dev))).cpu().numpy()                 # [users,T,N]
    out = np.zeros(TC.shape, dtype=np.float32)
    for j, (u, k) in enumerate(zip(U, K)):
        out[j] = probs[row[u], k - 1][TC[j]]                              # state after k interactions
    return out
