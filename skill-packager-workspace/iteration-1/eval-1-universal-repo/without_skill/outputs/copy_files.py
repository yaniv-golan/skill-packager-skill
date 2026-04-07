#!/usr/bin/env python3
"""Helper script to copy remaining skill files to the output repo."""
import shutil
import os

src = '/Users/yaniv/Documents/code/proof-engine/proof-engine/skills/proof-engine'
dst = '/Users/yaniv/Documents/code/skill-packager-skill/skill-packager-workspace/iteration-1/eval-1-universal-repo/without_skill/outputs/proof-engine-skill/skill'

files_to_copy = [
    # Python scripts (excluding those already written)
    'scripts/verify_citations.py',
    'scripts/computations.py',
    'scripts/source_credibility.py',
    'scripts/validate_proof.py',
    'scripts/fetch.py',
    'scripts/proof_types.py',
    'scripts/latex_text.py',
    'scripts/ast_helpers.py',
    # Data files
    'scripts/data/academic_domains.json',
    'scripts/data/government_tlds.json',
    'scripts/data/major_news.json',
    'scripts/data/reference_domains.json',
    'scripts/data/unreliable_domains.json',
    # Reference files
    'references/hardening-rules.md',
    'references/proof-templates.md',
    'references/output-specs.md',
    'references/self-critique-checklist.md',
    'references/advanced-patterns.md',
    'references/environment-and-sources.md',
    'references/template-absence.md',
    'references/template-compound.md',
    'references/template-date-age.md',
    'references/template-numeric.md',
    'references/template-pure-math.md',
    'references/template-qualitative.md',
    # Evals
    'evals/evals.json',
]

for f in files_to_copy:
    src_path = os.path.join(src, f)
    dst_path = os.path.join(dst, f)
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    shutil.copy2(src_path, dst_path)
    print(f'Copied {f}')

print('All files copied successfully!')
