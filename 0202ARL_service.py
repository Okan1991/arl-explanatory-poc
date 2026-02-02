"""ARL proof-of-concept service (minimal).

Scope
- Deterministic evaluation of a small, versioned knowledge pack keyed by LOINC.
- Produces citizen-facing explanation bundles + an optional convergence summary.
- NOT a diagnostic engine and NOT medical advice.

Run
  python arl_service.py --obs sample_observations.json --kb arl_knowledge.json
"""

from __future__ import annotations

import argparse
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
        # PoC: reject unit mismatch rather than guessing conversions
        return {
            "observation_code": loinc_code,
            "value": value,
            "unit": unit,
            "status": "rejected",
            "reason": f"Unit mismatch (expected {expected_unit}, got {unit}).",
            "pack_version": entry.get("pack_version"),
        }

    for category, thr in entry.get("thresholds", {}).items():
        min_v = thr.get("min", float("-inf"))
        max_v = thr.get("max", float("inf"))
        if min_v <= value <= max_v and category in entry.get("interpretations", {}):
            interp = entry["interpretations"][category]
            return {
                "observation_code": loinc_code,
                "value": value,
                "unit": unit,
                "category": category,
                "interpretation": interp.get("label"),
                "interpretation_snomed": interp.get("snomed"),
                "explanation": interp.get("explanation"),
                "recommended_action": interp.get("action"),
                "evidence_source": interp.get("evidence"),
                "evidence_grade": interp.get("evidence_grade"),
                "pack_version": entry.get("pack_version"),
                "status": "ok",
            }

    return {
        "observation_code": loinc_code,
        "value": value,
        "unit": unit,
        "status": "no_match",
        "reason": "No interpretation category matched thresholds.",
        "pack_version": entry.get("pack_version"),
    }


def find_convergence(
    explanations: List[Dict[str, Any]],
    marker_set: List[str],
    min_support: int = 2,
) -> Optional[Dict[str, Any]]:
    relevant = [
        e for e in explanations
        if e and e.get("status") == "ok" and e.get("observation_code") in marker_set
        and e.get("category") not in ("normal",)
    ]
    if len(relevant) >= min_support:
        return {
            "support_count": len(relevant),
            "supporting_observations": [e["observation_code"] for e in relevant],
            "combined_interpretation": "Multiple markers suggest a shared metabolic pattern (prioritization heuristic).",
            "confidence_note": "Convergence increases plausibility but is not diagnostic.",
        }
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--obs", required=True, help="Path to a JSON list of FHIR Observation resources.")
    parser.add_argument("--kb", required=True, help="Path to ARL knowledge pack JSON.")
    args = parser.parse_args()

    with open(args.kb, "r", encoding="utf-8") as f:
        kb = json.load(f)

    with open(args.obs, "r", encoding="utf-8") as f:
        observations = json.load(f)

    explanations = []
    for obs in observations:
        explanations.append(process_fhir_observation(obs, kb))

    metabolic_marker_set = ["4548-4", "1558-6", "1988-5"]
    convergence = find_convergence(explanations, metabolic_marker_set, min_support=2)

    output = {
        "explanations": explanations,
        "convergence": convergence,
        "disclaimer": "This PoC provides explanatory summaries based on curated rules. It is not diagnostic or medical advice.",
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
