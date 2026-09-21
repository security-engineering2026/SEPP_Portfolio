from __future__ import annotations
import hashlib, re
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
        candidates = [*self.root.glob("Software_Forge/SOFTWARE_FORGE_MASTER_MANIFEST_v*.yaml"), *self.root.glob("SOFTWARE_FORGE_MASTER_MANIFEST_v*.yaml")]
        def version_key(p):
            m = re.search(r"_v(\d+)\.(\d+)\.yaml$", p.name)
            return (int(m.group(1)), int(m.group(2))) if m else (-1, -1)
        candidates.sort(key=version_key, reverse=True)
        if candidates:
            return candidates[0]
        p=self.root/"FORGE_MANIFEST.yaml"
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
        if data.get("forge_manifest_version") not in {"1.2","1.3"}:
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
            "approval_before_contract_change","implementation_without_approval","discovery","analysis","offline",
        }
        if not isinstance(product_intelligence,dict) or not required_product_intelligence.issubset(product_intelligence):
            errors.append("product_intelligence_contract_incomplete")
        discovery=product_intelligence.get("discovery") if isinstance(product_intelligence,dict) else None
        required_discovery={"search_engine","search_planner","query_generation","query_expansion","multi_source_search","semantic_search","category_search","capability_search","workflow_search","ux_search","source_registry","candidate_pooling","large_candidate_pool","deduplication","relevance_filtering","adaptive_search_depth","saturation_detection","minimum_candidate_policy","deep_analysis_threshold","no_fixed_top_n_cap","search_cache","local_search_index","research_scheduler"}
        if not isinstance(discovery,dict) or not required_discovery.issubset(discovery): errors.append("product_intelligence_discovery_contract_incomplete")
        analysis=product_intelligence.get("analysis") if isinstance(product_intelligence,dict) else None
        required_analysis={"batch_analysis","comparative_analysis","capability_matrix","workflow_matrix","ux_pattern_matrix","evidence_scoring","provenance","pattern_synthesis","result_confidence","discovery_to_analysis_traceability"}
        if not isinstance(analysis,dict) or not required_analysis.issubset(analysis): errors.append("product_intelligence_analysis_contract_incomplete")
        pi_offline=product_intelligence.get("offline") if isinstance(product_intelligence,dict) else None
        required_pi_offline={"local_index","local_knowledge_store","knowledge_pack_import","knowledge_pack_export","local_search","local_comparison","local_pattern_analysis","local_gap_analysis","incremental_online_sync","evidence_refresh_on_reconnect","external_discovery_when_offline"}
        if not isinstance(pi_offline,dict) or not required_pi_offline.issubset(pi_offline): errors.append("product_intelligence_offline_contract_incomplete")
        offline=data.get("offline")
        required_offline={"local_build","local_test","local_static_analysis","local_runtime","local_evidence","local_git","local_recovery","local_failure_diagnosis","local_repair","local_regression","local_independent_verification","local_product_intelligence","local_search_index","knowledge_pack_import","knowledge_pack_export","dependency_cache","toolchain_cache","documentation_cache","package_registry_cache","platform_image_cache","offline_external_discovery"}
        if not isinstance(offline,dict) or not required_offline.issubset(offline): errors.append("offline_capability_contract_incomplete")
        evolution=data.get("manifest_evolution") if isinstance(data,dict) else None
        if data.get("forge_manifest_version") == "1.3":
            required_evolution={"proposal_engine","structured_diff","explicit_user_instruction","approval_ledger","versioned_change","requirement_delta","impact_analysis","affected_test_detection","validation_after_change","independent_verification_after_change","silent_change_forbidden","requirement_weakening_requires_explicit_approval","removal_requires_explicit_approval","stale_manifest_rejection","immutable_proposal_hash","rollback_or_rejection"}
            if not isinstance(evolution,dict) or not required_evolution.issubset(evolution): errors.append("manifest_evolution_contract_incomplete")
        pre=data.get("online_preprovisioning")
        required_pre={"readiness_scan","dependency_inventory","toolchain_inventory","required_runtime_inventory","required_sdk_inventory","package_cache_warmup","browser_runtime_warmup","platform_image_warmup","documentation_cache_warmup","knowledge_pack_warmup","offline_readiness_score","missing_capability_report","scheduled_refresh","integrity_verification","resumable_downloads","content_addressed_storage","version_pinning","license_policy_check","storage_budget"}
        if not isinstance(pre,dict) or not required_pre.issubset(pre): errors.append("online_preprovisioning_contract_incomplete")
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
