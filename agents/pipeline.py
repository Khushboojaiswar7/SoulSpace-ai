# agents/pipeline.py
# Orchestrator that ties all AI agents together in the correct sequence.
#
# Pipeline flow:
#   1. Crisis Detection (bypass everything if crisis)
#   2. NLP Preprocessing
#   3. Entry Analysis Agent
#   4. Store Analysis
#   5. Memory Agent (pattern detection across entries)
#   6. Verification Agent (independent check)
#   7. Safety Gate (approval check)
#   8. Disclosure Agent (if approved)
#
# Usage:
#   from agents.pipeline import run_pipeline
#   result = run_pipeline(user_id=1, journal_text="I feel overwhelmed...")

import traceback

from agents.crisis_detector import detect_crisis, store_crisis_event
from agents.nlp_preprocessor import preprocess
from agents.entry_analysis import analyze_entry, store_entry_analysis
from agents.memory_agent import analyze_patterns, store_memory_patterns
from agents.verification_agent import verify_patterns, store_verification_result
from agents.safety_gate import evaluate, store_safety_log
from agents.disclosure_agent import generate_disclosure, store_disclosure


def run_pipeline(user_id: int, journal_text: str, journal_id: int = None) -> dict:
    """
    Runs the full agentic AI pipeline on a journal entry.

    This is the single entry point for the AI system. It orchestrates all
    agents in sequence, handles errors gracefully, and returns a unified
    result dict.

    Args:
        user_id (int): The ID of the current user.
        journal_text (str): The raw journal entry text.
        journal_id (int, optional): The journal entry's database ID
                                     (used for storing analysis results).

    Returns:
        dict: Unified result containing all pipeline outputs:
            {
                "crisis": {...} or None,
                "analysis": {...},
                "patterns": {...} or None,
                "verification": {...} or None,
                "safety": {...} or None,
                "disclosure": {...} or None,
                "pipeline_complete": bool,
                "errors": [str]
            }
    """
    result = {
        "crisis": None,
        "analysis": None,
        "patterns": None,
        "verification": None,
        "safety": None,
        "disclosure": None,
        "pipeline_complete": False,
        "errors": []
    }

    # ===================================================================
    # STEP 1: Crisis Detection — runs FIRST, bypasses everything if found
    # ===================================================================
    try:
        crisis_result = detect_crisis(journal_text)
        if crisis_result["is_crisis"]:
            result["crisis"] = crisis_result
            # Store crisis event in the database
            if journal_id and user_id:
                try:
                    store_crisis_event(
                        user_id=user_id,
                        journal_id=journal_id,
                        severity=crisis_result["severity"],
                        matched_patterns=crisis_result["matched_patterns"],
                        response_text=crisis_result["resources"]["message"]
                    )
                except Exception as e:
                    print(f"[pipeline] Failed to store crisis event: {e}")
            # BYPASS all reasoning agents — return crisis resources only
            result["pipeline_complete"] = True
            return result
    except Exception as e:
        print(f"[pipeline] Crisis detection error: {e}")
        traceback.print_exc()
        result["errors"].append(f"Crisis detection: {str(e)}")

    # ===================================================================
    # STEP 2: NLP Preprocessing
    # ===================================================================
    preprocessed = None
    try:
        preprocessed = preprocess(journal_text)
    except Exception as e:
        print(f"[pipeline] NLP preprocessing error: {e}")
        traceback.print_exc()
        result["errors"].append(f"NLP preprocessing: {str(e)}")

    # ===================================================================
    # STEP 3: Entry Analysis Agent
    # ===================================================================
    analysis = None
    try:
        analysis = analyze_entry(journal_text, preprocessed_data=preprocessed)
        result["analysis"] = analysis
    except Exception as e:
        print(f"[pipeline] Entry analysis error: {e}")
        traceback.print_exc()
        result["errors"].append(f"Entry analysis: {str(e)}")

    # ===================================================================
    # STEP 4: Store the analysis in the database
    # ===================================================================
    if analysis and journal_id and user_id:
        try:
            store_entry_analysis(journal_id, user_id, analysis)
        except Exception as e:
            print(f"[pipeline] Store analysis error: {e}")
            result["errors"].append(f"Store analysis: {str(e)}")

    # ===================================================================
    # STEP 5: Memory Agent — pattern detection across last 10 entries
    # ===================================================================
    memory_patterns = None
    try:
        memory_patterns = analyze_patterns(user_id, current_analysis=analysis)
        result["patterns"] = memory_patterns

        # Store patterns if valid
        if memory_patterns and not memory_patterns.get("insufficient_data"):
            try:
                store_memory_patterns(user_id, memory_patterns)
            except Exception as e:
                print(f"[pipeline] Store patterns error: {e}")
    except Exception as e:
        print(f"[pipeline] Memory agent error: {e}")
        traceback.print_exc()
        result["errors"].append(f"Memory agent: {str(e)}")

    # ===================================================================
    # STEP 6: Verification Agent — independent pattern check
    # ===================================================================
    verification = None
    try:
        verification = verify_patterns(user_id)
        result["verification"] = verification

        # Store verification result if valid
        if verification and not verification.get("insufficient_data"):
            try:
                store_verification_result(user_id, verification)
            except Exception as e:
                print(f"[pipeline] Store verification error: {e}")
    except Exception as e:
        print(f"[pipeline] Verification agent error: {e}")
        traceback.print_exc()
        result["errors"].append(f"Verification agent: {str(e)}")

    # ===================================================================
    # STEP 7: Safety Gate — only allow disclosure if evidence is strong
    # ===================================================================
    safety_result = None
    if memory_patterns and verification:
        try:
            safety_result = evaluate(memory_patterns, verification)
            result["safety"] = safety_result

            # Store safety decision
            try:
                store_safety_log(
                    user_id=user_id,
                    decision="approved" if safety_result.get("disclosure_allowed") else "rejected",
                    reason=safety_result.get("reason", ""),
                    memory_confidence=memory_patterns.get("confidence", 0.0),
                    verification_confidence=verification.get("confidence", 0.0),
                    agreement_score=safety_result.get("agreement_score", 0.0)
                )
            except Exception as e:
                print(f"[pipeline] Store safety log error: {e}")
        except Exception as e:
            print(f"[pipeline] Safety gate error: {e}")
            traceback.print_exc()
            result["errors"].append(f"Safety gate: {str(e)}")

    # ===================================================================
    # STEP 8: Disclosure Agent — generate supportive language (if approved)
    # ===================================================================
    if safety_result and safety_result.get("disclosure_allowed"):
        try:
            disclosure = generate_disclosure(
                approved_patterns=safety_result.get("approved_patterns", {}),
                user_id=user_id
            )
            result["disclosure"] = disclosure

            # Store disclosure
            if disclosure:
                try:
                    store_disclosure(
                        user_id=user_id,
                        disclosed_patterns=safety_result.get("approved_patterns", {}),
                        disclosure_text=disclosure.get("overall_reflection", "")
                    )
                except Exception as e:
                    print(f"[pipeline] Store disclosure error: {e}")
        except Exception as e:
            print(f"[pipeline] Disclosure agent error: {e}")
            traceback.print_exc()
            result["errors"].append(f"Disclosure agent: {str(e)}")

    result["pipeline_complete"] = True
    return result


def run_analysis_only(journal_text: str, preprocessed_data: dict = None) -> dict:
    """
    Runs ONLY the crisis detection + entry analysis steps.
    Useful for quick analysis without the full pattern pipeline.

    Args:
        journal_text (str): The raw journal entry text.
        preprocessed_data (dict, optional): Pre-computed NLP data.

    Returns:
        dict: { "crisis": {...} or None, "analysis": {...} }
    """
    # Crisis check
    crisis_result = detect_crisis(journal_text)
    if crisis_result["is_crisis"]:
        return {"crisis": crisis_result, "analysis": None}

    # NLP preprocessing if not provided
    if preprocessed_data is None:
        try:
            preprocessed_data = preprocess(journal_text)
        except Exception:
            preprocessed_data = None

    # Entry analysis
    analysis = analyze_entry(journal_text, preprocessed_data=preprocessed_data)
    return {"crisis": None, "analysis": analysis}


if __name__ == "__main__":
    # Quick test
    test_text = "I've been feeling really overwhelmed with work lately. The deadlines keep piling up and I can't sleep well. But I'm trying to exercise more which helps a bit."
    print("=" * 60)
    print("PIPELINE TEST (analysis only)")
    print("=" * 60)
    result = run_analysis_only(test_text)
    import json
    print(json.dumps(result, indent=2, default=str))
