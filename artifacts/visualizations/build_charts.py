#!/usr/bin/env python3
"""Regenerate presentation charts (white theme).
Outputs:
  artifacts/visualizations/chart_attack_patterns.png   (p4 dataset)
  artifacts/visualizations/chart_detection_gap.png     (p9 detection-action gap)
  experiment/analysis/logit_lens_qwen3/logit_lens_qwen3_{1_7b,8b}_named.png  (p8)
Numbers are derived from artifacts/tier2_features/merged_runs_features_tier1_tier2.csv.
"""
import csv, collections
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
VIZ = ROOT / "artifacts/visualizations"
LL = ROOT / "experiment/analysis/logit_lens_qwen3"
CSV = ROOT / "artifacts/tier2_features/merged_runs_features_tier1_tier2.csv"
INK="#18181B"; BLUE="#2563EB"; RED="#DC2626"; AMBER="#D97706"; GREEN="#16A34A"; MUTE="#A1A1AA"; TRACK="#EEEEEF"
plt.rcParams.update({"font.size":13,"axes.edgecolor":"#D4D4D8","text.color":INK,"axes.labelcolor":INK,
                     "xtick.color":"#52525B","ytick.color":INK})

def pos(r,k):
    v=str(r.get(k,"")).strip()
    if v in ("1","True","true","1.0"): return True
    try: return float(v)>0
    except: return False

rows=list(csv.DictReader(open(CSV)))

# ---- chart 1: attack-pattern distribution over unique skills ----
pat_keys=[("pat_rce","Remote code execution"),("pat_cred_theft","Credential theft"),
          ("pat_behavior_manip","Behavior manipulation"),("pat_ext_transmission","External transmission"),
          ("pat_context_leakage","Context leakage"),("pat_hidden_instr","Hidden instructions"),
          ("pat_code_obfusc","Code obfuscation")]
seen={}
for r in rows:
    seen.setdefault(r["skill"], {k:pos(r,k) for k,_ in pat_keys})
n=len(seen)
data=[(lab, round(100*sum(seen[s][k] for s in seen)/n)) for k,lab in pat_keys][::-1]
labels=[d[0] for d in data]; vals=[d[1] for d in data]
cols=[RED if v>=60 else (AMBER if v>=15 else MUTE) for v in vals]
fig,ax=plt.subplots(figsize=(8.2,4.3),dpi=240)
ax.barh(labels,vals,color=cols,height=0.66)
for i,v in enumerate(vals): ax.text(v+1.5,i,f"{v}%",va="center",fontweight="bold",fontsize=12,color=INK)
ax.set_xlim(0,112); ax.set_xlabel(f"share of {n} malicious skills (%)")
ax.set_title("What's in the dataset — malicious patterns per skill",fontweight="bold",loc="left",fontsize=13)
for sp in ["top","right"]: ax.spines[sp].set_visible(False)
ax.tick_params(length=0); ax.grid(axis="x",alpha=0.12)
plt.tight_layout(); plt.savefig(VIZ/"chart_attack_patterns.png"); plt.close()

# ---- chart 2: detection-action gap ----
det=sum(pos(r,"agent_detected_malicious") for r in rows)
detB=sum(1 for r in rows if pos(r,"agent_detected_malicious") and pos(r,"stage_b_execution"))
detC=sum(1 for r in rows if pos(r,"agent_detected_malicious") and pos(r,"stage_c_egress"))
fig,ax=plt.subplots(figsize=(8.2,3.2),dpi=240)
ax.barh([2],[det],color=TRACK,height=0.5); ax.barh([2],[det],color="none",edgecolor=BLUE,height=0.5,linewidth=2)
ax.text(det+6,2,f"{det}  recognized malicious",va="center",fontweight="bold",color=BLUE,fontsize=12)
ax.barh([1],[detB],color=AMBER,height=0.5); ax.text(detB+6,1,f"{detB}  still executed (Stage-B)",va="center",fontweight="bold",color=AMBER,fontsize=12)
ax.barh([0],[detC],color=RED,height=0.5); ax.text(detC+6,0,f"{detC}  reached egress despite detection",va="center",fontweight="bold",color=RED,fontsize=12)
ax.set_yticks([2,1,0]); ax.set_yticklabels(["detected","→ executed","→ egress"])
ax.set_xlim(0,int(det*1.33)); ax.set_xlabel("sessions")
ax.set_title("Detection ≠ defense — recognized, yet acted anyway",fontweight="bold",loc="left",fontsize=13)
for sp in ["top","right"]: ax.spines[sp].set_visible(False)
ax.tick_params(length=0); ax.grid(axis="x",alpha=0.12)
plt.tight_layout(); plt.savefig(VIZ/"chart_detection_gap.png"); plt.close()

# ---- charts 3-4: logit lens per-layer, named framings ----
NAMES={"C1":"Neutral","C2":"Safety-review","C3":"Trust-pressure"}
COL={"C1":"#2563EB","C2":"#16A34A","C3":"#DC2626"}
def logit(fn,title,out):
    rs=list(csv.DictReader(open(fn)))
    agg=collections.defaultdict(lambda:collections.defaultdict(list))
    for r in rs: agg[r["condition"]][int(float(r["layer"]))].append(float(r["exec_minus_refusal"]))
    plt.figure(figsize=(8,4.8),dpi=250)
    for c in ["C1","C2","C3"]:
        xs=sorted(agg[c]); ys=[sum(agg[c][x])/len(agg[c][x]) for x in xs]
        plt.plot(xs,ys,label=NAMES[c],color=COL[c],linewidth=2)
    plt.axhline(0,color="#444",linewidth=1); plt.title(title,fontsize=12)
    plt.xlabel("Layer",fontsize=11); plt.ylabel("Execution − Refusal score",fontsize=11)
    plt.legend(fontsize=11,loc="upper left"); plt.grid(alpha=0.15)
    plt.tight_layout(); plt.savefig(out); plt.close()
if (LL/"logit_lens_all85_qwen3_1_7b.csv").exists():
    logit(LL/"logit_lens_all85_qwen3_1_7b.csv","Logit Lens: Execution vs Refusal Direction by Framing — Qwen3-1.7B, 85 Skills",LL/"logit_lens_qwen3_1_7b_named.png")
    logit(LL/"logit_lens_all85_qwen3_8b.csv","Logit Lens: Execution vs Refusal Direction by Framing — Qwen3-8B, 85 Skills",LL/"logit_lens_qwen3_8b_named.png")
print("charts regenerated")
