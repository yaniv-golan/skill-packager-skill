#!/usr/bin/env python3
"""Helper script to copy remaining skill files."""
import shutil
import os

src = '/Users/yaniv/Documents/code/proof-engine/proof-engine/skills/proof-engine'
dst = '/Users/yaniv/Documents/code/skill-packager-skill/skill-packager-workspace/iteration-1/eval-1-universal-repo/with_skill/outputs/proof-engine-skill/proof-engine/skills/proof-engine'

# Template reference files (overwrite abbreviated versions)
refs = [
    'template-absence.md', 'template-compound.md', 'template-date-age.md',
    'template-numeric.md', 'template-pure-math.md', 'template-qualitative.md',
]
for f in refs:
    shutil.copy2(os.path.join(src, 'references', f), os.path.join(dst, 'references', f))
    print(f'  Copied references/{f}')

# Script files
scripts = [
    '__init__.py', 'ast_helpers.py', 'computations.py', 'extract_values.py',
    'fetch.py', 'latex_text.py', 'proof_types.py', 'smart_extract.py',
    'source_credibility.py', 'validate_proof.py', 'verify_citations.py',
]
for f in scripts:
    shutil.copy2(os.path.join(src, 'scripts', f), os.path.join(dst, 'scripts', f))
    print(f'  Copied scripts/{f}')

# Data files
data_files = [
    'academic_domains.json', 'government_tlds.json', 'major_news.json',
    'reference_domains.json', 'unreliable_domains.json',
]
for f in data_files:
    shutil.copy2(os.path.join(src, 'scripts', 'data', f), os.path.join(dst, 'scripts', 'data', f))
    print(f'  Copied scripts/data/{f}')

# Evals
shutil.copy2(os.path.join(src, 'evals', 'evals.json'), os.path.join(dst, 'evals', 'evals.json'))
print('  Copied evals/evals.json')

print('All files copied successfully')
