"""
AI Drug-Drug Interaction Checker Module (CI-07)
Detects adverse interactions between multiple prescribed medications using clinical pharmacology rules
and risk severity classification.
"""
from typing import List, Dict, Any, Tuple
import itertools

# Known clinical drug-drug interactions database
INTERACTION_DATABASE = {
    frozenset(["warfarin", "aspirin"]): {
        "severity": "Severe / High Risk",
        "category": "Anticoagulant + Antiplatelet",
        "description": "Concurrent use significantly increases the risk of severe gastrointestinal and systemic bleeding.",
        "recommendation": "Avoid combination unless strictly monitored with regular INR checks. Consider alternative analgesic."
    },
    frozenset(["warfarin", "ibuprofen"]): {
        "severity": "Severe / High Risk",
        "category": "Anticoagulant + NSAID",
        "description": "NSAIDs cause gastrointestinal mucosal damage and inhibit platelet function, dramatically elevating hemorrhage risk.",
        "recommendation": "Contraindicated. Substitute NSAID with Acetaminophen (Paracetamol) if pain relief is required."
    },
    frozenset(["lisinopril", "potassium"]): {
        "severity": "Severe / High Risk",
        "category": "ACE Inhibitor + Potassium Supplement",
        "description": "ACE inhibitors reduce aldosterone secretion, causing potassium retention. Concurrent potassium can trigger dangerous Hyperkalemia and cardiac arrhythmias.",
        "recommendation": "Monitor serum potassium levels frequently. Discontinue unnecessary potassium supplements."
    },
    frozenset(["lisinopril", "ibuprofen"]): {
        "severity": "Moderate",
        "category": "ACE Inhibitor + NSAID",
        "description": "NSAIDs can blunt the antihypertensive effectiveness of ACE inhibitors and cause acute kidney impairment.",
        "recommendation": "Limit NSAID duration or monitor blood pressure and renal function closely."
    },
    frozenset(["metformin", "contrast dye"]): {
        "severity": "Severe / High Risk",
        "category": "Biguanide + Radiocontrast Agent",
        "description": "Iodinated contrast can induce acute renal failure, precipitating potentially fatal lactic acidosis in patients taking metformin.",
        "recommendation": "Withhold metformin 48 hours prior to and 48 hours after intravascular radiocontrast imaging."
    },
    frozenset(["atorvastatin", "clarithromycin"]): {
        "severity": "Severe / High Risk",
        "category": "Statin + CYP3A4 Inhibitor",
        "description": "Clarithromycin inhibits CYP3A4 metabolism of Atorvastatin, significantly elevating plasma statin levels and risking Rhabdomyolysis (muscle breakdown).",
        "recommendation": "Temporarily suspend statin therapy during the antibiotic course or choose an alternative antibiotic."
    },
    frozenset(["metformin", "glipizide"]): {
        "severity": "Moderate",
        "category": "Biguanide + Sulfonylurea",
        "description": "Synergistic glucose-lowering effect. Beneficial for diabetes control but increases the risk of symptomatic Hypoglycemia if meals are skipped.",
        "recommendation": "Educate patient on hypoglycemia symptoms (dizziness, shakiness) and carry fast-acting glucose."
    },
    frozenset(["aspirin", "ibuprofen"]): {
        "severity": "Moderate",
        "category": "Antiplatelet + NSAID",
        "description": "Ibuprofen interferes with the irreversible antiplatelet effect of low-dose cardio-protective aspirin and exacerbates GI ulceration.",
        "recommendation": "Take immediate-release aspirin at least 30 minutes before or 8 hours after ibuprofen."
    },
    frozenset(["sildenafil", "nitroglycerin"]): {
        "severity": "Severe / Contraindicated",
        "category": "PDE5 Inhibitor + Nitrate",
        "description": "Synergistic vasodilation causes profound, life-threatening hypotension and cardiovascular collapse.",
        "recommendation": "Strictly contraindicated. Must not be co-administered within 24-48 hours."
    },
    frozenset(["ciprofloxacin", "theophylline"]): {
        "severity": "Severe / High Risk",
        "category": "Fluoroquinolone + Xanthine",
        "description": "Ciprofloxacin inhibits theophylline clearance, increasing plasma concentrations and leading to theophylline toxicity (seizures, cardiac arrhythmias).",
        "recommendation": "Reduce theophylline dosage by 50% or choose an alternative antibacterial."
    }
}

def normalize_name(name: str) -> str:
    """Extracts base drug name from dosage string (e.g. 'Lisinopril 10mg' -> 'lisinopril')"""
    clean = name.lower().strip()
    # Strip common units and numbers
    parts = clean.split()
    if parts:
        return parts[0]
    return clean

def check_drug_interactions(medicines: List[str]) -> Dict[str, Any]:
    """
    Checks all pairs in the provided list of medicines for potential drug interactions.
    Returns detected interactions, highest risk level, and clinical recommendations.
    """
    normalized = [(m, normalize_name(m)) for m in medicines if m]
    found_interactions = []
    has_severe = False
    has_moderate = False

    # Check pairwise interactions
    for (orig1, norm1), (orig2, norm2) in itertools.combinations(normalized, 2):
        key = frozenset([norm1, norm2])
        if key in INTERACTION_DATABASE:
            data = INTERACTION_DATABASE[key]
            severity = data["severity"]
            if "Severe" in severity:
                has_severe = True
            elif "Moderate" in severity:
                has_moderate = True
            
            found_interactions.append({
                "drug_1": orig1,
                "drug_2": orig2,
                "severity": severity,
                "category": data["category"],
                "description": data["description"],
                "recommendation": data["recommendation"]
            })

    status = "Safe"
    if has_severe:
        status = "High Risk (Severe Interaction Detected)"
    elif has_moderate:
        status = "Moderate Caution (Interaction Detected)"

    return {
        "total_medicines_analyzed": len(medicines),
        "interactions_count": len(found_interactions),
        "status": status,
        "is_safe": len(found_interactions) == 0,
        "interactions": found_interactions
    }

if __name__ == "__main__":
    test_drugs = ["Warfarin 5mg", "Aspirin 81mg", "Lisinopril 10mg"]
    result = check_drug_interactions(test_drugs)
    print("Test Drug Interaction Result:")
    print(f"Status: {result['status']}")
    print(f"Conflicts found: {result['interactions_count']}")
    for inter in result['interactions']:
        print(f"- {inter['drug_1']} + {inter['drug_2']}: {inter['severity']} -> {inter['description']}")
