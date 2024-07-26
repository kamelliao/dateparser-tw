from typing import Dict, Tuple


def replace_spans(original_string: str, spans_dict: Dict[Tuple[int, int], str]) -> str:
    # Convert spans dictionary to a list of tuples and sort by start index descending
    sorted_spans = sorted(spans_dict.items(), key=lambda x: x[0][0], reverse=True)

    result = original_string

    for (start, end), replacement in sorted_spans:
        # Replace the substring within the specified span with the replacement value
        result = result[:start] + replacement + result[end:]

    return result
