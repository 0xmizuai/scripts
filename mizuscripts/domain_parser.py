#!/usr/bin/python3

import pathlib
import json
import re

ROOT_DIR = pathlib.Path(__file__).parent.resolve()


def flatten(xss):
    return [x for xs in xss for x in xs]


def clean_line(line: str):
    if line.find(':') != -1:
        line = line.split(":")[1].strip()
        return line if len(line) > 0 else None
    elif line.find('=') != -1:
        line = line.split("=")[1].strip()
        return line if len(line) > 0 else None
    else:
        return line


def parse_line(line: str | None) -> list[str]:
    if line is None or isinstance(line, str) == False:
        return []
    result = []
    try:
        parsed = json.loads(line)
        if isinstance(line, str):
            result = [parsed]
        elif isinstance(parsed, list):
            result = parsed
    except ValueError as e:
        if line.find(",") != -1:
            result = line.split(",")
        elif line.find("/") != -1:
            result = line.split("/")
        else:
            result = [line]
    return list(filter(lambda x: isinstance(x, str) and len(x) > 0, result))


def parse_domain(domain: str):
    domain = domain.strip().strip("[]'\"")
    if matched := re.compile("^(.*)_\\((.*)\\)$").match(domain):
        domain = matched.group(1) if len(matched.group(1)) > len(
            matched.group(2)) else matched.group(2)
    elif "knowledge_domain" in domain or "knowledge domain" in domain:
        return None
    elif len(domain) > 50:
        return None
    return domain.strip() if len(domain) > 0 else None


def load_domains(filePath: str):
    domains = []
    with open(filePath) as f:
        for line in f:
            for item in parse_line(clean_line(line)):
                for iitem in parse_line(item):
                    # iterate two levels to ensure all nested domains are extracted
                    domains += parse_line(iitem)
    cleaned = list(map(lambda x: parse_domain(x), domains))
    return list(set(filter(lambda x: x is not None and len(x.strip()) > 0, cleaned)))


def main():
    domains = load_domains(pathlib.PurePath(ROOT_DIR, "../data/domains"))
    print(domains)
    print("total domains: ", len(domains))
    open(pathlib.PurePath(ROOT_DIR, "../data/cleaned"),
         'w').write("\n".join(str(i) for i in domains))


if __name__ == '__main__':
    main()
