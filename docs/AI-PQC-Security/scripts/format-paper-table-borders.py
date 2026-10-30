"""Mechanical LaTeX table formatting only; cell contents remain unchanged."""
from pathlib import Path
import re

path = Path(__file__).resolve().parents[1] / 'docs/research/paper/main.tex'
text = path.read_text(encoding='utf-8')

def borders(match):
    block = match.group(0)
    specs = {
        'p{.13\\textwidth}p{.24\\textwidth}Y Y':'|p{.13\\textwidth}|p{.24\\textwidth}|Y|Y|',
        'Y Y':'|Y|Y|', 'lll':'|l|l|l|',
        'p{.15\\textwidth}p{.20\\textwidth}p{.20\\textwidth}Y':'|p{.15\\textwidth}|p{.20\\textwidth}|p{.20\\textwidth}|Y|',
        'llrrr':'|l|l|r|r|r|', 'lrrrr':'|l|r|r|r|r|',
        'llrrrr':'|l|l|r|r|r|r|', 'Yrrrr':'|Y|r|r|r|r|',
        'p{.22\\textwidth}p{.24\\textwidth}Y':'|p{.22\\textwidth}|p{.24\\textwidth}|Y|',
        'lrrr':'|l|r|r|r|', 'p{.25\\textwidth}Y':'|p{.25\\textwidth}|Y|'
    }
    for old,new in specs.items():
        block = block.replace('{'+old+'}', '{'+new+'}')
    block = block.replace(r'\toprule', r'\hline').replace(r'\midrule', r'\hline').replace(r'\bottomrule', r'\hline')
    block = re.sub(r'(?<!\\)\\\\(?!\\hline)', lambda _:r'\\\hline', block)
    block = block.replace(r'\multicolumn{5}{l}', r'\multicolumn{5}{|l|}')
    return block

text, count = re.subn(r'\\begin\{tabularx?\}.*?\\end\{tabularx?\}', borders, text, flags=re.S)
assert count == 12, count
path.write_text(text,encoding='utf-8')
print(f'Applied outer/column/row borders to {count} tables; no cell values changed.')
