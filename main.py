#!/usr/bin/env python3
"""
Interview Knowledge Base - Main Pipeline

Orchestrates the full flow: ingestion -> indexing -> generation
"""
import argparse
import logging
import sys
import json
from pathlib import Path
from typing import Optional
import ingestion
import indexing
import generation
from config import BRIEF_MODES, GENERATION_MODEL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_pipeline(
    company: str,
    person: Optional[str] = None,
    mode: str = "summary",
    skip_ingestion: bool = False,
    skip_indexing: bool = False,
    model: str = GENERATION_MODEL,
) -> dict:
    """
    Run the complete interview KB pipeline.

    Args:
        company: Company name
        person: Person name (optional)
        mode: Brief generation mode
        skip_ingestion: Skip ingestion if data exists
        skip_indexing: Skip indexing if index exists
        model: LLM model to use

    Returns:
        Dict with pipeline results
    """
    logger.info(f"Starting pipeline for {company}" + (f" / {person}" if person else ""))

    results = {
        "company": company,
        "person": person,
        "mode": mode,
        "steps": {}
    }

    # Step 1: Ingestion
    if not skip_ingestion:
        logger.info("="*60)
        logger.info("STEP 1: INGESTION")
        logger.info("="*60)
        try:
            output_file = ingestion.run_ingestion(company, person or company)
            results["steps"]["ingestion"] = {
                "status": "success",
                "output_file": str(output_file),
            }
            logger.info(f"✓ Ingestion complete: {output_file}")
        except Exception as e:
            logger.error(f"✗ Ingestion failed: {e}")
            results["steps"]["ingestion"] = {"status": "failed", "error": str(e)}
            return results
    else:
        logger.info("Skipping ingestion (using existing data)")
        results["steps"]["ingestion"] = {"status": "skipped"}

    # Step 2: Indexing
    if not skip_indexing:
        logger.info("\n" + "="*60)
        logger.info("STEP 2: INDEXING")
        logger.info("="*60)
        try:
            # Convert company to folder name
            company_folder = company.replace(" ", "_").lower()
            index_dir = indexing.build_index(company_folder)
            results["steps"]["indexing"] = {
                "status": "success",
                "index_dir": str(index_dir),
            }
            logger.info(f"✓ Indexing complete: {index_dir}")
        except Exception as e:
            logger.error(f"✗ Indexing failed: {e}")
            results["steps"]["indexing"] = {"status": "failed", "error": str(e)}
            return results
    else:
        logger.info("Skipping indexing (using existing index)")
        results["steps"]["indexing"] = {"status": "skipped"}

    # Step 3: Generation
    logger.info("\n" + "="*60)
    logger.info("STEP 3: GENERATION")
    logger.info("="*60)
    try:
        company_folder = company.replace(" ", "_").lower()
        brief = generation.generate_brief(
            company=company_folder,
            person=person,
            mode=mode,
            model=model,
        )
        results["steps"]["generation"] = {
            "status": "success",
            "brief": brief,
        }
        logger.info(f"✓ Generation complete: {len(brief['summary'])} chars, "
                   f"{len(brief['insights'])} insights, {len(brief['citations'])} citations")
    except Exception as e:
        logger.error(f"✗ Generation failed: {e}")
        results["steps"]["generation"] = {"status": "failed", "error": str(e)}
        return results

    return results


def print_results(results: dict):
    """Pretty print pipeline results."""
    print("\n" + "="*80)
    print("INTERVIEW KNOWLEDGE BASE - PIPELINE RESULTS")
    print("="*80)

    print(f"\n📊 Company: {results['company']}")
    if results['person']:
        print(f"👤 Person: {results['person']}")
    print(f"📝 Mode: {results['mode']}")

    print("\n" + "-"*80)
    print("PIPELINE STEPS")
    print("-"*80)

    for step_name, step_data in results['steps'].items():
        status_icon = "✓" if step_data['status'] == 'success' else "✗" if step_data['status'] == 'failed' else "⊘"
        print(f"\n{status_icon} {step_name.upper()}: {step_data['status']}")
        if 'error' in step_data:
            print(f"  Error: {step_data['error']}")

    # Print brief if generation succeeded
    if results['steps'].get('generation', {}).get('status') == 'success':
        brief = results['steps']['generation']['brief']

        print("\n" + "="*80)
        print("GENERATED BRIEF")
        print("="*80)
        print(brief['summary'])

        print("\n" + "-"*80)
        print("KEY ENTITIES")
        print("-"*80)
        for entity in brief['key_entities'][:5]:
            print(f"  • {entity['type']}: {entity['text']} ({entity['mentions']} mentions)")

        print("\n" + "-"*80)
        print("METADATA")
        print("-"*80)
        meta = brief['metadata']
        print(f"  Model: {meta['model']}")
        print(f"  Chunks retrieved: {meta['n_chunks_retrieved']}")
        print(f"  Citations: {meta['n_citations']}")
        print(f"  Retrieval time: {meta['retrieval_time_ms']}ms")
        print(f"  Generation time: {meta['generation_time_ms']}ms")
        print(f"  Total time: {meta['total_time_ms']}ms")

    print("\n" + "="*80)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Interview Knowledge Base - RAG-based interview preparation system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline
  python main.py --company "TechCorp" --person "Jane Smith"

  # Generate brief using existing data
  python main.py --company "TechCorp" --skip-ingestion --skip-indexing

  # Use different mode and model
  python main.py --company "TechCorp" --mode technical --model claude-3-5-sonnet-20241022

  # Save output to JSON
  python main.py --company "TechCorp" --output brief.json
        """
    )

    parser.add_argument(
        "--company",
        required=True,
        help="Company name"
    )
    parser.add_argument(
        "--person",
        help="Person name (optional)"
    )
    parser.add_argument(
        "--mode",
        choices=BRIEF_MODES,
        default="summary",
        help="Brief generation mode (default: summary)"
    )
    parser.add_argument(
        "--model",
        default=GENERATION_MODEL,
        help=f"LLM model to use (default: {GENERATION_MODEL})"
    )
    parser.add_argument(
        "--skip-ingestion",
        action="store_true",
        help="Skip ingestion step (use existing data)"
    )
    parser.add_argument(
        "--skip-indexing",
        action="store_true",
        help="Skip indexing step (use existing index)"
    )
    parser.add_argument(
        "--output",
        help="Save results to JSON file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Run pipeline
        results = run_pipeline(
            company=args.company,
            person=args.person,
            mode=args.mode,
            skip_ingestion=args.skip_ingestion,
            skip_indexing=args.skip_indexing,
            model=args.model,
        )

        # Print results
        print_results(results)

        # Save to file if requested
        if args.output:
            # Make results JSON serializable
            output_data = {
                "company": results["company"],
                "person": results["person"],
                "mode": results["mode"],
                "steps": {
                    k: {kk: vv for kk, vv in v.items() if kk != 'brief'}
                    for k, v in results["steps"].items()
                }
            }

            # Add brief separately (it's already serializable)
            if "generation" in results["steps"] and "brief" in results["steps"]["generation"]:
                output_data["brief"] = results["steps"]["generation"]["brief"]

            with open(args.output, "w") as f:
                json.dump(output_data, f, indent=2)
            logger.info(f"Results saved to {args.output}")

        # Exit with appropriate code
        if any(step.get("status") == "failed" for step in results["steps"].values()):
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\nPipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
