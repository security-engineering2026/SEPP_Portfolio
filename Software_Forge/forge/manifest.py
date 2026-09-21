from __future__ import annotations
import hashlib
from pathlib import Path
import yaml

class ManifestError(ValueError):
    pass

REQUIRED_TOP_LEVEL = {"forge_manifest_version","product","intent","modes","core_principles","validation","release","truth_states"}

class ManifestEngine:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.path = self._find_manifest()

    def _find_manifest(self):
        for p in [
            self.root/"Software_Forge/SOFTWARE_FORGE_MASTER_MANIFEST_v1.1.yaml",
            self.root/"SOFTWARE_FORGE_MASTER_MANIFEST_v1.1.yaml",
            self.root/"FORGE_MANIFEST.yaml",
        ]:
            if p.exists():
                return p
        raise ManifestError("Manifest not found")

    def load(self):
        data=yaml.safe_load(self.path.read_text(encoding="utf-8"))
        if not isinstance(data,dict):
            raise ManifestError("Manifest root must be a mapping")
        return data

    def validate(self):
        data=self.load()
        missing=sorted(REQUIRED_TOP_LEVEL-set(data))
        errors=[]
        if missing:
            errors.append("missing_top_level:"+",".join(missing))
        if data.get("forge_manifest_version")!="1.1":
            errors.append("unsupported_manifest_version")
        product=data.get("product")
        if not isinstance(product,dict) or not product.get("id") or not product.get("name"):
            errors.append("invalid_product_identity")
        if not isinstance(data.get("modes"),list) or not data["modes"]:
            errors.append("modes_required")
        required_validation={"unit","integration","runtime","ui","security","red_team","blue_team","regression","independent_verification","product_intelligence"}
        validation=data.get("validation")
        if not isinstance(validation,dict) or not required_validation.issubset(validation):
            errors.append("validation_matrix_incomplete")
        product_intelligence=data.get("product_intelligence")
        required_product_intelligence={
            "enabled","external_product_discovery","similar_product_analysis",
            "capability_extraction","workflow_pattern_analysis","ux_pattern_analysis",
            "evidence_backed_comparison","provenance_tracking","gap_analysis",
            "improvement_candidate_generation","requirement_traceability","impact_analysis",
            "approval_before_contract_change","implementation_without_approval","outputs","lifecycle",
        }
        if not isinstance(product_intelligence,dict) or not required_product_intelligence.issubset(product_intelligence):
            errors.append("product_intelligence_contract_incomplete")
        if not isinstance(data.get("release"),dict):
            errors.append("release_policy_required")
        if data.get("truth_states")!=["unknown","claimed","observed","tested","verified","passed","released"]:
            errors.append("truth_state_order_invalid")
        return {
            "state":"VERIFIED" if not errors else "FAILED",
            "path":str(self.path),
            "sha256":hashlib.sha256(self.path.read_bytes()).hexdigest(),
            "errors":errors,
            "product_id":product.get("id") if isinstance(product,dict) else None,
            "requirement_count":self.extract_requirements(data)["count"],
        }

    def extract_requirements(self,data=None):
        data=self.load() if data is None else data
        req=[]
        def walk(v,path=""):
            if isinstance(v,dict):
                for k,c in v.items():
                    p=f"{path}.{k}" if path else k
                    if c=="required" or c is True:
                        req.append({"id":"REQ-"+hashlib.sha1(p.encode()).hexdigest()[:10].upper(),"path":p,"value":c})
                    walk(c,p)
            elif isinstance(v,list):
                for i,c in enumerate(v):
                    walk(c,f"{path}[{i}]")
        walk(data)
        unique={r["id"]:r for r in req}
        return {"count":len(unique),"requirements":list(unique.values())}

    def snapshot(self):
        data=self.load()
        return {"manifest":self.validate(),"requirements":self.extract_requirements(data)}
