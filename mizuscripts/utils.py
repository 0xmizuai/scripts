def chunk(content: str, length: int, buffer: int):
    res = []
    start = 0
    end = length
    while end < len(content):
        res.append(content[start:end])
        start = end - buffer
        end += length
    res.append(content[start:end])
    return res
