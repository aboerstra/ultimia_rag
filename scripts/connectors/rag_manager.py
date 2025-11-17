"""RAG (Retrieval Augmented Generation) Manager using ChromaDB for semantic search."""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pathlib import Path
import json
from typing import List, Dict, Any, Optional
import logging
import re
from collections import Counter
import math
from datetime import datetime

logger = logging.getLogger(__name__)

# Value Stream Classification Keywords
VALUE_STREAM_KEYWORDS = {
    "Application Intake": ["intake", "application", "automated intake", "aio", "deal intake"],
    "Credit Underwriting": ["credit", "underwriting", "scoring", "score", "konga"],
    "Documentation": ["document", "documentation", "docusign", "doc"],
    "Funding": ["funding", "fund"],
    "Servicing & Collections": ["servicing", "collection", "support", "issues"],
    "Client/Broker/Dealer Relationship Management": ["axia", "client", "broker", "relationship", "dealer"],
    "Product & Program Innovation": ["innovation", "product", "program", "enhancement", "enhancements"],
    "Maintenance": ["maintenance", "data model", "integration", "sandbox", "tracking", "merging", "ownership", "metrics", "refresh"]
}


class RAGManager:
    """Manages vector database and semantic search for QBR data."""
    
    def __init__(self, persist_directory: str = "data-sources/vector_db"):
        """Initialize RAG manager with ChromaDB."""
        self.persist_dir = Path(persist_directory)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client (1.3.3 uses PersistentClient)
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        
        # Load embedding model (lightweight, fast)
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="qbr_knowledge"
        )
        
        # Value stream lookup (will be populated during indexing)
        self.value_stream_lookup = {}
        
        logger.info(f"RAG Manager initialized with {self.collection.count()} documents")
    
    def classify_to_value_stream(self, text: str) -> Optional[str]:
        """Classify text into a value stream based on keywords."""
        text_lower = text.lower()
        
        # Count keyword matches for each value stream
        matches = {}
        for vs_name, keywords in VALUE_STREAM_KEYWORDS.items():
            match_count = sum(1 for keyword in keywords if keyword in text_lower)
            if match_count > 0:
                matches[vs_name] = match_count
        
        # Return value stream with most matches, or None
        if matches:
            return max(matches, key=matches.get)
        return None
    
    def build_value_stream_lookup(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Build lookup table from value stream IDs to names."""
        lookup = {}
        if 'valueStreams' in data:
            for vs in data['valueStreams']:
                vs_id = vs.get('id', '')
                vs_name = vs.get('name', '')
                if vs_id and vs_name:
                    lookup[vs_id] = vs_name
        return lookup
    
    def extract_snapshot_date(self, filename: str) -> Optional[str]:
        """
        Extract snapshot date from portfolio filename.
        Supports formats: 
        - portfolio-2025-11-11.json -> "2025-11-11"
        - faye-portfolio-2025-11-11.json -> "2025-11-11"
        - portfolio-2026-Q1.json -> "2026-Q1"
        """
        # Try YYYY-MM-DD format
        match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if match:
            return match.group(1)
        
        # Try YYYY-QX format
        match = re.search(r'(\d{4}-Q[1-4])', filename, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # No date found
        return None
    
    def delete_portfolio_snapshot(self, snapshot_date: str):
        """Delete all documents from a specific portfolio snapshot."""
        try:
            # Get all documents
            all_docs = self.collection.get()
            if not all_docs or not all_docs.get('ids'):
                return
            
            # Find documents matching this snapshot
            ids_to_delete = []
            for i, metadata in enumerate(all_docs.get('metadatas', [])):
                if (metadata.get('source') == 'portfolio-snapshot' and 
                    metadata.get('snapshot_date') == snapshot_date):
                    ids_to_delete.append(all_docs['ids'][i])
            
            # Delete them
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                logger.info(f"Deleted {len(ids_to_delete)} documents from snapshot {snapshot_date}")
        except Exception as e:
            logger.error(f"Error deleting portfolio snapshot {snapshot_date}: {e}")
    
    def is_portfolio_file(self, data: Dict[str, Any]) -> bool:
        """Check if a JSON file is a portfolio/roadmap file."""
        return 'projects' in data and 'valueStreams' in data
    
    def index_document(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        """Index a single document with metadata."""
        try:
            # Generate embedding
            embedding = self.embedder.encode(text).tolist()
            
            # Add to collection
            self.collection.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata]
            )
            logger.debug(f"Indexed document: {doc_id}")
        except Exception as e:
            logger.error(f"Error indexing document {doc_id}: {e}")
    
    def index_all_data(self, project_root: Path):
        """Index all QBR data sources."""
        logger.info("Starting to index all data sources...")
        
        # 1. Index Personas (split into sections for better coverage)
        personas_dir = project_root / 'data-sources' / 'personas'
        if personas_dir.exists():
            for persona_file in personas_dir.glob('*_persona.md'):
                try:
                    with open(persona_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    person_name = persona_file.stem.replace('_persona', '').replace('-', ' ').title()
                    
                    # Split by major headers (# or ##)
                    sections = content.split('\n## ')
                    
                    for i, section in enumerate(sections):
                        if len(section.strip()) > 100:  # Only index substantial sections
                            # Extract section title (first line)
                            lines = section.strip().split('\n')
                            section_title = lines[0].replace('#', '').strip() if lines else f"Section {i}"
                            
                            self.index_document(
                                doc_id=f"persona_{persona_file.stem}_section_{i}",
                                text=section[:2000],  # 2000 chars per section
                                metadata={
                                    "source": "persona",
                                    "name": person_name,
                                    "file": persona_file.name,
                                    "section": section_title
                                }
                            )
                    
                    logger.info(f"Indexed {len(sections)} sections from {person_name}'s persona")
                except Exception as e:
                    logger.error(f"Error indexing persona {persona_file}: {e}")
        
        # 2. Index Individual Transcripts
        transcripts_dir = project_root / 'data-sources' / 'transcripts' / 'extracted'
        if transcripts_dir.exists():
            transcript_files = list(transcripts_dir.glob('*.md'))
            for transcript_file in transcript_files:
                try:
                    with open(transcript_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Split into chunks for better search (2000 chars per chunk)
                    chunks = [content[i:i+2000] for i in range(0, len(content), 2000)]
                    for i, chunk in enumerate(chunks):
                        if len(chunk.strip()) > 100:  # Only index substantial chunks
                            self.index_document(
                                doc_id=f"transcript_{transcript_file.stem}_chunk_{i}",
                                text=chunk,
                                metadata={
                                    "source": "transcript",
                                    "file": transcript_file.name,
                                    "chunk": i,
                                    "total_chunks": len(chunks)
                                }
                            )
                    
                    logger.info(f"Indexed transcript: {transcript_file.name} ({len(chunks)} chunks)")
                except Exception as e:
                    logger.error(f"Error indexing transcript {transcript_file}: {e}")
        
        # 3. Index Transcript Syntheses
        synthesis_file = project_root / 'data-sources' / 'synthesis' / 'transcript-synthesis.md'
        if synthesis_file.exists():
            try:
                with open(synthesis_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Split into sections (by headers)
                sections = content.split('\n## ')
                for i, section in enumerate(sections):
                    if len(section.strip()) > 100:  # Only index substantial sections
                        self.index_document(
                            doc_id=f"synthesis_section_{i}",
                            text=section[:1500],  # First 1500 chars
                            metadata={
                                "source": "synthesis",
                                "section": i
                            }
                        )
            except Exception as e:
                logger.error(f"Error indexing synthesis: {e}")
        
        # 4. Index Jira Issues (ALL issues with rich metadata and value stream classification)
        jira_file = project_root / 'data-sources' / 'jira' / 'raw' / 'issues.json'
        if jira_file.exists():
            try:
                with open(jira_file, 'r') as f:
                    issues = json.load(f)
                
                # First pass: Build epic lookup (epic_key -> epic_name) and classify epics
                epic_lookup = {}
                epic_value_streams = {}
                
                for issue in issues:
                    if issue.get('type') == 'Epic':
                        epic_key = issue.get('key', '')
                        epic_name = issue.get('summary', '')
                        epic_lookup[epic_key] = epic_name
                        
                        # Classify epic to value stream
                        vs = self.classify_to_value_stream(epic_name)
                        if vs:
                            epic_value_streams[epic_key] = vs
                
                # Second pass: Index ALL issues with enriched metadata
                for i, issue in enumerate(issues):
                    issue_type = issue.get('type', 'Unknown')
                    issue_key = issue.get('key', '')
                    issue_summary = issue.get('summary', '')
                    
                    # Determine value stream
                    value_stream = None
                    epic_name = None
                    
                    if issue_type == 'Epic':
                        # This IS an epic - use its classification
                        value_stream = epic_value_streams.get(issue_key)
                        epic_name = issue_summary  # The epic name is the issue summary
                    else:
                        # This is a task/story - inherit from parent epic
                        epic_link = issue.get('epic_link', '')
                        if epic_link:
                            epic_name = epic_lookup.get(epic_link, epic_link)
                            value_stream = epic_value_streams.get(epic_link)
                    
                    # Build comprehensive summary
                    summary_parts = [
                        f"Issue: {issue_key}: {issue_summary}",
                        f"Type: {issue_type}",
                        f"Status: {issue.get('status', 'Unknown')}",
                        f"Priority: {issue.get('priority', 'Unknown')}"
                    ]
                    
                    # Add value stream if classified
                    if value_stream:
                        summary_parts.append(f"Value Stream: {value_stream}")
                    
                    # Add epic info if present
                    if epic_name and issue_type != 'Epic':
                        summary_parts.append(f"Epic: {epic_name}")
                    
                    # Add assignee
                    assignee = issue.get('assignee', 'Unassigned')
                    summary_parts.append(f"Assignee: {assignee}")
                    
                    # Add reporter
                    if issue.get('reporter'):
                        summary_parts.append(f"Reporter: {issue.get('reporter')}")
                    
                    # Add labels if present
                    labels = issue.get('labels', [])
                    if labels:
                        summary_parts.append(f"Labels: {', '.join(labels)}")
                    
                    # Add story points if present
                    if issue.get('story_points'):
                        summary_parts.append(f"Story Points: {issue.get('story_points')}")
                    
                    # Add project
                    if issue.get('project'):
                        summary_parts.append(f"Project: {issue.get('project')}")
                    
                    summary = "\n".join(summary_parts)
                    
                    # Build metadata
                    metadata = {
                        "source": "jira",
                        "key": issue_key,
                        "summary": issue_summary,
                        "status": issue.get('status', ''),
                        "type": issue_type,
                        "priority": issue.get('priority', ''),
                        "assignee": assignee
                    }
                    
                    # Add value stream to metadata if classified
                    if value_stream:
                        metadata["value_stream"] = value_stream
                    
                    # Add epic name to metadata if present
                    if epic_name:
                        metadata["epic_name"] = epic_name
                    
                    self.index_document(
                        doc_id=f"jira_{issue_key}",
                        text=summary,
                        metadata=metadata
                    )
                
                logger.info(f"Indexed {len(issues)} Jira issues ({len(epic_lookup)} epics with {len(epic_value_streams)} classified to value streams)")
            except Exception as e:
                logger.error(f"Error indexing Jira issues: {e}")
        
        # 5. Index Clockify Time Entries (individual entries with user details)
        clockify_entries_file = project_root / 'data-sources' / 'clockify' / 'raw' / 'time_entries.json'
        if clockify_entries_file.exists():
            try:
                with open(clockify_entries_file, 'r') as f:
                    entries = json.load(f)
                
                # Group entries by user for better context
                user_entries = {}
                for entry in entries:
                    user = entry.get('user_name', 'Unknown')
                    if user not in user_entries:
                        user_entries[user] = []
                    user_entries[user].append(entry)
                
                # Index entries in chunks per user
                for user_name, user_time_entries in user_entries.items():
                    # Create chunks of 10 entries each
                    chunk_size = 10
                    for chunk_idx, i in enumerate(range(0, len(user_time_entries), chunk_size)):
                        chunk_entries = user_time_entries[i:i+chunk_size]
                        
                        summary = f"Clockify Time Entries for {user_name}:\n\n"
                        total_hours = 0
                        
                        for entry in chunk_entries:
                            summary += f"- {entry.get('description', 'No description')}\n"
                            summary += f"  Project: {entry.get('project_name', 'Unknown')}\n"
                            summary += f"  Date: {entry.get('start', '')[:10]}\n"
                            summary += f"  Hours: {entry.get('hours', 0)}\n"
                            summary += f"  Billable: {'Yes' if entry.get('billable') else 'No'}\n\n"
                            total_hours += entry.get('hours', 0)
                        
                        summary += f"Total Hours in this chunk: {total_hours}\n"
                        
                        self.index_document(
                            doc_id=f"clockify_entries_{user_name.replace(' ', '_')}_{chunk_idx}",
                            text=summary,
                            metadata={
                                "source": "clockify",
                                "user_name": user_name,
                                "entry_count": len(chunk_entries),
                                "chunk": chunk_idx,
                                "total_hours": total_hours
                            }
                        )
                
                logger.info(f"Indexed {len(entries)} Clockify time entries for {len(user_entries)} users")
            except Exception as e:
                logger.error(f"Error indexing Clockify time entries: {e}")
        
        # Also index project summaries for quick totals
        clockify_summary_file = project_root / 'data-sources' / 'clockify' / 'raw' / 'project_summary.json'
        if clockify_summary_file.exists():
            try:
                with open(clockify_summary_file, 'r') as f:
                    projects = json.load(f)
                
                summary = "Clockify Project Summaries:\n\n"
                for proj_name, proj_data in projects.items():
                    summary += f"{proj_name}:\n"
                    summary += f"  Total Hours: {proj_data.get('total_hours', 0)}\n"
                    summary += f"  Entry Count: {proj_data.get('entry_count', 0)}\n\n"
                
                self.index_document(
                    doc_id="clockify_project_summaries",
                    text=summary,
                    metadata={
                        "source": "clockify",
                        "type": "project_summary",
                        "project_count": len(projects)
                    }
                )
                
                logger.info(f"Indexed {len(projects)} Clockify project summaries")
            except Exception as e:
                logger.error(f"Error indexing Clockify project summaries: {e}")
        
        # 6. Index Salesforce Metrics
        sf_file = project_root / 'data-sources' / 'salesforce' / 'raw' / 'metrics.json'
        if sf_file.exists():
            try:
                with open(sf_file, 'r') as f:
                    metrics = json.load(f)
                
                summary = "Salesforce Metrics:\n"
                for key, value in metrics.items():
                    summary += f"- {key}: {value}\n"
                
                self.index_document(
                    doc_id="salesforce_metrics",
                    text=summary,
                    metadata={"source": "salesforce"}
                )
            except Exception as e:
                logger.error(f"Error indexing Salesforce metrics: {e}")
        
        # 7. Index Confluence Pages
        confluence_dir = project_root / 'data-sources' / 'confluence' / 'raw'
        if confluence_dir.exists():
            # Find any *_pages.json file
            pages_files = list(confluence_dir.glob('*_pages.json'))
            if pages_files:
                try:
                    with open(pages_files[0], 'r') as f:
                        pages = json.load(f)
                    
                    # Index all pages
                    for i, page in enumerate(pages):
                        title = page.get('title', 'Untitled')
                        space = page.get('space', {}).get('key', 'Unknown')
                        body = page.get('body_text', '')[:1500]  # First 1500 chars
                        
                        summary = f"Title: {title}\nSpace: {space}\n\n{body}"
                        
                        self.index_document(
                            doc_id=f"confluence_{page.get('id', i)}",
                            text=summary,
                            metadata={
                                "source": "confluence",
                                "space": space,
                                "title": title,
                                "page_id": page.get('id', '')
                            }
                        )
                    
                    logger.info(f"Indexed {len(pages)} Confluence pages")
                except Exception as e:
                    logger.error(f"Error indexing Confluence pages: {e}")
        
        # 8. Index Custom Context Files (uploaded JSON/text files)
        custom_dir = project_root / 'data-sources' / 'custom-context'
        if custom_dir.exists():
            # Index JSON files
            for json_file in custom_dir.glob('*.json'):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Handle portfolio/initiative files WITH SNAPSHOT SUPPORT
                    if self.is_portfolio_file(data):
                        # Extract snapshot date from filename
                        snapshot_date = self.extract_snapshot_date(json_file.name)
                        
                        # Build value stream lookup
                        vs_lookup = self.build_value_stream_lookup(data)
                        self.value_stream_lookup.update(vs_lookup)
                        
                        # Index each project with value stream NAME and snapshot metadata
                        for project in data.get('projects', []):
                            vs_id = project.get('valueStreamId', '')
                            vs_name = vs_lookup.get(vs_id, vs_id)  # Fall back to ID if not found
                            
                            summary = f"Project: {project.get('name', 'Unknown')}\n"
                            summary += f"Value Stream: {vs_name}\n"  # Use NAME not ID
                            if snapshot_date:
                                summary += f"Snapshot Date: {snapshot_date}\n"
                            summary += f"Status: {project.get('status', '')}\n"
                            summary += f"Priority: {project.get('priority', '')}\n"
                            summary += f"Progress: {project.get('progress', 0)}%\n"
                            summary += f"Description: {project.get('description', '')}\n"
                            
                            # Add milestones
                            milestones = project.get('milestones', [])
                            if milestones:
                                summary += f"\nMilestones:\n"
                                for ms in milestones:
                                    summary += f"- {ms.get('name', '')}: {ms.get('status', '')} ({ms.get('date', '')})\n"
                            
                            # Build metadata with snapshot info
                            metadata = {
                                "source": "portfolio-snapshot",
                                "file": json_file.name,
                                "type": "project",
                                "project_name": project.get('name', ''),
                                "value_stream": vs_name,
                                "status": project.get('status', '')
                            }
                            
                            # Add snapshot date to metadata if available
                            if snapshot_date:
                                metadata["snapshot_date"] = snapshot_date
                            
                            self.index_document(
                                doc_id=f"portfolio_{snapshot_date or json_file.stem}_proj_{project.get('id', '')}",
                                text=summary,
                                metadata=metadata
                            )
                        
                        # Index value streams summary
                        if data.get('valueStreams'):
                            vs_summary = "Value Streams and Strategic Initiatives"
                            if snapshot_date:
                                vs_summary += f" (Snapshot: {snapshot_date})"
                            vs_summary += ":\n\n"
                            for vs in data['valueStreams']:
                                vs_summary += f"{vs.get('name', '')}: {vs.get('description', '')}\n"
                            
                            vs_metadata = {
                                "source": "portfolio-snapshot",
                                "file": json_file.name,
                                "type": "value_streams"
                            }
                            if snapshot_date:
                                vs_metadata["snapshot_date"] = snapshot_date
                            
                            self.index_document(
                                doc_id=f"portfolio_{snapshot_date or json_file.stem}_valuestreams",
                                text=vs_summary,
                                metadata=vs_metadata
                            )
                        
                        log_msg = f"Indexed {len(data.get('projects', []))} projects from {json_file.name}"
                        if snapshot_date:
                            log_msg += f" (snapshot: {snapshot_date})"
                        logger.info(log_msg)
                    else:
                        # Generic JSON indexing
                        content = json.dumps(data, indent=2)[:2000]
                        self.index_document(
                            doc_id=f"custom_{json_file.stem}",
                            text=content,
                            metadata={
                                "source": "custom-context",
                                "file": json_file.name,
                                "type": "json"
                            }
                        )
                        logger.info(f"Indexed custom JSON: {json_file.name}")
                except Exception as e:
                    logger.error(f"Error indexing custom file {json_file}: {e}")
            
            # Index text/markdown files
            for text_file in list(custom_dir.glob('*.txt')) + list(custom_dir.glob('*.md')):
                try:
                    with open(text_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Split into chunks if large
                    chunks = [content[i:i+2000] for i in range(0, len(content), 2000)]
                    for i, chunk in enumerate(chunks[:10]):  # Max 10 chunks per file
                        self.index_document(
                            doc_id=f"custom_{text_file.stem}_chunk_{i}",
                            text=chunk,
                            metadata={
                                "source": "custom-context",
                                "file": text_file.name,
                                "type": "text",
                                "chunk": i
                            }
                        )
                    
                    logger.info(f"Indexed custom text file: {text_file.name} ({len(chunks)} chunks)")
                except Exception as e:
                    logger.error(f"Error indexing custom file {text_file}: {e}")
        
        logger.info(f"Indexing complete. Total documents: {self.collection.count()}")
    
    def _bm25_score(self, query_terms: List[str], doc_text: str, avg_doc_len: float = 100.0, k1: float = 1.5, b: float = 0.75) -> float:
        """Calculate BM25 score for keyword matching."""
        doc_terms = re.findall(r'\w+', doc_text.lower())
        doc_len = len(doc_terms)
        doc_term_freq = Counter(doc_terms)
        
        score = 0.0
        for term in query_terms:
            if term in doc_term_freq:
                tf = doc_term_freq[term]
                # Simplified IDF (not using collection statistics for speed)
                idf = math.log(1 + (1.0 / (tf + 1)))
                # BM25 formula
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * (doc_len / avg_doc_len))
                score += idf * (numerator / denominator)
        
        return score
    
    def _keyword_search(self, query: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """Perform keyword-based search for exact matches."""
        try:
            # Extract all documents
            all_docs = self.collection.get()
            if not all_docs or not all_docs.get('documents'):
                return []
            
            # Prepare query terms
            query_terms = [term.lower() for term in re.findall(r'\w+', query)]
            
            # Check for issue ID pattern (e.g., MAXCOM-292)
            issue_id_pattern = r'\b[A-Z]{2,}-\d+\b'
            issue_ids = re.findall(issue_id_pattern, query.upper())
            
            # Score each document
            scored_docs = []
            for i, doc_text in enumerate(all_docs['documents']):
                metadata = all_docs['metadatas'][i] if all_docs.get('metadatas') else {}
                doc_id = all_docs['ids'][i] if all_docs.get('ids') else str(i)
                
                # Boost score for exact issue ID matches
                boost = 0.0
                for issue_id in issue_ids:
                    if issue_id in doc_text.upper():
                        boost += 100.0  # Strong boost for exact ID match
                    if metadata.get('key') == issue_id or metadata.get('issue_key') == issue_id:
                        boost += 200.0  # Even stronger boost for metadata match
                
                # Calculate BM25 score
                bm25_score = self._bm25_score(query_terms, doc_text)
                total_score = bm25_score + boost
                
                if total_score > 0:
                    scored_docs.append({
                        'text': doc_text,
                        'metadata': metadata,
                        'score': total_score,
                        'method': 'keyword'
                    })
            
            # Sort by score and return top results
            scored_docs.sort(key=lambda x: x['score'], reverse=True)
            return scored_docs[:n_results]
            
        except Exception as e:
            logger.error(f"Keyword search error: {e}")
            return []
    
    def search(self, query: str, n_results: int = 5, use_hybrid: bool = True) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic and keyword-based matching.
        
        Args:
            query: Search query
            n_results: Number of results to return
            use_hybrid: If True, combine semantic + keyword search (recommended)
        """
        try:
            if not use_hybrid:
                # Original semantic-only search
                query_embedding = self.embedder.encode(query).tolist()
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results
                )
                
                formatted_results = []
                if results['documents'] and len(results['documents']) > 0:
                    for i in range(len(results['documents'][0])):
                        formatted_results.append({
                            'text': results['documents'][0][i],
                            'metadata': results['metadatas'][0][i],
                            'distance': results['distances'][0][i] if 'distances' in results else None
                        })
                
                return formatted_results
            
            # HYBRID SEARCH: Combine semantic + keyword
            
            # 1. Get semantic search results (more results to merge later)
            query_embedding = self.embedder.encode(query).tolist()
            semantic_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results * 2  # Get more to ensure good coverage
            )
            
            # 2. Get keyword search results
            keyword_results = self._keyword_search(query, n_results=n_results * 2)
            
            # 3. Merge and rank results
            merged = {}
            
            # Add semantic results (normalized distance scores)
            if semantic_results['documents'] and len(semantic_results['documents']) > 0:
                for i in range(len(semantic_results['documents'][0])):
                    doc_id = semantic_results['ids'][0][i] if 'ids' in semantic_results else str(i)
                    distance = semantic_results['distances'][0][i] if 'distances' in semantic_results else 1.0
                    
                    # Convert distance to similarity score (lower distance = higher score)
                    semantic_score = 1.0 / (1.0 + distance)
                    
                    merged[doc_id] = {
                        'text': semantic_results['documents'][0][i],
                        'metadata': semantic_results['metadatas'][0][i],
                        'semantic_score': semantic_score,
                        'keyword_score': 0.0,
                        'distance': distance
                    }
            
            # Add/boost with keyword results
            for kw_result in keyword_results:
                # Try to find matching doc by text or metadata
                doc_id = None
                for mid, mdata in merged.items():
                    if mdata['text'] == kw_result['text']:
                        doc_id = mid
                        break
                
                if doc_id:
                    # Document found in both - boost it
                    merged[doc_id]['keyword_score'] = kw_result['score']
                else:
                    # New document from keyword search
                    # Create a synthetic ID
                    doc_id = f"keyword_{len(merged)}"
                    merged[doc_id] = {
                        'text': kw_result['text'],
                        'metadata': kw_result['metadata'],
                        'semantic_score': 0.0,
                        'keyword_score': kw_result['score'],
                        'distance': None
                    }
            
            # Calculate final scores (weighted combination)
            for doc in merged.values():
                # Weight: 60% semantic, 40% keyword (keyword helps exact matches)
                doc['final_score'] = (doc['semantic_score'] * 0.6) + (doc['keyword_score'] * 0.4)
            
            # Sort by final score and return top n
            sorted_results = sorted(merged.values(), key=lambda x: x['final_score'], reverse=True)
            
            # Format for return
            formatted_results = []
            for result in sorted_results[:n_results]:
                formatted_results.append({
                    'text': result['text'],
                    'metadata': result['metadata'],
                    'distance': result.get('distance'),
                    'content': result['text']  # Add alias for compatibility
                })
            
            logger.debug(f"Hybrid search returned {len(formatted_results)} results for query: {query[:50]}...")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def get_context_for_query(self, query: str, max_tokens: int = 2000) -> tuple[str, List[str]]:
        """Get relevant context for a query, limited by token count."""
        # Return more results by default for better coverage
        # Use 100 for "list all" queries, 50 for "how many" queries, 30 for normal queries
        if any(keyword in query.lower() for keyword in ['list all', 'all the', 'all epic', 'show all']):
            n_results = 100
        elif any(keyword in query.lower() for keyword in ['how many', 'count', 'total']):
            n_results = 50
        else:
            n_results = 30
        
        results = self.search(query, n_results=n_results)
        
        context_parts = []
        sources = []
        total_chars = 0
        max_chars = max_tokens * 4  # Rough estimate: 4 chars per token
        
        for result in results:
            text = result['text']
            metadata = result['metadata']
            source = metadata.get('source', 'unknown')
            
            # Add source attribution with value stream info where available
            if source == 'persona':
                header = f"\n--- PERSONA: {metadata.get('name', 'Unknown')} ---\n"
            elif source == 'transcript':
                file_name = metadata.get('file', 'Unknown')
                chunk_info = f"(chunk {metadata.get('chunk', 0) + 1}/{metadata.get('total_chunks', 1)})"
                header = f"\n--- TRANSCRIPT: {file_name} {chunk_info} ---\n"
            elif source == 'jira':
                # Enhanced Jira header with value stream and epic info
                jira_key = metadata.get('key', '')
                jira_type = metadata.get('type', '')
                vs = metadata.get('value_stream', '')
                epic_name = metadata.get('epic_name', '')
                
                header_parts = [f"JIRA {jira_type}: {jira_key}"]
                if vs:
                    header_parts.append(f"Value Stream: {vs}")
                if epic_name and jira_type != 'Epic':
                    header_parts.append(f"Epic: {epic_name}")
                
                header = f"\n--- {' | '.join(header_parts)} ---\n"
            elif source == 'synthesis':
                header = f"\n--- MEETING INSIGHTS (Section {metadata.get('section', '')}) ---\n"
            elif source == 'clockify':
                proj_name = metadata.get('project', 'Unknown')
                header = f"\n--- CLOCKIFY: {proj_name} ---\n"
            elif source == 'salesforce':
                header = "\n--- SALESFORCE METRICS ---\n"
            elif source == 'confluence':
                header = f"\n--- CONFLUENCE: {metadata.get('title', 'Unknown')} ({metadata.get('space', '')}) ---\n"
            elif source == 'portfolio-snapshot':
                project_name = metadata.get('project_name', metadata.get('type', 'Unknown'))
                vs = metadata.get('value_stream', '')
                snapshot_date = metadata.get('snapshot_date', '')
                
                header_parts = [f"PORTFOLIO: {project_name}"]
                if vs:
                    header_parts.append(f"Value Stream: {vs}")
                if snapshot_date:
                    header_parts.append(f"Snapshot: {snapshot_date}")
                
                header = f"\n--- {' | '.join(header_parts)} ---\n"
            elif source == 'custom-context':
                file_name = metadata.get('file', 'Unknown')
                header = f"\n--- CUSTOM CONTEXT: {file_name} ---\n"
            else:
                header = f"\n--- {source.upper()} ---\n"
            
            chunk = header + text
            
            if total_chars + len(chunk) > max_chars:
                break
            
            context_parts.append(chunk)
            if source not in sources:
                sources.append(source.title())
            total_chars += len(chunk)
        
        return '\n'.join(context_parts), sources
    
    def get_stats(self, project_root: Path) -> Dict[str, Any]:
        """Get comprehensive statistics about indexed data."""
        stats = {
            "total_documents": self.collection.count(),
            "sources": {}
        }
        
        # Get all metadata to count by source
        try:
            all_docs = self.collection.get()
            if all_docs and all_docs.get('metadatas'):
                source_counts = {}
                for metadata in all_docs['metadatas']:
                    source = metadata.get('source', 'unknown')
                    source_counts[source] = source_counts.get(source, 0) + 1
                
                stats["sources"] = source_counts
        except:
            pass
        
        # Add detailed counts from source files
        # Jira
        jira_file = project_root / 'data-sources' / 'jira' / 'raw' / 'issues.json'
        if jira_file.exists():
            try:
                with open(jira_file, 'r') as f:
                    issues = json.load(f)
                    stats["jira"] = {
                        "total_issues": len(issues),
                        "epics": len([i for i in issues if i.get('type') == 'Epic']),
                        "stories": len([i for i in issues if i.get('type') == 'Story']),
                        "tasks": len([i for i in issues if i.get('type') == 'Task']),
                        "bugs": len([i for i in issues if i.get('type') == 'Bug']),
                        "by_status": {}
                    }
                    # Count by status
                    for issue in issues:
                        status = issue.get('status', 'Unknown')
                        stats["jira"]["by_status"][status] = stats["jira"]["by_status"].get(status, 0) + 1
            except:
                pass
        
        # Clockify
        clockify_file = project_root / 'data-sources' / 'clockify' / 'raw' / 'project_summary.json'
        if clockify_file.exists():
            try:
                with open(clockify_file, 'r') as f:
                    projects = json.load(f)
                    total_hours = sum(p.get('total_hours', 0) for p in projects.values())
                    stats["clockify"] = {
                        "total_projects": len(projects),
                        "total_hours": round(total_hours, 2)
                    }
            except:
                pass
        
        # Transcripts
        transcripts_dir = project_root / 'data-sources' / 'transcripts' / 'extracted'
        if transcripts_dir.exists():
            md_files = list(transcripts_dir.glob('*.md'))
            stats["transcripts"] = {
                "total_files": len(md_files)
            }
        
        # Confluence
        confluence_dir = project_root / 'data-sources' / 'confluence' / 'raw'
        if confluence_dir.exists():
            pages_files = list(confluence_dir.glob('*_pages.json'))
            if pages_files:
                try:
                    with open(pages_files[0], 'r') as f:
                        pages = json.load(f)
                        stats["confluence"] = {
                            "total_pages": len(pages)
                        }
                except:
                    pass
        
        return stats
    
    def get_epic_list(self, project_root: Path) -> List[Dict[str, Any]]:
        """Get list of all epics with metadata."""
        epics = []
        jira_file = project_root / 'data-sources' / 'jira' / 'raw' / 'issues.json'
        
        if jira_file.exists():
            try:
                with open(jira_file, 'r') as f:
                    issues = json.load(f)
                    
                for issue in issues:
                    if issue.get('type') == 'Epic':
                        epic_key = issue.get('key', '')
                        epic_name = issue.get('summary', '')
                        
                        # Classify epic to value stream
                        vs = self.classify_to_value_stream(epic_name)
                        
                        epics.append({
                            "key": epic_key,
                            "name": epic_name,
                            "value_stream": vs,
                            "status": issue.get('status', ''),
                            "assignee": issue.get('assignee', 'Unassigned')
                        })
            except:
                pass
        
        return epics
    
    def reindex(self, project_root: Path):
        """Clear and reindex all data."""
        logger.info("Clearing existing index...")
        # Delete and recreate collection
        try:
            self.client.delete_collection(name="qbr_knowledge")
        except:
            pass
        
        self.collection = self.client.get_or_create_collection(
            name="qbr_knowledge"
        )
        
        # Reindex
        self.index_all_data(project_root)
