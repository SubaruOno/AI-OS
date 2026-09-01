"""
Academic Paper Search Client — OpenAlex-powered research engine.

Primary: OpenAlex API (250M+ papers, excellent search quality, zero auth)
Supplement: Unpaywall (find free PDFs of paywalled papers via DOI)
Content: Firecrawl (scrape full article text from publisher pages)

Usage:
    from scripts.academic.client import AcademicClient

    client = AcademicClient()

    # Search for papers
    papers = client.search("autonomous AI coding agents", limit=10, year_from=2024)

    # Get a specific paper by DOI
    paper = client.get_paper(doi="10.1145/3650212.3680384")

    # Find free PDF for a paywalled paper
    pdf_url = client.find_free_pdf("10.1145/3650212.3680384")

    # Full research pipeline
    result = client.research("AI code generation accuracy", max_papers=5, year_from=2024)
"""

import json
import os
import re
import subprocess
import time
from pathlib import Path

import requests
from dotenv import load_dotenv


def _find_and_load_env():
    current = Path(__file__).resolve().parent
    for _ in range(5):
        candidate = current / ".env"
        if candidate.exists():
            load_dotenv(candidate)
            return
        current = current.parent

_find_and_load_env()

# Rate limiter
_last_request = 0.0


def _rate_limit(delay: float = 0.2):
    """Polite delay between requests."""
    global _last_request
    elapsed = time.time() - _last_request
    if elapsed < delay:
        time.sleep(delay - elapsed)
    _last_request = time.time()


def _reconstruct_abstract(inverted_index: dict) -> str:
    """Reconstruct abstract from OpenAlex's inverted index format."""
    if not inverted_index:
        return ""
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort()
    return " ".join(w for _, w in word_positions)


class AcademicClient:
    """Academic paper search via OpenAlex + Unpaywall + Firecrawl."""

    OPENALEX_BASE = "https://api.openalex.org"
    UNPAYWALL_BASE = "https://api.unpaywall.org/v2"
    # Set CONTACT_EMAIL in .env for OpenAlex's polite pool (faster, fewer 429s)
    EMAIL = os.environ.get("CONTACT_EMAIL", "").strip()

    def __init__(self):
        self.session = requests.Session()
        ua = "AIOS-Research/1.0" + (f" (mailto:{self.EMAIL})" if self.EMAIL else "")
        self.session.headers.update({
            "User-Agent": ua,
            "Accept": "application/json",
        })

    def _polite(self, params: dict) -> dict:
        """Add the OpenAlex polite-pool mailto param when an email is set."""
        if self.EMAIL:
            params = {**params, "mailto": self.EMAIL}
        return params

    # ─── OpenAlex: Search & Discovery ─────────────────────────────

    def search(
        self,
        query: str,
        limit: int = 10,
        year_from: int | None = None,
        year_to: int | None = None,
        open_access_only: bool = False,
        sort: str = "relevance_score:desc",
        cited_by_min: int | None = None,
    ) -> list[dict]:
        """
        Search for academic papers via OpenAlex.

        Args:
            query: Search topic
            limit: Max results (up to 200 per page)
            year_from: Filter papers published from this year
            year_to: Filter papers published up to this year
            open_access_only: Only return open access papers
            sort: Sort order (relevance_score:desc, cited_by_count:desc, publication_date:desc)
            cited_by_min: Minimum citation count filter

        Returns:
            List of paper dicts with title, abstract, authors, year, citations, DOI, OA status
        """
        _rate_limit()

        filters = []
        if year_from:
            filters.append(f"from_publication_date:{year_from}-01-01")
        if year_to:
            filters.append(f"to_publication_date:{year_to}-12-31")
        if open_access_only:
            filters.append("open_access.is_oa:true")
        if cited_by_min:
            filters.append(f"cited_by_count:>{cited_by_min}")

        params = {
            "search": query,
            "per_page": min(limit, 200),
            "sort": sort,
        }
        if filters:
            params["filter"] = ",".join(filters)

        try:
            resp = self.session.get(f"{self.OPENALEX_BASE}/works", params=self._polite(params), timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"OpenAlex search failed: {e} (tip: set CONTACT_EMAIL in .env for the polite pool)")
            return []

        results = data.get("results", [])
        total = data.get("meta", {}).get("count", 0)

        papers = []
        for r in results:
            abstract = _reconstruct_abstract(r.get("abstract_inverted_index", {}))

            # Extract authors
            authors = []
            for a in r.get("authorships", [])[:5]:
                name = a.get("author", {}).get("display_name", "")
                institution = ""
                insts = a.get("institutions", [])
                if insts:
                    institution = insts[0].get("display_name", "")
                if name:
                    authors.append({"name": name, "institution": institution})

            # Open access info
            oa = r.get("open_access", {})
            oa_url = oa.get("oa_url", "")

            # Primary location (journal/venue)
            location = r.get("primary_location", {}) or {}
            source = location.get("source", {}) or {}
            venue = source.get("display_name", "")

            doi = r.get("doi", "")
            if doi and doi.startswith("https://doi.org/"):
                doi_short = doi.replace("https://doi.org/", "")
            else:
                doi_short = doi

            papers.append({
                "title": r.get("title", ""),
                "abstract": abstract,
                "year": r.get("publication_year"),
                "cited_by": r.get("cited_by_count", 0),
                "doi": doi_short,
                "doi_url": doi,
                "open_access": oa.get("is_oa", False),
                "oa_url": oa_url,
                "authors": authors,
                "venue": venue,
                "type": r.get("type", ""),
                "openalex_id": r.get("id", ""),
            })

        return papers

    def get_paper(self, doi: str = None, openalex_id: str = None) -> dict | None:
        """Get a specific paper by DOI or OpenAlex ID."""
        _rate_limit()

        if doi:
            url = f"{self.OPENALEX_BASE}/works/doi:{doi}"
        elif openalex_id:
            url = f"{self.OPENALEX_BASE}/works/{openalex_id}"
        else:
            return None

        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None
            r = resp.json()
        except Exception:
            return None

        abstract = _reconstruct_abstract(r.get("abstract_inverted_index", {}))
        authors = [{"name": a.get("author", {}).get("display_name", "")}
                   for a in r.get("authorships", [])[:10]]

        oa = r.get("open_access", {})
        location = r.get("primary_location", {}) or {}
        source = location.get("source", {}) or {}

        doi_val = r.get("doi", "")
        if doi_val and doi_val.startswith("https://doi.org/"):
            doi_val = doi_val.replace("https://doi.org/", "")

        return {
            "title": r.get("title", ""),
            "abstract": abstract,
            "year": r.get("publication_year"),
            "cited_by": r.get("cited_by_count", 0),
            "doi": doi_val,
            "open_access": oa.get("is_oa", False),
            "oa_url": oa.get("oa_url", ""),
            "authors": authors,
            "venue": source.get("display_name", ""),
            "type": r.get("type", ""),
            "referenced_works_count": len(r.get("referenced_works", [])),
            "related_works": r.get("related_works", [])[:5],
        }

    def get_citations(self, openalex_id: str, limit: int = 10) -> list[dict]:
        """Get papers that cite a given paper."""
        _rate_limit()

        try:
            resp = self.session.get(
                f"{self.OPENALEX_BASE}/works",
                params={
                    "filter": f"cites:{openalex_id}",
                    "per_page": limit,
                    "sort": "cited_by_count:desc",
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

        return [{
            "title": r.get("title", ""),
            "year": r.get("publication_year"),
            "cited_by": r.get("cited_by_count", 0),
            "doi": (r.get("doi", "") or "").replace("https://doi.org/", ""),
            "openalex_id": r.get("id", ""),
        } for r in data.get("results", [])]

    # ─── Unpaywall: Free PDF Finder ──────────────────────────────

    def find_free_pdf(self, doi: str) -> str | None:
        """Find a free legal PDF for a paywalled paper via Unpaywall."""
        _rate_limit()

        clean_doi = doi.replace("https://doi.org/", "")
        try:
            resp = self.session.get(
                f"{self.UNPAYWALL_BASE}/{clean_doi}",
                params={"email": self.EMAIL},
                timeout=10,
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            best = data.get("best_oa_location", {}) or {}
            return best.get("url_for_pdf") or best.get("url")
        except Exception:
            return None

    # ─── Full Text Extraction ────────────────────────────────────

    def get_full_text(self, url: str) -> str | None:
        """Scrape full article text from a URL via Firecrawl."""
        try:
            result = subprocess.run(
                ["firecrawl", "scrape", url, "--json"],
                capture_output=True, text=True, timeout=30,
                cwd=str(Path(__file__).resolve().parent.parent.parent),
            )
            if result.returncode != 0:
                return None
            data = json.loads(result.stdout)
            if isinstance(data, dict):
                return data.get("markdown", data.get("content", ""))
            elif isinstance(data, list) and data:
                return data[0].get("markdown", "")
            return None
        except Exception:
            return None

    # ─── Combined Research Pipeline ──────────────────────────────

    def research(
        self,
        query: str,
        max_papers: int = 5,
        search_limit: int = 15,
        year_from: int | None = 2024,
        extract_full_text: bool = False,
        find_free_pdfs: bool = True,
    ) -> dict:
        """
        Full research pipeline: search → enrich with free PDFs → optionally extract full text.

        Args:
            query: Research topic
            max_papers: How many papers to fully process
            search_limit: How many search results to consider
            year_from: Minimum publication year
            extract_full_text: Scrape full article text (slower, uses Firecrawl credits)
            find_free_pdfs: Look up free PDFs via Unpaywall for paywalled papers

        Returns:
            dict with: query, papers (list with abstracts, PDFs, optionally full text)
        """
        # Step 1: Search
        papers = self.search(query, limit=search_limit, year_from=year_from)

        # Step 2: Take top N
        top_papers = papers[:max_papers]

        # Step 3: Enrich with free PDFs
        if find_free_pdfs:
            for paper in top_papers:
                if not paper.get("open_access") and paper.get("doi"):
                    pdf_url = self.find_free_pdf(paper["doi"])
                    if pdf_url:
                        paper["free_pdf_url"] = pdf_url
                        paper["open_access"] = True

        # Step 4: Optionally extract full text
        if extract_full_text:
            for paper in top_papers:
                url = paper.get("oa_url") or paper.get("free_pdf_url")
                if url:
                    text = self.get_full_text(url)
                    if text:
                        paper["full_text"] = text[:50000]  # Cap at 50K chars
                        paper["full_text_length"] = len(text)

        return {
            "query": query,
            "total_found": len(papers),
            "papers_processed": len(top_papers),
            "papers": top_papers,
        }
