import sys

with open('app.py', 'r') as f:
    content = f.read()

# We want to replace the database layer and download functions
# Find where the database functions start
start_idx = content.find('# ============ DATABASE ============')
end_idx = content.find('# All countries for TikTok')

header = content[:start_idx]
footer = content[end_idx:]

new_db_code = """# ============ DATABASE & MEDIA ============
from db import init_db, save_search, get_search_history, get_search_results
import os

"""

with open('app.py', 'w') as f:
    f.write(header + new_db_code + footer)
