import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automation.general_agent import process_general_directive

queries = [
    'open leetcode',
    'submit daily streak on leetcode',
    'go to my account gagansokhal-coder',
    'close the microsoft edge',
    'unlock my laptop'
]

for q in queries:
    ok, reply = process_general_directive(q)
    print(f"Query: '{q}' -> Handled: {ok} | Reply: '{reply}'")

