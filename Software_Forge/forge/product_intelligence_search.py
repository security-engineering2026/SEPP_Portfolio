from __future__ import annotations
import hashlib
import json
import math
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Protocol

TOKEN_RE=re.compile(r"[A-Za-z0-9][A-Za-z0-9_+.#-]{1,}")

def _tokens(text: str) -> set[str]:
    return {x.lower() for x in TOKEN_RE.findall(text or "")}

@dataclass(frozen=True)
class Candidate:
    url: str
    name: str
    description: str = ""
    capabilities: tuple[str,...] = ()
    workflows: tuple[str,...] = ()
    source: str = ""
    evidence: tuple[str,...] = ()

    @property
    def candidate_id(self):
        return hashlib.sha256(self.url.strip().lower().encode()).hexdigest()[:16]

class SearchSource(Protocol):
    name: str
    def search(self, query: str) -> Iterable[Candidate]: ...

class LocalCatalogSource:
    name="local_catalog"
    def __init__(self, records: Iterable[dict]):
        self.records=list(records)

    def search(self, query: str):
        q=_tokens(query)
        for r in self.records:
            text=" ".join([r.get("name",""),r.get("description","")," ".join(r.get("capabilities",[])), " ".join(r.get("workflows",[]))])
            if not q or q & _tokens(text):
                yield Candidate(
                    url=r["url"], name=r.get("name",r["url"]), description=r.get("description",""),
                    capabilities=tuple(r.get("capabilities",[])), workflows=tuple(r.get("workflows",[])),
                    source=r.get("source","local_catalog"), evidence=tuple(r.get("evidence",[])))

class ProductSearchEngine:
    """Large-pool discovery core. Search and deep analysis are separate stages."""
    def __init__(self, sources: Iterable[SearchSource]):
        self.sources=list(sources)

    def discover(self, queries: Iterable[str], minimum_candidates: int=100, max_candidates: int | None=None):
        queries=[q.strip() for q in queries if q and q.strip()]
        pool={}
        query_hits={}
        for query in queries:
            hits=0
            for source in self.sources:
                for candidate in source.search(query):
                    pool[candidate.candidate_id]=candidate
                    hits+=1
            query_hits[query]=hits
            if max_candidates is not None and len(pool)>=max_candidates:
                break
        ranked=self._rank(pool.values(),queries)
        if max_candidates is not None:
            ranked=ranked[:max_candidates]
        return {
            "state":"OBSERVED",
            "queries":queries,
            "sources":[getattr(s,"name",s.__class__.__name__) for s in self.sources],
            "discovered_count":sum(query_hits.values()),
            "unique_count":len(ranked),
            "minimum_candidates":minimum_candidates,
            "minimum_met":len(ranked)>=minimum_candidates,
            "saturation":self._saturation(query_hits, len(ranked)),
            "candidates":[asdict(c) | {"candidate_id":c.candidate_id} for c in ranked],
        }

    def _rank(self,candidates,queries):
        q=_tokens(" ".join(queries))
        scored=[]
        for c in candidates:
            text=_tokens(" ".join([c.name,c.description,*c.capabilities,*c.workflows]))
            overlap=len(q & text)
            evidence=min(len(c.evidence),5)
            score=(overlap*3)+(evidence*0.5)+math.log1p(len(c.capabilities)+len(c.workflows))
            scored.append((score,c))
        scored.sort(key=lambda x:(-x[0],x[1].name.lower(),x[1].url.lower()))
        return [c for _,c in scored]

    @staticmethod
    def _saturation(query_hits, unique_count):
        if not query_hits: return {"state":"UNKNOWN","new_unique_per_query":0.0}
        return {"state":"OBSERVED","new_unique_per_query":round(unique_count/max(len(query_hits),1),2)}

    def persist(self, result, path: Path):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
        return {"state":"TESTED","path":str(path),"count":len(result.get("candidates",[]))}
