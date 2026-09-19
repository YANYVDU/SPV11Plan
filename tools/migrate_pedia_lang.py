import os

V10 = r"d:/Git/CIV5/dyy/Super-Power-Remaking-of-World-Order/Super Power - Remaking of World Order (v 7)"
V11 = r"d:/Git/CIV5/dyy/V11/Super-Power-Remaking-of-World-Order/Super Power - Remaking of World Order (v 7)"
files = ["TextInfos_zh_CN.xml", "TextInfos_zh_Hant_HK.xml", "TextInfos_en_US.xml"]

def has_bom(path):
    with open(path, 'rb') as fh:
        return fh.read(3) == b'\xef\xbb\xbf'

def read_lines(path):
    enc = 'utf-8-sig' if has_bom(path) else 'utf-8'
    with open(path, 'r', encoding=enc) as fh:
        return fh.readlines()

def write_lines(path, lines, bom):
    enc = 'utf-8-sig' if bom else 'utf-8'
    with open(path, 'w', encoding=enc, newline='') as fh:
        fh.writelines(lines)

for f in files:
    src = os.path.join(V10, 'Gameplay', 'XML', 'Localization', f)
    dst = os.path.join(V11, 'Gameplay', 'XML', 'Localization', f)

    src_lines = read_lines(src)
    start = next(i for i, l in enumerate(src_lines) if 'TXT_KEY_PEDIA_EXTRA_SP_UPDATE_LOG' in l)
    end = next(i for i, l in enumerate(src_lines) if l.strip().startswith('</Language_'))
    block = src_lines[start:end]

    dst_bom = has_bom(dst)
    dst_lines = read_lines(dst)
    dst_end = next(i for i, l in enumerate(dst_lines) if l.strip().startswith('</Language_'))
    new_lines = dst_lines[:dst_end] + block + dst_lines[dst_end:]
    write_lines(dst, new_lines, dst_bom)

    print(f"{f}: inserted {len(block)} lines, bom={dst_bom}")
