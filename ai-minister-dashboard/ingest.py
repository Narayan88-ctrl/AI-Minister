import os, argparse, pandas as pd, yaml

REQ_BUDGET = ["year","region","sector","program","amount_npr"]
REQ_PROJ   = ["project_name","region","sector","budget_npr","status"]

def load_map(path):
    with open(path,"r") as f: return yaml.safe_load(f)

def to_int(x):
    try: return int(str(x).replace(",","").replace(" ",""))
    except: return 0

def canon_sector(v,syn):
    v = (str(v) if v is not None else "").strip().lower()
    for k,als in syn.items():
        if v==k or any(a in v for a in als): return k.title()
    return v.title() if v else "Other"

def budgets(df, m, norm):
    df = df.rename(columns={v:k for k,v in m.items() if v in df.columns})
    for c in REQ_BUDGET:
        if c not in df: df[c]=None
    if norm.get("region_titlecase", True):
        df["region"]=df["region"].astype(str).str.title()
    df["year"]=df["year"].fillna(norm.get("guess_missing_year",2024))
    syn = norm.get("sector_synonyms", {})
    df["sector"]=df["sector"].apply(lambda x: canon_sector(x,syn))
    df["program"]=df["program"].fillna("Unspecified")
    df["amount_npr"]=df["amount_npr"].apply(to_int)
    return df[REQ_BUDGET]

def projects(df, m, norm):
    df = df.rename(columns={v:k for k,v in m.items() if v in df.columns})
    for c in REQ_PROJ:
        if c not in df: df[c]=None
    if norm.get("region_titlecase", True):
        df["region"]=df["region"].astype(str).str.title()
    syn = norm.get("sector_synonyms", {})
    df["sector"]=df["sector"].apply(lambda x: canon_sector(x,syn))
    df["project_name"]=df["project_name"].fillna("Unnamed Project")
    df["budget_npr"]=df["budget_npr"].apply(to_int)
    df["status"]=df["status"].fillna("ongoing").str.lower()
    return df[REQ_PROJ]

def main():
    p=argparse.ArgumentParser(); p.add_argument("--map",default="mapping.yaml")
    args=p.parse_args(); cfg=load_map(args.map); norm=cfg.get("normalization",{})
    bsrc=cfg["budgets"]["source_file"]; bmap=cfg["budgets"]["columns"]
    psrc=cfg["projects"]["source_file"]; pmap=cfg["projects"]["columns"]

    os.makedirs("data", exist_ok=True)
    bdf=pd.read_csv(bsrc); b_out=budgets(bdf,bmap,norm)
    b_out.to_csv("data/budgets_2024.csv",index=False)
    print(f"[OK] Wrote data/budgets_2024.csv ({len(b_out)} rows)")

    pdf=pd.read_csv(psrc); p_out=projects(pdf,pmap,norm)
    p_out.to_csv("data/projects.csv",index=False)
    print(f"[OK] Wrote data/projects.csv ({len(p_out)} rows)")

if __name__=="__main__":
    main()

