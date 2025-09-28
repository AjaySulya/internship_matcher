from typing import List

def list_to_str(lst: List[str]) -> str:
    return ",".join(lst)

def str_to_list(s: str) -> List[str]:
    if s:
        return [item.strip() for item in s.split(",") if item.strip()]
    return []
