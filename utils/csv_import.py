import csv
import io


def read_csv_rows_with_fallback(file_obj, encodings=None):
    """Decode CSV bytes using a fallback encoding chain and return DictReader + encoding."""
    if encodings is None:
        encodings = ['utf-8-sig', 'utf-8', 'gb18030', 'cp936', 'big5', 'latin-1']

    file_bytes = file_obj.read()
    for encoding in encodings:
        try:
            content = file_bytes.decode(encoding)
            reader = csv.DictReader(io.StringIO(content))
            return reader, encoding
        except UnicodeDecodeError:
            continue

    raise UnicodeDecodeError('unknown', b'', 0, 1, 'Unable to decode CSV with supported encodings')


def normalize_header(raw_header):
    header = (str(raw_header or '').strip().lower())
    for marker in ('(required)', '(optional)', '[required]', '[optional]'):
        header = header.replace(marker, '')
    header = header.strip().replace(' ', '_')
    return header


def normalize_headers_and_rows(headers, rows, aliases=None):
    aliases = aliases or {}
    normalized_headers = []
    for header in headers:
        base = normalize_header(header)
        normalized_headers.append(aliases.get(base, base))

    normalized_rows = []
    for row in rows:
        normalized_row = {}
        for original_header, normalized_header in zip(headers, normalized_headers):
            value = row.get(original_header)
            normalized_row[normalized_header] = '' if value is None else str(value).strip()
        normalized_rows.append(normalized_row)

    return normalized_headers, normalized_rows
