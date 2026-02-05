"""Worker thread for running acquisition jobs without blocking UI."""

from PySide6.QtCore import QThread, Signal
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger

from app.services.acquisition.csv_reader import read_journals_csv
from app.services.acquisition.job import acquisition_job
from app.services.acquisition.db_ops import save_articles_batch, save_journal


class AcquisitionWorker(QThread):
    """Worker thread for acquisition jobs."""
    
    # Signals
    progress = Signal(str)  # Progress message
    journal_started = Signal(str)  # Journal name
    journal_completed = Signal(str, int)  # Journal name, article count
    finished = Signal(dict)  # Final stats
    error = Signal(str)  # Error message
    
    def __init__(
        self,
        journals_csv: Path,
        year_from: int,
        year_to: int,
        parent=None
    ):
        super().__init__(parent)
        self.journals_csv = journals_csv
        self.year_from = year_from
        self.year_to = year_to
        self._is_running = True
    
    def stop(self):
        """Stop the acquisition job."""
        self._is_running = False
        logger.info("Acquisition worker stop requested")
    
    def run(self):
        """Run the acquisition job."""
        try:
            self.progress.emit(f"Loading journals from {self.journals_csv}")
            journals = read_journals_csv(self.journals_csv)
            
            if not journals:
                self.error.emit("No journals found in CSV")
                return
            
            self.progress.emit(f"Loaded {len(journals)} journals")
            
            total_articles = 0
            all_stats = {'inserted': 0, 'duplicates': 0, 'errors': 0}
            
            for journal in journals:
                if not self._is_running:
                    self.progress.emit("Acquisition stopped by user")
                    break
                
                journal_name = journal['journal_name']
                issn = journal.get('issn')
                
                self.journal_started.emit(journal_name)
                self.progress.emit(f"Processing: {journal_name}")
                
                # Save journal
                save_journal(journal_name, issn)
                
                # Acquire articles
                articles = []
                for article in acquisition_job(
                    journal_name,
                    self.year_from,
                    self.year_to,
                    issn
                ):
                    if not self._is_running:
                        break
                    articles.append(article.to_dict())
                
                # Save to database
                if articles and self._is_running:
                    stats = save_articles_batch(articles)
                    all_stats['inserted'] += stats['inserted']
                    all_stats['duplicates'] += stats['duplicates']
                    all_stats['errors'] += stats['errors']
                    
                    total_articles += len(articles)
                    self.journal_completed.emit(journal_name, len(articles))
                    self.progress.emit(
                        f"  Saved {stats['inserted']} new articles "
                        f"({stats['duplicates']} duplicates)"
                    )
            
            if self._is_running:
                all_stats['total_articles'] = total_articles
                all_stats['journals_processed'] = len(journals)
                self.finished.emit(all_stats)
            
        except Exception as e:
            logger.exception("Acquisition worker error")
            self.error.emit(str(e))
