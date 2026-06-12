"""String helper functions (equivalent to T4 helper methods)."""

import re


def to_camel_case(value: str) -> str:
    if not value:
        return value
    return value[0].lower() + value[1:]


def to_pascal_case(value: str) -> str:
    if not value:
        return value
    return value[0].upper() + value[1:]


def to_kebab_case(value: str) -> str:
    return re.sub(r"(?<!^)([A-Z])", r"-\1", value).lower()


def split_words(value: str) -> str:
    return re.sub(r"(?<!^)([A-Z])", r" \1", value)


def build_filter_ctor_params(filters: list[list[str]]) -> str:
    if not filters:
        return ""
    parts = ", ".join(f"{f[0]} {f[1]} = null" for f in filters)
    return f", {parts}"


def build_filter_controller_params(filters: list[list[str]]) -> str:
    if not filters:
        return ""
    parts = []
    for f in filters:
        binding = f[2] if len(f) > 2 else "FromQuery"
        parts.append(f"[{binding}] {f[0]} {f[1]}")
    return ", " + ", ".join(parts)


def build_filter_service_params(filters: list[list[str]]) -> str:
    if not filters:
        return ""
    return "".join(f"{f[0]} {f[1]}, " for f in filters)


def build_filter_call_args(filters: list[list[str]]) -> str:
    if not filters:
        return ""
    return "".join(f"request.{f[1]}, " for f in filters)


def build_filter_ctor_args(filters: list[list[str]]) -> str:
    if not filters:
        return ""
    parts = ", ".join(f[1] for f in filters)
    return f", {parts}"


def build_filter_predicate(filters: list[list[str]]) -> str:
    if not filters:
        return "true"
    clauses = []
    for f in filters:
        type_name = f[0]
        name = f[1]
        prop = to_pascal_case(name)
        if type_name.startswith("string"):
            clauses.append(f"({name} == null || e.{prop}.Contains({name}))")
        else:
            clauses.append(f"({name} == null || e.{prop} == {name})")
    return " && ".join(clauses)


def make_relative(base_dir: str, full_path: str) -> str:
    return full_path.replace(base_dir + "\\", "").replace(base_dir + "/", "")


# C# value types that need ? when not required
_VALUE_TYPES = frozenset({
    "bool", "byte", "sbyte", "char", "decimal", "double", "float",
    "int", "uint", "long", "ulong", "short", "ushort",
    "DateTime", "DateTimeOffset", "Guid", "DateOnly", "TimeOnly",
})


def nullable_type(type_name: str, is_required: bool) -> str:
    """Return the type string, appending ? for non-required value types.

    Reference types (string, object, etc.) are left as-is since they're
    already nullable in C# reference semantics.
    """
    if is_required:
        return type_name
    clean = type_name.rstrip("?")
    return clean + "?"
