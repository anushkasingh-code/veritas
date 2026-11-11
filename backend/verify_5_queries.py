import asyncio
import time
from typing import Dict, Any, List

queries = [
    "AI replacing software engineers",
    "CRISPR safety and human gene editing",
    "Semiconductor supply chain bottlenecks",
    "Bitcoin regulation and central bank digital currencies",
    "Quantum computing commercial viability",
]

required_sections = [
    "# Research & Fact Verification Report",
    "## Research Query",
    "## Overall Assessment",
    "## Executive Summary",
    "## Claim Verification Matrix",
    "## Contradiction Analysis",
    "## Evidence Analysis",
    "## Final Conclusion",
    "## References",
]

forbidden_phrases = [
    "this report analyzes",
    "the research indicates",
    "as an ai model",
]

async def evaluate_quality(query: str, report_md: str) -> Dict[str, Any]:
    score = 0

    # 1. Schema Compliance (20 pts)
    missing = [sec for sec in required_sections if sec not in report_md]
    schema_pts = 20 if not missing else max(0, 20 - len(missing) * 4)
    score += schema_pts

    # 2. No Filler Phrases (20 pts)
    lower_report = report_md.lower()
    filler_found = [p for p in forbidden_phrases if p in lower_report]
    filler_pts = 20 if not filler_found else 0
    score += filler_pts

    # 3. Executive Summary Quality & Word Count (20 pts)
    exec_summary = ""
    if "## Executive Summary" in report_md and "## Claim Verification Matrix" in report_md:
        exec_summary = report_md.split("## Executive Summary")[1].split("## Claim Verification Matrix")[0].strip()

    word_count_exec = len(exec_summary.split())
    exec_pts = 20 if (exec_summary and word_count_exec <= 280) else 10
    score += exec_pts

    # 4. Reference Reliability Sorting (20 pts)
    ref_pts = 20
    if "## References" in report_md:
        refs_section = report_md.split("## References")[1].strip()
        ref_lines = [line for line in refs_section.split("\n") if "Reliability Rating:" in line]
        ratings = []
        for line in ref_lines:
            if "High" in line:
                ratings.append(3)
            elif "Medium" in line:
                ratings.append(2)
            else:
                ratings.append(1)
        if ratings and ratings != sorted(ratings, reverse=True):
            ref_pts = 10
    score += ref_pts

    # 5. Length Control (20 pts)
    total_words = len(report_md.split())
    length_pts = 20 if total_words <= 1500 else 10
    score += length_pts

    return {
        "score": score,
        "total_words": total_words,
        "exec_words": word_count_exec,
        "missing_sections": missing,
        "filler_phrases": filler_found,
        "schema_pts": schema_pts,
        "filler_pts": filler_pts,
        "exec_pts": exec_pts,
        "ref_pts": ref_pts,
        "length_pts": length_pts,
    }


async def run_quality_validation():
    from app.agents.report_generator import generate_report
    from app.graph.state import Claim, Source, Contradiction

    print("=== EXECUTING QUALITY & SCHEMA VALIDATION FOR 5 DIVERSE QUERIES ===")

    results = []

    for idx, q in enumerate(queries, start=1):
        print(f"\n[{idx}/5] Testing Query: '{q}'...")
        start_time = time.time()

        sample_claims = [
            Claim(id=f"claim_{idx}_01", text=f"Primary technological and economic factor in {q}", category="Fact", verdict="SUPPORTED", confidence=0.91, reasoning=f"Corroborated by academic and industry data on {q}.", supporting_sources=["src_01"]),
            Claim(id=f"claim_{idx}_02", text=f"Regulatory and policy implications of {q}", category="Policy", verdict="MIXED", confidence=0.68, reasoning=f"Discrepancies across jurisdictional frameworks regarding {q}.", supporting_sources=["src_02"], contradicting_sources=["src_03"]),
        ]

        sample_sources = [
            Source(id="src_01", title=f"Peer Reviewed Journal on {q}", url=f"https://nature.com/articles/{idx}001", snippet="Academic research.", domain="nature.com", score=0.94),
            Source(id="src_02", title=f"Government Policy Brief: {q}", url=f"https://nih.gov/policy/{idx}", snippet="Government analysis.", domain="nih.gov", score=0.88),
            Source(id="src_03", title=f"Market Intelligence Report: {q}", url=f"https://reuters.com/tech/{idx}", snippet="Industry coverage.", domain="reuters.com", score=0.76),
        ]

        sample_contradictions = [
            Contradiction(claim_id=f"claim_{idx}_02", source_a_id="src_02", source_b_id="src_03", conflict_description=f"Jurisdictional variance in regulatory timelines for {q}.")
        ] if idx % 2 == 0 else []

        report_md = await generate_report(
            user_query=q,
            claims=sample_claims,
            sources=sample_sources,
            contradictions=sample_contradictions,
        )

        elapsed = round(time.time() - start_time, 2)
        eval_metrics = await evaluate_quality(q, report_md)

        print(f"  Latency: {elapsed}s | Length: {eval_metrics['total_words']} words")
        print(f"  Quality Score: {eval_metrics['score']}/100")

        results.append({
            "query": q,
            "latency": elapsed,
            "eval": eval_metrics,
            "preview": report_md[:300],
        })

    print("\n====================================================")
    print("QUALITY VALIDATION FINAL REPORT")
    print("====================================================")

    avg_score = sum(r["eval"]["score"] for r in results) / len(results)
    print(f"Total Queries Evaluated: {len(results)}")
    print(f"Average Quality Score: {avg_score:.1f}/100")

    for idx, r in enumerate(results, start=1):
        print(f"\nQuery {idx}: '{r['query']}'")
        print(f"  - Quality Score: {r['eval']['score']}/100")
        print(f"  - Word Count: {r['eval']['total_words']} words (Exec Summary: {r['eval']['exec_words']} words)")
        print(f"  - Latency: {r['latency']}s")

    return results

if __name__ == "__main__":
    asyncio.run(run_quality_validation())
