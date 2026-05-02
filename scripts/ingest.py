#!/usr/bin/env python3
import sys
import os
import json
import hashlib
from urllib.parse import urlparse

# Placeholder imports for web extraction and wiki manipulation
# In a real environment, replace these with actual implementations

import urllib.request
import urllib.error

def web_extract(url):
    """
    Extracts clean markdown from a URL using the Jina Reader API.
    This strips out ads/navigation and returns pure LLM-friendly markdown.
    """
    print(f"Extracting content from {url}...")
    jina_url = f"https://r.jina.ai/{url}"
    req = urllib.request.Request(jina_url, headers={'User-Agent': 'Mozilla/5.0 (Wiki Ingest)'})
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except urllib.error.URLError as e:
        print(f"Warning: Failed to extract {url} - {str(e)}")
        return f"# Article Extraction Failed\n\nURL: {url}\nError: {str(e)}"


def slugify(title):
    import re
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip('-')
    return slug

wiki_root = os.path.expanduser('~/wiki')
raw_articles = os.path.join(wiki_root, 'raw', 'articles')
concepts_dir = os.path.join(wiki_root, 'concepts')
entities_dir = os.path.join(wiki_root, 'entities')
index_md = os.path.join(wiki_root, 'index.md')
log_md = os.path.join(wiki_root, 'log.md')


def ensure_dirs():
    for d in [raw_articles, concepts_dir, entities_dir]:
        os.makedirs(d, exist_ok=True)


def write_frontmatter(path, fm):
    with open(path, 'w') as f:
        f.write('---\n')
        for k, v in fm.items():
            f.write(f"{k}: {v}\n")
        f.write('---\n')


def append_log(entry):
    with open(log_md, 'a') as f:
        f.write(f"## {entry}\n")


def add_or_update_concept(concept_title, domains, tags, sources):
    slug = slugify(concept_title)
    p = os.path.join(concepts_dir, f"{slug}.md")
    if not os.path.exists(p):
        fm = {
            'title': concept_title,
            'created': '2026-05-02',
            'updated': '2026-05-02',
            'type': 'concept',
            'domains': domains,
            'tags': ", ".join(tags),
            'sources': f"[raw/articles/{slug}.md]"
        }
        write_frontmatter(p, fm)
    # Append body if needed (not implemented fully here)
    return p


def add_or_update_entity(entity_title, domains, tags):
    slug = slugify(entity_title)
    p = os.path.join(entities_dir, f"{slug}.md")
    if not os.path.exists(p):
        fm = {
            'title': entity_title,
            'created': '2026-05-02',
            'updated': '2026-05-02',
            'type': 'entity',
            'domains': domains,
            'tags': ", ".join(tags)
        }
        write_frontmatter(p, fm)
    return p


def best_guess_tags(domain, text):
    taxonomy = {
        'personal-knowledge': ['travel','bike','fitness','health','family','homelab'],
        'work-knowledge': ['contacts','companies','medical-knowledge','nemt-industry']
    }
    tags = taxonomy.get(domain, [])
    hits = []
    for t in tags:
        if t in text:
            hits.append(t)
    return hits[:4]


def update_index_with_concept(concept_title):
    slug = slugify(concept_title)
    with open(index_md, 'a') as f:
        f.write(f"- [[{slug}|{concept_title}]]\n")


def main():
    ensure_dirs()
    if len(sys.argv) < 2:
        print("Usage: ingest.py url|note --domain DOMAIN [--tags TAG1,TAG2] [--notes \"...\"]")
        sys.exit(1)
    cmd = sys.argv[1]
    # Very rough argument parsing for demonstration
    domain = None
    tags = None
    title = None
    url = None
    note = None
    if cmd == 'url':
        if len(sys.argv) >= 3:
            url = sys.argv[2]
        else:
            print("Provide a URL to ingest")
            sys.exit(2)
        # Domain required per user request
        if '--domain' in sys.argv:
            idx = sys.argv.index('--domain')
            domain = sys.argv[idx+1] if idx+1 < len(sys.argv) else None
        
        if not domain:
            print("Error: --domain is required. Please specify it (e.g., --domain personal-knowledge).")
            sys.exit(1)
            
        if '--tags' in sys.argv:
            idx = sys.argv.index('--tags')
            tags = sys.argv[idx+1].split(',') if idx+1 < len(sys.argv) else None
        # Optional: title for the concept
        if '--title' in sys.argv:
            idx = sys.argv.index('--title')
            title = sys.argv[idx+1] if idx+1 < len(sys.argv) else None
        # Fetch article
        body = web_extract(url)
        body_path_name = slugify(title or urlparse(url).path.split("/")[-1])
        body_path = os.path.join(raw_articles, f"{body_path_name}.md")
        with open(body_path, 'w') as f:
            f.write(body)
        sha = hashlib.sha256(body.encode('utf-8')).hexdigest()
        # Save raw frontmatter
        write_frontmatter(body_path, {'source_url': url, 'ingested': '2026-05-02', 'sha256': sha})
        # Best guess tags if not provided
        if not tags:
            text = body
            tags = best_guess_tags(domain, text) or ['article']
        concept_title = title or body.splitlines()[0].strip('# ').strip()
        concept_path = add_or_update_concept(concept_title, [domain], tags, [f"raw/articles/{body_path_name}.md"])
        # Create placeholder entity if we can detect a named-entity; simplified here
        tokens = concept_title.split()
        if len(tokens) > 1:
            entity_title = tokens[0] + ' ' + tokens[1]
            add_or_update_entity(entity_title, [domain], tags[:2] or ['entity'])
        update_index_with_concept(concept_title)
        append_log(f"URL ingest: {url} -> {concept_title} (domain={domain}, tags={tags})")
        print(f"Ingested {url} into {concept_title}")
    elif cmd == 'note':
        # Discord note ingestion (raw note)
        if len(sys.argv) >= 3:
            note = sys.argv[2]
        else:
            note = ''
        domain = None
        if '--domain' in sys.argv:
            idx = sys.argv.index('--domain')
            domain = sys.argv[idx+1] if idx+1 < len(sys.argv) else None
            
        if not domain:
            print("Error: --domain is required. Please specify it (e.g., --domain personal-knowledge).")
            sys.exit(1)
            
        if '--tags' in sys.argv:
            idx = sys.argv.index('--tags')
            tags = sys.argv[idx+1].split(',') if idx+1 < len(sys.argv) else None
        if not tags:
            # naive guess from content
            tags = best_guess_tags(domain, note) or ['article']
        # Save raw note
        transcripts = os.path.join(wiki_root, 'raw', 'transcripts')
        os.makedirs(transcripts, exist_ok=True)
        import datetime
        fname = f"discord-note-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        with open(os.path.join(transcripts, fname), 'w') as f:
            f.write(note)
        concept_title = note.splitlines()[0] if note else 'Discord Note'
        concept_path = add_or_update_concept(concept_title, [domain], tags, [f"raw/transcripts/{fname}"])
        # Create placeholder entity
        if len(concept_title.split()) > 1:
            entity_title = concept_title.split()[0] + ' ' + concept_title.split()[1]
            add_or_update_entity(entity_title, [domain], tags[:2] or ['entity'])
        update_index_with_concept(concept_title)
        append_log(f"Discord note ingest: {concept_title} (domain={domain}, tags={tags})")
        print(f"Ingested Discord note as concept: {concept_title}")
    else:
        print("Unknown command. Use 'url' or 'note'.")

if __name__ == '__main__':
    main()
