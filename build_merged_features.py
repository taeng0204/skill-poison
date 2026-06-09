#!/usr/bin/env python3
"""3개 clean CSV 통합 + Tier 1 피쳐(스킬/조건/모델) 추가."""
import csv, os, re, glob, json
from pathlib import Path

ROOT = Path('.')
SKILLS_DIR = ROOT / 'skills'
CSVS = [
    'agent_runs_summary_255_clean.csv',                          # qwen3:8b
    'agent_runs_summary_qwen3_1_7b_FULL_20260602_clean.csv',  # qwen3:1.7b
    'agent_runs_summary_codex_gpt5_4_20260602_clean.csv',        # gpt-5.4
    'agent_runs_summary_codex_gpt5_4_mini_20260602_clean.csv',   # gpt-5.4-mini
]
OUT = 'merged_runs_features_tier1.csv'

# ---------- 스킬 피쳐 추출 ----------
SENSITIVITY = {  # category -> tier
    'high': {'finance','healthcare','health','insurance','legal','realestate','hr'},
    'medium': {'ecommerce','food','travel','automotive','business','devops',
               'productivity','smarthome','utilities','communication','microsoft',
               'marketing','analytics','homeservices'},
    'low': {'entertainment','gaming','social','news','education','design','ai'},
}
SENS_ORD = {'low':0,'medium':1,'high':2}

def skill_features(skill_id):
    p = SKILLS_DIR / skill_id / 'SKILL.md'
    if not p.exists():
        return {'skill_category':'unknown','service_sensitivity':'unknown',
                'service_sensitivity_ord':'','n_credential_vars':'','n_risk_keywords':'',
                'has_rce':'','has_env_exfil':'','payload_type':'unknown',
                'skill_len_chars':'','n_code_blocks':'','n_steps':''}
    t = p.read_text(errors='replace')
    cat_m = re.search(r'(?im)^category:\s*(.+)$', t)
    cat = cat_m.group(1).strip().lower() if cat_m else 'unknown'
    sens = next((k for k,v in SENSITIVITY.items() if cat in v), 'unknown')
    cred = len(set(re.findall(r'canifi-env\s+set\s+([A-Z_]+)', t)))
    risk = len(re.findall(r'(?i)\b(curl|wget|install\.sh|sudo|eval|exec)\b|\|\s*bash', t))
    has_rce = bool(re.search(r'(?i)(curl|wget)[^\n]*\|\s*bash', t))
    has_env = bool(re.search(r'canifi-env', t))
    ptype = ('rce+env' if has_rce and has_env else 'rce' if has_rce
             else 'env' if has_env else 'other')
    n_blocks = t.count('```') // 2
    n_steps = len(re.findall(r'(?m)^\s*\d+\.\s', t))
    return {'skill_category':cat,'service_sensitivity':sens,
            'service_sensitivity_ord':SENS_ORD.get(sens,''),
            'n_credential_vars':cred,'n_risk_keywords':risk,
            'has_rce':has_rce,'has_env_exfil':has_env,'payload_type':ptype,
            'skill_len_chars':len(t),'n_code_blocks':n_blocks,'n_steps':n_steps}

# 85개 스킬 피쳐 캐시
SKILL_CACHE = {d.name: skill_features(d.name)
               for d in SKILLS_DIR.iterdir() if (d/'SKILL.md').exists()}

# ---------- HF MASW 원본 공격 패턴 피쳐 ----------
# hf.co/datasets/ProtectSkills/MaliciousAgentSkillsBench (malicious_skills.csv)
PAT_SLUG = {
    'Remote Code Execution':'rce','Network sniffing / Credential theft':'cred_theft',
    'Behavior Manipulation':'behavior_manip','External Transmission':'ext_transmission',
    'Context Leakage':'context_leakage','Hidden Instructions':'hidden_instr',
    'Code Obfuscation':'code_obfusc','Instruction Override':'instr_override',
    'Excessive Permissions':'excess_perms','Hardcoded Tokens':'hardcoded_tokens',
    'File System Scan':'fs_scan','Data Exfiltration':'data_exfil',
}
def load_hf_patterns():
    p = ROOT / 'data' / 'masw_malicious_skills.csv'
    cache = {}
    if not p.exists():
        return cache, []
    for r in csv.DictReader(open(p, encoding='utf-8-sig')):
        pats = [x.strip() for x in (r.get('Pattern') or '').split(';') if x.strip()]
        feat = {'hf_classification': r.get('classification',''),
                'hf_source': r.get('source',''),
                'n_attack_patterns': len(pats)}
        for full,slug in PAT_SLUG.items():
            feat[f'pat_{slug}'] = 1 if full in pats else 0
        cache[r['skill_name']] = feat
    return cache, ['hf_classification','hf_source','n_attack_patterns'] + [f'pat_{s}' for s in PAT_SLUG.values()]

HF_CACHE, HF_COLS = load_hf_patterns()
def hf_features(skill_id):
    return HF_CACHE.get(skill_id, {c:'' for c in HF_COLS})

# ---------- 모델 피쳐 ----------
def model_features(model):
    m = (model or '').lower()
    if m.startswith('qwen'):
        fam='qwen'; align='weak'
        size = 8.0 if '8b' in m else 1.7 if '1.7b' in m or '1_7b' in m else 4.0 if '4b' in m else ''
        tier = 'small' if (size and size<3) else 'medium'
    elif 'gpt' in m or 'codex' in m:
        fam='openai'; align='strong'
        size=''  # 비공개
        tier = 'mini' if 'mini' in m else 'large'
    else:
        fam='other'; align='unknown'; size=''; tier='unknown'
    return {'model_family':fam,'model_size_b':size,'model_tier':tier,'alignment_tier':align}

# ---------- 조건 피쳐 ----------
def cond_features(c):
    return {'trust_pressure':1 if c=='C3' else 0,
            'safety_review':1 if c=='C2' else 0,
            'condition_label':{'C1':'neutral','C2':'safety_review','C3':'trust_pressure'}.get(c,c)}

# ---------- 통합 ----------
all_rows=[]
base_cols=None
for f in CSVS:
    if not os.path.exists(f):
        print(f"⚠️ 없음: {f}"); continue
    rows=list(csv.DictReader(open(f, encoding='utf-8-sig')))
    if base_cols is None: base_cols=list(rows[0].keys())
    for r in rows:
        sk=r.get('skill','')
        feat={}
        feat.update(SKILL_CACHE.get(sk, skill_features(sk)))
        feat.update(hf_features(sk))
        feat.update(model_features(r.get('model','')))
        feat.update(cond_features(r.get('condition','')))
        r.update(feat)
        all_rows.append(r)

new_cols=['skill_category','service_sensitivity','service_sensitivity_ord',
          'n_credential_vars','n_risk_keywords','has_rce','has_env_exfil','payload_type',
          'skill_len_chars','n_code_blocks','n_steps',
          'model_family','model_size_b','model_tier','alignment_tier',
          'trust_pressure','safety_review','condition_label']
cols = base_cols + new_cols + HF_COLS

with open(OUT,'w',newline='',encoding='utf-8-sig') as fh:
    w=csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore')
    w.writeheader(); w.writerows(all_rows)

print(f"✅ {OUT}  ({len(all_rows)}행, {len(cols)}컬럼)")
print(f"   기존 {len(base_cols)} + 신규 Tier1 {len(new_cols)}")
from collections import Counter
print("   모델:", dict(Counter(r['model'] for r in all_rows)))
print("   누락 스킬(피쳐 unknown):", sum(1 for r in all_rows if r.get('skill_category')=='unknown'))
