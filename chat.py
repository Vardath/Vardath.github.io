"""Simple local command-line chat test."""
import sys
from pathlib import Path
from deepthort_local import LocalModelClient

if __name__=='__main__':
    prompt=' '.join(sys.argv[1:]).strip() or 'Write a short Python function to compute Fibonacci numbers.'
    here=Path(__file__).resolve().parent
    client=LocalModelClient(here/'state'/'sessions.sqlite3')
    print(client.chat('local-test',prompt))
