"""Export and reporting utilities."""

import csv
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from loguru import logger

from app.core.models import get_session, Article


def export_articles_to_csv(output_path: Path, limit: int = None) -> int:
    """
    Export articles from database to CSV.
    
    Args:
        output_path: Path to output CSV file
        limit: Optional limit on number of articles
        
    Returns:
        Number of articles exported
    """
    session = get_session()
    
    try:
        query = session.query(Article)
        if limit:
            query = query.limit(limit)
        
        articles = query.all()
        
        if not articles:
            logger.warning("No articles to export")
            return 0
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open('w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'doi', 'title', 'authors', 'year', 'journal',
                'abstract', 'url', 'pdf_url', 'source', 'confidence'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for article in articles:
                writer.writerow({
                    'doi': article.doi,
                    'title': article.title,
                    'authors': article.authors,
                    'year': article.year,
                    'journal': article.journal,
                    'abstract': article.abstract,
                    'url': article.url,
                    'pdf_url': article.pdf_url,
                    'source': article.source,
                    'confidence': article.confidence
                })
        
        logger.info(f"Exported {len(articles)} articles to {output_path}")
        return len(articles)
        
    finally:
        session.close()


def generate_coverage_report(output_path: Path, job_stats: Dict = None) -> Dict:
    """
    Generate coverage report with acquisition statistics.
    
    Args:
        output_path: Path to output JSON file
        job_stats: Optional statistics from acquisition job
        
    Returns:
        Report dictionary
    """
    session = get_session()
    
    try:
        # Query database stats
        total_articles = session.query(Article).count()
        articles_with_doi = session.query(Article).filter(Article.doi.isnot(None)).count()
        articles_with_abstract = session.query(Article).filter(Article.abstract.isnot(None)).count()
        articles_with_pdf_url = session.query(Article).filter(Article.pdf_url.isnot(None)).count()
        
        # Build report
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'total_articles': total_articles,
            'coverage': {
                'doi': {
                    'count': articles_with_doi,
                    'percentage': round(articles_with_doi / total_articles * 100, 2) if total_articles > 0 else 0
                },
                'abstract': {
                    'count': articles_with_abstract,
                    'percentage': round(articles_with_abstract / total_articles * 100, 2) if total_articles > 0 else 0
                },
                'pdf_url': {
                    'count': articles_with_pdf_url,
                    'percentage': round(articles_with_pdf_url / total_articles * 100, 2) if total_articles > 0 else 0
                }
            },
            'missing_fields': {
                'doi': total_articles - articles_with_doi,
                'abstract': total_articles - articles_with_abstract,
                'pdf_url': total_articles - articles_with_pdf_url
            }
        }
        
        # Add job stats if provided
        if job_stats:
            report['job_stats'] = job_stats
        
        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Generated coverage report: {output_path}")
        return report
        
    finally:
        session.close()
