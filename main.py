#!/usr/bin/env python3
"""
Interview Knowledge Base - URL Discovery Tool

Discovers all relevant URLs for a company/person for NotebookLM import.
"""
import argparse
import logging
import sys
import json
from pathlib import Path
from typing import Optional
from ingestion.url_discovery import discover_urls

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def discover_urls_cli(
    company: str,
    person: Optional[str] = None,
    max_urls: int = 50,
    output_file: Optional[str] = None,
) -> dict:
    """
    Discover URLs for a company/person.

    Args:
        company: Company name
        person: Person name (optional)
        max_urls: Maximum URLs to discover
        output_file: Save results to file (optional)

    Returns:
        Dict with discovered URLs
    """
    logger.info(f"Starting URL discovery for {company}" + (f" / {person}" if person else ""))

    try:
        # Discover URLs
        urls = discover_urls(company, person, max_urls)

        results = {
            "company": company,
            "person": person,
            "total_urls": len(urls),
            "urls": urls
        }

        # Group by category
        by_category = {}
        for url_data in urls:
            category = url_data["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(url_data)

        results["by_category"] = by_category

        # Save to file if requested
        if output_file:
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {output_file}")

        return results

    except Exception as e:
        logger.error(f"URL discovery failed: {e}", exc_info=True)
        return {"error": str(e)}


def print_results(results: dict):
    """Pretty print URL discovery results."""
    if "error" in results:
        print(f"\n❌ Error: {results['error']}")
        return

    print("\n" + "="*80)
    print("INTERVIEW KNOWLEDGE BASE - URL DISCOVERY")
    print("="*80)

    print(f"\n📊 Company: {results['company']}")
    if results['person']:
        print(f"👤 Person: {results['person']}")
    print(f"🔗 Total URLs: {results['total_urls']}")

    print("\n" + "-"*80)
    print("URLS BY CATEGORY")
    print("-"*80)

    for category, urls in results.get("by_category", {}).items():
        print(f"\n🏷️  {category.upper()} ({len(urls)} URLs)")
        for url_data in urls[:5]:  # Show first 5
            print(f"  • {url_data['title'][:70]}")
            print(f"    {url_data['url']}")
        if len(urls) > 5:
            print(f"  ... and {len(urls) - 5} more")

    print("\n" + "-"*80)
    print("ALL URLS (for NotebookLM)")
    print("-"*80)
    for url_data in results["urls"]:
        print(url_data["url"])

    print("\n" + "="*80)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Interview Knowledge Base - URL Discovery for NotebookLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover URLs for a company
  python main.py --company "OpenAI"

  # Discover URLs for a person at a company
  python main.py --company "OpenAI" --person "Sam Altman"

  # Get more URLs
  python main.py --company "OpenAI" --max-urls 100

  # Save to file
  python main.py --company "OpenAI" --output urls.json
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
        "--max-urls",
        type=int,
        default=50,
        help="Maximum URLs to discover (default: 50)"
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
        # Discover URLs
        results = discover_urls_cli(
            company=args.company,
            person=args.person,
            max_urls=args.max_urls,
            output_file=args.output,
        )

        # Print results
        print_results(results)

        # Exit with appropriate code
        if "error" in results:
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\nURL discovery interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
