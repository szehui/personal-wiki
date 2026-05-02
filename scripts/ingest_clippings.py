#!/usr/bin/env python3
import os
import glob
import subprocess
import sys

wiki_root = os.path.expanduser('~/wiki')
clippings_dir = os.path.join(wiki_root, 'Clippings')

def main():
    if not os.path.exists(clippings_dir):
        print(f"Clippings directory not found: {clippings_dir}")
        sys.exit(0)
        
    md_files = glob.glob(os.path.join(clippings_dir, '**', '*.md'), recursive=True)
    if not md_files:
        print("No clippings found to ingest.")
        sys.exit(0)
        
    print(f"Found {len(md_files)} clippings to ingest.")
    
    script_path = os.path.join(wiki_root, 'scripts', 'ingest.py')
    
    success_count = 0
    fail_count = 0
    
    for md_file in md_files:
        print(f"\n--- Ingesting {os.path.basename(md_file)} ---")
        try:
            # We run the ingestion script in a subprocess
            result = subprocess.run(
                [sys.executable, script_path, 'clip', md_file],
                cwd=wiki_root,
                check=True,
                text=True,
                capture_output=True
            )
            print(result.stdout)
            success_count += 1
        except subprocess.CalledProcessError as e:
            print(f"Failed to ingest {md_file}:")
            print(e.stderr)
            fail_count += 1
            
    print(f"\n--- Clippings Ingestion Complete ---")
    print(f"Successfully processed: {success_count}")
    print(f"Failed: {fail_count}")

if __name__ == '__main__':
    main()
