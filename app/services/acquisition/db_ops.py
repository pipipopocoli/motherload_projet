"""Database operations for acquisition service."""

from typing import List, Dict
from sqlalchemy.exc import IntegrityError
from loguru import logger

from app.core.models import get_session, Article, Journal


def save_articles_batch(articles: List[Dict], batch_size: int = 100) -> Dict[str, int]:
    """
    Save articles to database in batches.
    
    Args:
        articles: List of article dictionaries
        batch_size: Number of articles to commit at once
        
    Returns:
        Dictionary with 'inserted', 'duplicates', 'errors' counts
    """
    stats = {'inserted': 0, 'duplicates': 0, 'errors': 0}
    session = get_session()
    
    try:
        for i, article_data in enumerate(articles):
            try:
                article = Article(**article_data)
                session.add(article)
                
                # Commit in batches
                if (i + 1) % batch_size == 0:
                    session.commit()
                    logger.debug(f"Committed batch at {i + 1} articles")
                    stats['inserted'] += batch_size
            
            except IntegrityError:
                session.rollback()
                stats['duplicates'] += 1
                logger.debug(f"Duplicate article (DOI: {article_data.get('doi')})")
            
            except Exception as e:
                session.rollback()
                stats['errors'] += 1
                logger.error(f"Error saving article: {e}")
        
        # Commit remaining
        session.commit()
        remaining = len(articles) % batch_size
        stats['inserted'] += remaining
        
        logger.info(
            f"Saved articles: {stats['inserted']} inserted, "
            f"{stats['duplicates']} duplicates, {stats['errors']} errors"
        )
        
    finally:
        session.close()
    
    return stats


def save_journal(journal_name: str, issn: str = None) -> int:
    """
    Save journal to database.
    
    Args:
        journal_name: Name of the journal
        issn: Optional ISSN
        
    Returns:
        Journal ID
    """
    session = get_session()
    
    try:
        # Check if journal exists
        journal = session.query(Journal).filter_by(name=journal_name).first()
        
        if not journal:
            journal = Journal(name=journal_name, issn=issn)
            session.add(journal)
            session.commit()
            logger.info(f"Created journal: {journal_name}")
        
        return journal.id
        
    finally:
        session.close()
