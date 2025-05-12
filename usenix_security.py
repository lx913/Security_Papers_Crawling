import requests
from bs4 import BeautifulSoup
import time
import csv
import os
import re
import argparse
from pathlib import Path


class UsernixScraper:
    def __init__(self, args):
        self.base_url = "https://www.usenix.org"
        self.output_file = args.output
        self.papers_dir = args.save_dir
        self.download_pdf = args.pdf
        self.keywords = args.keywords
        self.years = args.years
        self.terms = args.terms
        self.verbose = args.verbose

        # Statistics
        self.total_papers = 0
        self.filtered_papers = 0
        self.downloaded_pdfs = 0
        self.failed_downloads = 0

    def get_paper_urls(self):
        """Generate all paper URLs based on years and terms."""
        urls = []
        for year in self.years:
            for term in self.terms:
                if term == "cycle1":  # Handle special case for "cycle1"
                    url = f"{self.base_url}/conference/usenixsecurity{year}/{term}-accepted-papers"
                else:
                    url = f"{self.base_url}/conference/usenixsecurity{year}/{term}-accepted-papers"
                urls.append((url, year, term))
        return urls

    def get_paper_blocks(self, url):
        """Scrape all paper blocks (<article>) from a given URL."""
        try:
            res = requests.get(url)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            papers = soup.select("article.node-paper")
            if self.verbose:
                print(f"Found {len(papers)} papers at {url}")
            return papers
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return []

    def extract_paper_data(self, article_tag, year, term):
        """Extract title, detail URL, authors, description, and PDF link from <article>."""
        title_tag = article_tag.select_one("h2 a")
        if not title_tag:
            return None

        detail_url = self.base_url + title_tag["href"]
        title = title_tag.text.strip()

        # Authors
        authors_tag = article_tag.select_one(".field-name-field-paper-people-text")
        authors = authors_tag.get_text(separator=" ", strip=True) if authors_tag else "N/A"

        # Abstract/Description
        abstract_tag = article_tag.select_one(".field-name-field-paper-description-long")
        abstract = abstract_tag.get_text(separator=" ", strip=True) if abstract_tag else "N/A"

        # PDF Link (optional presence)
        pdf_tag = article_tag.select_one("span.usenix-schedule-media.pdf a")
        pdf_link = self.base_url + pdf_tag["href"] if pdf_tag else "N/A"

        return {
            "title": title.strip(),
            "url": detail_url.strip(),
            "authors": authors.strip(),
            "abstract": abstract.strip(),
            "pdf_link": pdf_link.strip(),
            "year": year.strip(),
            "term": term.strip(),
            "local_pdf_path": "N/A"  # Will be updated if PDF is downloaded
        }

    def check_keywords(self, abstract):
        """Check if the abstract contains any of the keywords."""
        if not self.keywords:
            return True

        abstract_lower = abstract.lower()
        for keyword in self.keywords:
            if keyword.lower() in abstract_lower:
                return True
        return False

    def sanitize_filename(self, title):
        """Create a safe filename from paper title."""
        # Replace invalid filename characters with underscores
        safe_name = re.sub(r'[\\/*?:"<>|]', "_", title)
        # Replace multiple spaces with single underscore
        safe_name = re.sub(r'\s+', "_", safe_name)
        # Limit length and remove trailing underscores
        return safe_name[:100].rstrip("_")

    def download_paper(self, paper_data):
        """Download paper PDF and save to the specified directory."""
        if not self.download_pdf:
            return False

        if paper_data["pdf_link"] == "N/A":
            if self.verbose:
                print(f"No PDF link available for: {paper_data['title']}")
            return False

        # Create output directory structure: {papers_dir}/{year}/{term}/
        dir_path = os.path.join(self.papers_dir, paper_data["year"], paper_data["term"])
        Path(dir_path).mkdir(parents=True, exist_ok=True)

        # Create a safe filename
        filename = self.sanitize_filename(paper_data["title"]) + ".pdf"
        file_path = os.path.join(dir_path, filename)

        # Check if file already exists
        if os.path.exists(file_path):
            if self.verbose:
                print(f"File already exists: {filename}")
            return file_path

        # Download the PDF
        try:
            if self.verbose:
                print(f"Downloading: {paper_data['title']}")
            res = requests.get(paper_data["pdf_link"], stream=True)
            res.raise_for_status()

            # Save to file
            with open(file_path, 'wb') as f:
                for chunk in res.iter_content(chunk_size=8192):
                    f.write(chunk)

            if self.verbose:
                print(f"Successfully saved: {filename}")
            self.downloaded_pdfs += 1
            return file_path
        except Exception as e:
            if self.verbose:
                print(f"Error downloading {paper_data['title']}: {e}")
            self.failed_downloads += 1
            return False

    def run(self):
        """Run the scraper to collect papers and optionally download PDFs."""
        # Make sure output directory exists
        base_dir = os.path.dirname(self.output_file)
        if base_dir:
            Path(base_dir).mkdir(parents=True, exist_ok=True)

        # Get all paper URLs
        paper_urls = self.get_paper_urls()
        if self.verbose:
            print(f"Processing {len(paper_urls)} sources...")

        # Field names for the CSV header
        fieldnames = ["title", "url", "authors", "abstract", "pdf_link", "year", "term", "local_pdf_path"]

        # Write to CSV
        with open(self.output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            # Process each paper URL
            for url, year, term in paper_urls:
                print(f"\nProcessing papers from USENIX Security {year} ({term})...")
                papers = self.get_paper_blocks(url)

                for i, article in enumerate(papers, 1):
                    # Extract paper data
                    data = self.extract_paper_data(article, year, term)
                    if not data:
                        continue

                    self.total_papers += 1

                    # Filter by keywords if specified
                    if not self.check_keywords(data["abstract"]):
                        continue

                    self.filtered_papers += 1

                    # Print progress
                    if self.verbose:
                        print(f"\nProcessing paper {i}/{len(papers)}: {data['title']}")

                    # Download PDF if enabled
                    if self.download_pdf:
                        file_path = self.download_paper(data)
                        if file_path:
                            data["local_pdf_path"] = file_path

                    # Write to CSV
                    writer.writerow(data)

                    # Delay to be gentle with the server
                    time.sleep(0.1)

        # Print summary
        print(f"\nSummary:")
        print(f"- Total papers found: {self.total_papers}")
        if self.keywords:
            print(f"- Papers matching keywords ({', '.join(self.keywords)}): {self.filtered_papers}")

        if self.download_pdf:
            print(f"- Successfully downloaded PDFs: {self.downloaded_pdfs}")
            print(f"- Failed PDF downloads: {self.failed_downloads}")

        print(f"- Papers information saved to: {os.path.abspath(self.output_file)}")
        if self.download_pdf:
            print(f"- PDFs saved to: {os.path.abspath(self.papers_dir)}")


def parse_args():
    parser = argparse.ArgumentParser(description="USENIX Security Papers Scraper")

    parser.add_argument("-o", "--output", default="usenix_security_papers.csv",
                        help="Output CSV file path (default: usenix_security_papers.csv)")

    parser.add_argument("-d", "--save-dir", default="paper/usenix_security",
                        help="Directory to save PDF papers (default: paper/usenix_security)")

    parser.add_argument("--pdf", action="store_true",
                        help="Download PDF papers (default: False)")

    parser.add_argument("-k", "--keywords", nargs="+",
                        help="Filter papers by keywords in abstract")

    parser.add_argument("-y", "--years", nargs="+", default=["20", "21", "22", "23", "24", "25"],
                        help="Years to scrape (default: 20 21 22 23 24)")

    parser.add_argument("-t", "--terms", nargs="+", default=["summer", "spring", "fall", "winter", "cycle1", "cycle2"],
                        help="Terms to scrape (default: summer spring fall winter cycle1)")

    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    scraper = UsernixScraper(args)
    scraper.run()
