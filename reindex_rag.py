"""Script to reindex RAG system with progress tracking."""
from scripts.connectors.rag_manager import RAGManager
from pathlib import Path

print("Starting RAG reindex...")
rag = RAGManager()
project_root = Path('.')

print("Reindexing all data sources (this may take a minute)...")
rag.reindex(project_root)

print("\n✓ Reindex complete!")
print("\n=== Final Statistics ===")
stats = rag.get_stats(project_root)
print(f'Total documents: {stats["total_documents"]}')
print(f'\nDocuments by source:')
for source, count in sorted(stats.get('sources', {}).items()):
    print(f'  {source}: {count}')

# Test Clockify search
print('\n=== Testing Clockify Search ===')
results = rag.search('Vinay Vernekar Clockify time hours', n_results=5)
clockify_count = sum(1 for r in results if r['metadata'].get('source') == 'clockify')
print(f'Found {len(results)} total results, {clockify_count} from Clockify')

for i, result in enumerate(results[:3], 1):
    if result['metadata'].get('source') == 'clockify':
        print(f'\nClockify Result {i}:')
        print(f'  User: {result["metadata"].get("user_name")}')
        print(f'  Total Hours: {result["metadata"].get("total_hours")}')
        print(f'  Entries: {result["metadata"].get("entry_count")}')
