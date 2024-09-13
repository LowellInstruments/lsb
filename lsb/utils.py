def pt(s):
    return print(s)


def cmd_dir_ans_to_dict(ls, ext='*', match=True):
    if ls is None:
        return {}

    if b'ERR' in ls:
        return b'ERR'

    if type(ext) is str:
        ext = ext.encode()

    files, idx = {}, 0

    # ls: b'\n\r.\t\t\t0\n\r\n\r..\t\t\t0\n\r\n\rMAT.cfg\t\t\t189\n\r\x04\n\r'
    ls = ls.replace(b'System Volume Information\t\t\t0\n\r', b'')
    ls = ls.split()

    while idx < len(ls):
        name = ls[idx]
        if name in [b'\x04']:
            break

        names_to_omit = (
            b'.',
            b'..',
        )

        if type(ext) is str:
            ext = ext.encode()
        # wild-card case
        if ext == b'*' and name not in names_to_omit:
            files[name.decode()] = int(ls[idx + 1])
        # specific extension case
        elif name.endswith(ext) == match and name not in names_to_omit:
            files[name.decode()] = int(ls[idx + 1])
        idx += 2
    return files
