import json
from typing import Any, Dict, List, Optional

def _extract_loinc_code(fhir_obs: Dict[str, Any]) -> Optional[str]:
    codings = fhir_obs.get("code", {}).get("coding", [])
    for c in codings:
        if c.get("system") == "http://loinc.org":
            return c.get("code")
    return None

def process_fhir_observation(fhir_obs: Dict[str, Any], kb: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    loinc_code = _extract_loinc_code(fhir_obs)
    if not loinc_code or loinc_code not in kb:
        return None
    value = fhir_obs.get("valueQuantity", {}).get("value")
    unit = fhir_obs.get("valueQuantity", {}).get("unit")
    if value is None or unit is None:
        return None
    entry = kb[loinc_code]
    expected_unit = entry.get("unit")
    if expected_unit and expected_unit != unit:
        return {
            "observation_code": loinc_code,
            "value": value,
            "unit": unit,
            "status": "rejected",
            "reason": f"Unit mismatch (expected {expected_unit}, got {unit})."
        }
    for category, thr in entry.get("thresholds", {}).items():
        min_v = thr.get("min", float("-inf"))
        max_v = thr.get("max", float("inf"))
        if min_v <= value <= max_v and category in entry.get("interpretations", {}):
            interp = entry["interpretations"][category]
            return {
                "observation_code": loinc_code, "value": value, "unit": unit, "category": category,
                "interpretation": interp.get("label"), "interpretation_snomed": interp.get("snomed"),
                "explanation": interp.get("explanation"), "recommended_action": interp.get("action"),
                "evidence_source": interp.get("evidence"), "evidence_grade": interp.get("evidence_grade"),
                "status": "ok"
            }
    return {"observation_code": loinc_code, "status": "no_match"}

def find_convergence(explanations: List[Dict[str, Any]], marker_set: List[str], min_support: int = 2) -> Optional[Dict[str, Any]]:
    relevant = [
        e for e in explanations
        if e and e.get("status") == "ok"
        and e.get("observation_code") in marker_set
        and e.get("category") != "normal"
    ]
    if len(relevant) >= min_support:
        return {
            "support_count": len(relevant),
            "supporting_observations": [e["observation_code"] for e in relevant],
            "combined_interpretation": "Meerdere onafhankelijke markers wijzen op een gedeeld cardiovasculair/metabool risicoprofiel.",
            "confidence_note": "Convergentie verhoogt de aannemelijkheid van dit patroon, maar is geen klinische diagnose."
        }
    return None

with open("cvd_knowledge.json", "r") as f:
    kb = json.load(f)

with open("cvd_observations_unit_mismatch.json", "r") as f:
    observations = json.load(f)

results = [process_fhir_observation(obs, kb) for obs in observations]
cvd_marker_set = ["4548-4", "13457-7", "8480-6"]
convergence = find_convergence(results, cvd_marker_set)

final_output = {"explanations": results, "convergence": convergence}
print(json.dumps(final_output, indent=2))
