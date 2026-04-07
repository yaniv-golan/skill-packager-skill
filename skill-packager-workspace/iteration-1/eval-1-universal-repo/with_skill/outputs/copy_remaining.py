#!/usr/bin/env python3
"""Copy remaining skill files from source to output directory."""
import shutil
import os

src = '/Users/yaniv/Documents/code/proof-engine/proof-engine/skills/proof-engine'
dst = '/Users/yaniv/Documents/code/skill-packager-skill/skill-packager-workspace/iteration-1/eval-1-universal-repo/with_skill/outputs/proof-engine-skill/proof-engine/skills/proof-engine'

files_to_copy = [
    # Template reference files
    ('references/template-absence.md', 'references/template-absence.md'),
    ('references/template-compound.md', 'references/template-compound.md'),
    ('references/template-date-age.md', 'references/template-date-age.md'),
    ('references/template-numeric.md', 'references/template-numeric.md'),
    ('references/template-pure-math.md', 'references/template-pure-math.md'),
    ('references/template-qualitative.md', 'references/template-qualitative.md'),
    # Python scripts
    ('scripts/computations.py', 'scripts/computations.py'),
    ('scripts/extract_values.py', 'scripts/extract_values.py'),
    ('scripts/fetch.py', 'scripts/fetch.py'),
    ('scripts/latex_text.py', 'scripts/latex_text.py'),
    ('scripts/proof_types.py', 'scripts/proof_types.py'),
    ('scripts/smart_extract.py', 'scripts/smart_extract.py'),
    ('scripts/source_credibility.py', 'scripts/source_credibility.py'),
    ('scripts/validate_proof.py', 'scripts/validate_proof.py'),
    ('scripts/verify_citations.py', 'scripts/verify_citations.py'),
    # Data files
    ('scripts/data/academic_domains.json', 'scripts/data/academic_domains.json'),
    ('scripts/data/government_tlds.json', 'scripts/data/government_tlds.json'),
    ('scripts/data/major_news.json', 'scripts/data/major_news.json'),
    ('scripts/data/reference_domains.json', 'scripts/data/reference_domains.json'),
    ('scripts/data/unreliable_domains.json', 'scripts/data/unreliable_domains.json'),
    # Evals
    ('evals/evals.json', 'evals/evals.json'),
]

copied = 0
for src_rel, dst_rel in files_to_copy:
    src_path = os.path.join(src, src_rel)
    dst_path = os.path.join(dst, dst_rel)
    if os.path.exists(src_path):
        shutil.copy2(src_path, dst_path)
        copied += 1
        print(f'  Copied {src_rel}')
    else:
        print(f'  MISSING {src_rel}')

# Remove __pycache__ if it was copied
pycache = os.path.join(dst, 'scripts', '__pycache__')
if os.path.exists(pycache):
    shutil.rmtree(pycache)
    print('  Removed __pycache__')

print(f'\nDone: {copied} files copied')
