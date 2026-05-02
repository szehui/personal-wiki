#!/usr/bin/env python3
import sys
import os
import json
import hashlib
import datetime
from urllib.parse import urlparse
import urllib.request
import urllib.error
import subprocess
import ast

def read_frontmatter(md_path):
    try:
        with open(md_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return {}, ''
    if not lines or lines[0].strip() != '---':
        return {}, "".join(lines)
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            end = i
            break
    if end is None:
        return {}, "".join(lines)
    header = lines[1:end]
    body = "".join(lines[end+1:])
    fm = {}
    for l in header:
        if ':' in l:
            k, v = l.split(':', 1)
            fm[k.strip()] = v.strip()
    return fm, body

def write_frontmatter(md_path, fm, body=None):
    with open(md_path, 'w') as f:
        f.write('---\n')
        for k, v in fm.items():
            if k in ('summary', 'summary_text'):
                continue
            # Basic serialization for lists/strings in fm
            f.write(f"{k}: {v}\n")
        if 'summary_text' in fm:
            f.write("summary_text: |\n")
            for s in fm['summary_text'].splitlines():
                f.write(f"  {s}\n")
        f.write('---\n')
        if body:
            f.write(body)

def update_summary(md_path, summary_text):
    fm, body = read_frontmatter(md_path)
    fm['summary_text'] = summary_text
    write_frontmatter(md_path, fm, body=body)

def summarize_sources(concept_md_path):
    fm, _ = read_frontmatter(concept_md_path)
    sources = fm.get('sources', '')
    srcs = []
    if isinstance(sources, str):
        try:
            srcs = ast.literal_eval(sources)
        except Exception:
            # Fallback simple parse if array formatting is loose
            s = sources.strip('[]')
            srcs = [x.strip() for x in s.split(',')] if s else []
    elif isinstance(sources, list):
        srcs = sources

    aggregated = []
    for s in srcs:
        if isinstance(s, str) and (s.startswith('raw/articles/') or s.startswith('raw/transcripts/')):
            path = os.path.join(wiki_root, s)
            if os.path.exists(path):
                _, s_body = read_frontmatter(path)
                if s_body.strip():
                    aggregated.append(s_body.strip())
                    
    if not aggregated:
        return

    # Basic summarization: take the first 3 sentences of the combined raw bodies.
    # In a full LLM integration, this would call out to an LLM completion API.
    combined = " ".join(aggregated)
    import re
    sentences = [x.strip() for x in re.split(r'(?<=[.!?])\s+', combined) if x.strip()]
    summary_text = " ".join(sentences[:3])
    
    update_summary(concept_md_path, summary_text)

def sync_git(commit_message):
    """
    Adds, commits, and pushes changes to the git remote.
    """
    print("Syncing with git repository...")
    try:
        subprocess.run(['git', 'add', '-A'], cwd=wiki_root, check=True)
        res = subprocess.run(['git', 'commit', '-m', commit_message], cwd=wiki_root, capture_output=True, text=True)
        if res.returncode == 0:
            subprocess.run(['git', 'push'], cwd=wiki_root, check=True)
            print("Successfully synced to remote.")
        else:
            print("No changes to commit.")
    except Exception as e:
        print(f"Warning: Git sync failed. Ensure your remote is set up and push doesn't require interactive auth. Error: {e}")

def notify_discord(ingest_type, source, domain, tags, concept_title, touched_pages):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return
    
    description = (
        f"**Concept:** {concept_title}\n"
        f"**Domain:** {domain}\n"
        f"**Tags:** {', '.join(tags)}\n"
        f"**Source:** {source}\n\n"
        f"**Pages Touched ({len(touched_pages)}):**\n" + 
        "\n".join([f"- `{p}`" for p in touched_pages])
    )

    payload = {
        "embeds": [{
            "title": f"Wiki Ingest: {ingest_type}",
            "description": description,
            "color": 3447003 if ingest_type == "URL" else 10181046,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }]
    }

    req = urllib.request.Request(
        webhook_url, 
        data=json.dumps(payload).encode('utf-8'), 
        headers={'Content-Type': 'application/json', 'User-Agent': 'WikiBot/1.0'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            pass
    except Exception as e:
        print(f"Warning: Failed to post to Discord webhook: {e}")

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

def write_frontmatter_dict(path, fm, body=None):
    with open(path, 'w') as f:
        f.write('---\n')
        for k, v in fm.items():
            if k == 'summary_text':
                continue
            if isinstance(v, list):
                if k == 'sources':
                    # Need specific string formatting because literals won't have quotes inside the file
                    # actually let's just make it look like standard arrays for tags, sources
                    f.write(f"{k}: [{', '.join(v)}]\n")
                else:
                    f.write(f"{k}: [{', '.join(v)}]\n")
            else:
                f.write(f"{k}: {v}\n")
        if 'summary_text' in fm:
            f.write("summary_text: |\n")
            for s in fm['summary_text'].splitlines():
                f.write(f"  {s}\n")
        f.write('---\n')
        if body:
            f.write(body)

def append_log(entry):
    with open(log_md, 'a') as f:
        f.write(f"## {entry}\n")

def add_or_update_concept(concept_title, domains, tags, sources):
    slug = slugify(concept_title)
    p = os.path.join(concepts_dir, f"{slug}.md")
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    if not os.path.exists(p):
        fm = {
            'title': concept_title,
            'created': today,
            'updated': today,
            'type': 'concept',
            'domains': domains,
            'tags': tags,
            'sources': sources
        }
        write_frontmatter_dict(p, fm)
    return p

def add_or_update_entity(entity_title, domains, tags):
    slug = slugify(entity_title)
    p = os.path.join(entities_dir, f"{slug}.md")
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    if not os.path.exists(p):
        fm = {
            'title': entity_title,
            'created': today,
            'updated': today,
            'type': 'entity',
            'domains': domains,
            'tags': tags
        }
        write_frontmatter_dict(p, fm)
    return p

def best_guess_tags(domain, text):
    taxonomy = {
        'personal-knowledge': ['travel','bike','fitness','health','family','homelab'],
        'work-knowledge': ['contacts','companies','medical-knowledge','nemt-industry']
    }
    tags = taxonomy.get(domain, [])
    hits = []
    for t in tags:
        if t in text.lower():
            hits.append(t)
    return hits[:4]

def update_index_with_concept(concept_title):
    slug = slugify(concept_title)
    with open(index_md, 'r') as f:
        content = f.read()
    if f"[[{slug}|{concept_title}]]" not in content:
        with open(index_md, 'a') as f:
            f.write(f"- [[{slug}|{concept_title}]]\n")

def main():
    ensure_dirs()
    if len(sys.argv) < 2:
        print('Usage: ingest.py url|note --domain DOMAIN [--tags TAG1,TAG2] [--title "..." | --notes "..."]')
        sys.exit(1)
    
    cmd = sys.argv[1]
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
            
        if '--domain' in sys.argv:
            idx = sys.argv.index('--domain')
            domain = sys.argv[idx+1] if idx+1 < len(sys.argv) else None
            
        if not domain:
            print("Error: --domain is required. Please specify it (e.g., --domain personal-knowledge).")
            sys.exit(1)
            
        if '--tags' in sys.argv:
            idx = sys.argv.index('--tags')
            tags = sys.argv[idx+1].split(',') if idx+1 < len(sys.argv) else None
            
        if '--title' in sys.argv:
            idx = sys.argv.index('--title')
            title = sys.argv[idx+1] if idx+1 < len(sys.argv) else None
            
        body = web_extract(url)
        body_path_name = slugify(title or urlparse(url).path.split("/")[-1] or "article")
        body_path = os.path.join(raw_articles, f"{body_path_name}.md")
        
        with open(body_path, 'w') as f:
            f.write(body)
            
        sha = hashlib.sha256(body.encode('utf-8')).hexdigest()
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        write_frontmatter_dict(body_path, {'source_url': url, 'ingested': today, 'sha256': sha}, body=body)
        
        if not tags:
            tags = best_guess_tags(domain, body) or ['article']
            
        concept_title = title or body.splitlines()[0].strip('# ').strip()
        concept_path = add_or_update_concept(concept_title, [domain], tags, [f"raw/articles/{body_path_name}.md"])
        
        touched_pages = []
        touched_pages.append(os.path.relpath(body_path, wiki_root))
        touched_pages.append(os.path.relpath(concept_path, wiki_root))
        
        tokens = concept_title.split()
        if len(tokens) > 1:
            entity_title = tokens[0] + ' ' + tokens[1]
            entity_path = add_or_update_entity(entity_title, [domain], tags[:2] or ['entity'])
            touched_pages.append(os.path.relpath(entity_path, wiki_root))
            
        update_index_with_concept(concept_title)
        touched_pages.extend(['index.md', 'log.md'])
        
        summarize_sources(concept_path)
        
        append_log(f"URL ingest: {url} -> {concept_title} (domain={domain}, tags={tags})")
        print(f"Ingested {url} into {concept_title}")
        
        # Git and Discord
        iso_time = datetime.datetime.now().isoformat()
        num_pages = len(touched_pages)
        pages_summary = ", ".join(touched_pages)
        commit_message = (
            f"Ingested (URL): {concept_title}\n\n"
            f"Domain: {domain}\n"
            f"Tags: {', '.join(tags)}\n"
            f"Pages touched ({num_pages}):\n  - " + "\n  - ".join(touched_pages) + f"\n"
            f"Timestamp: {iso_time}"
        )
        
        sync_git(commit_message)
        notify_discord("URL", url, domain, tags, concept_title, touched_pages)
        
    elif cmd == 'note':
        if len(sys.argv) >= 3:
            note = sys.argv[2]
        else:
            note = ''
            
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
            tags = best_guess_tags(domain, note) or ['article']
            
        transcripts = os.path.join(wiki_root, 'raw', 'transcripts')
        os.makedirs(transcripts, exist_ok=True)
        fname = f"discord-note-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        note_path = os.path.join(transcripts, fname)
        
        with open(note_path, 'w') as f:
            f.write(note)
            
        concept_title = note.splitlines()[0][:50] if note else 'Discord Note'
        concept_path = add_or_update_concept(concept_title, [domain], tags, [f"raw/transcripts/{fname}"])
        
        touched_pages = []
        touched_pages.append(os.path.relpath(note_path, wiki_root))
        touched_pages.append(os.path.relpath(concept_path, wiki_root))
        
        if len(concept_title.split()) > 1:
            entity_title = concept_title.split()[0] + ' ' + concept_title.split()[1]
            entity_path = add_or_update_entity(entity_title, [domain], tags[:2] or ['entity'])
            touched_pages.append(os.path.relpath(entity_path, wiki_root))
            
        update_index_with_concept(concept_title)
        touched_pages.extend(['index.md', 'log.md'])
        
        summarize_sources(concept_path)
        
        append_log(f"Discord note ingest: {concept_title} (domain={domain}, tags={tags})")
        print(f"Ingested Discord note as concept: {concept_title}")
        
        # Git and Discord
        iso_time = datetime.datetime.now().isoformat()
        num_pages = len(touched_pages)
        commit_message = (
            f"Ingested (Note): {concept_title}\n\n"
            f"Domain: {domain}\n"
            f"Tags: {', '.join(tags)}\n"
            f"Pages touched ({num_pages}):\n  - " + "\n  - ".join(touched_pages) + f"\n"
            f"Timestamp: {iso_time}"
        )
        
        sync_git(commit_message)
        notify_discord("Note", "Discord text input", domain, tags, concept_title, touched_pages)
        
    else:
        print("Unknown command. Use 'url' or 'note'.")

if __name__ == '__main__':
    main()
