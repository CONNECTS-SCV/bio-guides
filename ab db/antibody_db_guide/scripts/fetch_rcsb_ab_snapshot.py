"""fetch_rcsb_ab_snapshot.py — RCSB에서 항체-항원 복합체 스냅샷을 직접 받아온다 (Ch.02).

SAbDab·Thera-SAbDab 웹 UI는 스크립트로 바로 긁기 어려워요(React 앱). 대신 같은 원본
(PDB)을 RCSB **Search API + Data API**로 조회해 "SAbDab스러운" 요약 표를 직접 만듭니다.

  1) Search API : X-ray ≤ 2.5 Å + 단백질 entity ≥ 3 + full-text "Fab antibody complex"
                  → release date 오름차순 상위 N개 entry (오래된 순이라 결과가 안정적)
  2) Data API   : 한 번의 GraphQL 요청으로 entry 메타데이터 + polymer entity 설명/사슬 ID
  3) entity 설명에서 heavy / light / antigen 사슬 역할을 파생

실행:
  python scripts/fetch_rcsb_ab_snapshot.py --rows 12 --out 02_databases/my_run/rcsb_ab_complexes.csv
"""
import argparse
import csv
import json
import pathlib
import sys

import requests

SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
GRAPHQL_URL = "https://data.rcsb.org/graphql"

GQL = """query($ids:[String!]!){ entries(entry_ids:$ids){
  rcsb_id
  struct{ title }
  rcsb_entry_info{ resolution_combined experimental_method }
  rcsb_accession_info{ initial_release_date }
  polymer_entities{
    rcsb_polymer_entity{ pdbx_description }
    rcsb_polymer_entity_container_identifiers{ auth_asym_ids }
    entity_poly{ rcsb_sample_sequence_length }
  }
} }"""

FIELDS = ["pdb_id", "released", "resolution_A", "method",
          "heavy_chains", "light_chains", "ab_other_chains", "antigen_chains",
          "antigen_name", "antigen_len", "title"]


def search_ids(rows):
    query = {
        "query": {"type": "group", "logical_operator": "and", "nodes": [
            {"type": "terminal", "service": "full_text",
             "parameters": {"value": "Fab antibody complex"}},
            {"type": "terminal", "service": "text",
             "parameters": {"attribute": "rcsb_entry_info.experimental_method",
                            "operator": "exact_match", "value": "X-ray"}},
            {"type": "terminal", "service": "text",
             "parameters": {"attribute": "rcsb_entry_info.resolution_combined",
                            "operator": "less_or_equal", "value": 2.5}},
            {"type": "terminal", "service": "text",
             "parameters": {"attribute": "rcsb_entry_info.polymer_entity_count_protein",
                            "operator": "greater_or_equal", "value": 3}},
        ]},
        "return_type": "entry",
        "request_options": {
            "paginate": {"start": 0, "rows": rows},
            # 오래된 entry 부터 = 시간이 지나도 목록이 잘 안 바뀌는 안정적인 스냅샷
            "sort": [{"sort_by": "rcsb_accession_info.initial_release_date",
                      "direction": "asc"}],
        },
    }
    r = requests.get(SEARCH_URL, params={"json": json.dumps(query)}, timeout=60)
    r.raise_for_status()
    data = r.json()
    return [x["identifier"] for x in data["result_set"]], data["total_count"]


def chain_role(desc):
    """entity 설명 문자열 → 사슬 역할(H/L/AB/AG). 항체 사슬은 이름에 단서가 있어요."""
    d = (desc or "").upper()
    if "HEAVY" in d:
        return "H"
    if "LIGHT" in d:
        return "L"
    if any(k in d for k in ("FAB", "FV ", "IMMUNOGLOBULIN", "ANTIBODY", "IGG", "SCFV", "NANOBODY")):
        return "AB"          # 항체이긴 한데 heavy/light 가 이름에 안 적힌 entity
    return "AG"              # 나머지 = 항원 후보


def fetch_entries(ids):
    r = requests.post(GRAPHQL_URL, json={"query": GQL, "variables": {"ids": ids}}, timeout=60)
    r.raise_for_status()
    return r.json()["data"]["entries"]


def to_rows(entries):
    rows = []
    for e in entries:
        heavy, light, ab_other, antigen = [], [], [], []
        ag_name, ag_len = "", ""
        for pe in e["polymer_entities"]:
            desc = pe["rcsb_polymer_entity"]["pdbx_description"]
            chains = pe["rcsb_polymer_entity_container_identifiers"]["auth_asym_ids"]
            length = (pe.get("entity_poly") or {}).get("rcsb_sample_sequence_length")
            role = chain_role(desc)
            if role == "H":
                heavy += chains
            elif role == "L":
                light += chains
            elif role == "AB":
                # 이름만으로는 heavy/light 를 못 가르는 항체 entity(예: "FAB NC10")
                # → 관례적으로 사슬 ID 가 H*/L* 인 경우만 추정하고, 나머지는 따로 표시
                for ch in chains:
                    (heavy if ch.startswith("H") else light if ch.startswith("L")
                     else ab_other).append(ch)
            else:
                antigen += chains
                if not ag_name:
                    ag_name, ag_len = desc, length
        res = (e["rcsb_entry_info"].get("resolution_combined") or [None])[0]
        rows.append({
            "pdb_id": e["rcsb_id"],
            "released": e["rcsb_accession_info"]["initial_release_date"][:10],
            "resolution_A": res,
            "method": e["rcsb_entry_info"]["experimental_method"],
            "heavy_chains": ";".join(heavy),
            "light_chains": ";".join(light),
            "ab_other_chains": ";".join(ab_other),
            "antigen_chains": ";".join(antigen),
            "antigen_name": ag_name,
            "antigen_len": ag_len,
            "title": e["struct"]["title"],
        })
    rows.sort(key=lambda r: (r["released"], r["pdb_id"]))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=12, help="가져올 entry 수")
    ap.add_argument("--out", default="rcsb_ab_complexes.csv")
    args = ap.parse_args()

    ids, total = search_ids(args.rows)
    print(f"[Search API] 조건에 맞는 entry {total}개 중 오래된 순 {len(ids)}개: {', '.join(ids)}",
          file=sys.stderr)
    rows = to_rows(fetch_entries(ids))

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print("Wrote:", out, f"({len(rows)} entries)", file=sys.stderr)


if __name__ == "__main__":
    main()
