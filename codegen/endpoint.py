"""Endpoint scaffold generator - adds a CQRS endpoint to an existing feature."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

from .appender import upsert_member
from .helpers import split_words, to_camel_case, to_kebab_case, to_pascal_case

TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "endpoint"


@dataclass
class EndpointConfig:
    feature_name: str
    feature_name_plural: str
    endpoint_name: str
    is_command: bool = True
    http_method: str = "POST"
    route: str = ""
    response_data_type: str = ""
    input_dto_name: str = ""
    input_properties: list[list[str]] = field(default_factory=list)
    input_params: list[list[str]] = field(default_factory=list)
    validation_rules: list[list[str]] = field(default_factory=list)
    dry_run: bool = False


def load_endpoint_config(config_path: str | Path) -> EndpointConfig:
    path = Path(config_path)
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return EndpointConfig(
        feature_name=data["feature_name"],
        feature_name_plural=data["feature_name_plural"],
        endpoint_name=data["endpoint_name"],
        is_command=data.get("is_command", True),
        http_method=data.get("http_method", "POST"),
        route=data.get("route", ""),
        response_data_type=data.get("response_data_type", ""),
        input_dto_name=data.get("input_dto_name", ""),
        input_properties=data.get("input_properties", []),
        input_params=data.get("input_params", []),
        validation_rules=data.get("validation_rules", []),
        dry_run=data.get("dry_run", False),
    )


def _is_primitive(type_name: str) -> bool:
    clean = type_name.rstrip("?")
    return clean in {
        "bool", "byte", "sbyte", "char", "decimal", "double", "float",
        "int", "uint", "long", "ulong", "short", "ushort", "string",
        "DateTime", "DateTimeOffset", "Guid",
    }


def _http_attribute(method: str) -> str:
    m = method.upper()
    if m == "GET":
        return "HttpGet"
    if m == "PUT":
        return "HttpPut"
    if m == "DELETE":
        return "HttpDelete"
    return "HttpPost"


def _route_attribute(route: str) -> str:
    if not route:
        return ""
    return f'("{route}")'


def _build_context(cfg: EndpointConfig) -> dict:
    is_multi_param = len(cfg.input_params) > 0
    generate_input_dto = not is_multi_param and len(cfg.input_properties) > 0
    input_dto_name = cfg.input_dto_name
    if generate_input_dto and not input_dto_name:
        input_dto_name = cfg.endpoint_name + "InputDto"

    # Input names
    if is_multi_param:
        input_names = [p[1] for p in cfg.input_params]
    elif generate_input_dto:
        input_names = ["model"]
    elif input_dto_name:
        input_names = ["id"]
    else:
        input_names = []

    use_case = "CommandUseCases" if cfg.is_command else "QueryUseCases"
    folder = "Commands" if cfg.is_command else "Queries"
    request_name = cfg.endpoint_name + ("Command" if cfg.is_command else "Query")
    handler_name = cfg.feature_name + ("CommandHandler" if cfg.is_command else "QueryHandler")
    service_interface_name = "I" + cfg.feature_name + ("CommandService" if cfg.is_command else "QueryService")
    service_class_name = cfg.feature_name + ("CommandService" if cfg.is_command else "QueryService")
    service_param_name = "_commandService" if cfg.is_command else "_queryService"
    service_method_name = cfg.endpoint_name + "Async"

    if cfg.response_data_type:
        tpos_result_type = "TPosResult<" + cfg.response_data_type + ">"
    else:
        tpos_result_type = "TPosResult"

    request_ctor_params = ""
    if is_multi_param:
        request_ctor_params = ", ".join(f"{p[0]} {p[1]}" for p in cfg.input_params)
    elif generate_input_dto:
        request_ctor_params = input_dto_name + " Value"
    elif input_dto_name:
        request_ctor_params = input_dto_name + " id"

    request_ctor_args = ", ".join(input_names)

    # Service params
    svc_parts: list[str] = []
    if is_multi_param:
        svc_parts.extend(f"{p[0]} {p[1]}" for p in cfg.input_params)
    elif generate_input_dto:
        svc_parts.append(input_dto_name + " model")
    elif input_dto_name:
        svc_parts.append(input_dto_name + " id")
    svc_parts.append("CancellationToken cancellationToken")
    service_params = ", ".join(svc_parts)

    # Controller params
    ctrl_parts: list[str] = []
    if is_multi_param:
        for p in cfg.input_params:
            binding = p[2] if len(p) > 2 and p[2] else ("FromQuery" if _is_primitive(p[0]) else "FromBody")
            ctrl_parts.append(f"[{binding}] {p[0]} {p[1]}")
    elif generate_input_dto:
        binding = "FromQuery" if cfg.http_method.upper() == "GET" else "FromBody"
        ctrl_parts.append(f"[{binding}] {input_dto_name} model")
    elif input_dto_name:
        ctrl_parts.append(f"[FromRoute] {input_dto_name} id")
    ctrl_parts.append("CancellationToken cancellationToken")
    controller_params = ", ".join(ctrl_parts)

    # Handler service call args
    handler_parts: list[str] = []
    if is_multi_param:
        handler_parts.extend(f"request.{p[1]}" for p in cfg.input_params)
    elif generate_input_dto:
        handler_parts.append("request.Value")
    elif input_dto_name:
        handler_parts.append("request.id")
    handler_parts.append("cancellationToken")
    handler_service_call_args = ", ".join(handler_parts)

    # Base type for service
    if cfg.is_command:
        base_type = f"MyErp6ApplicationWriteService<{cfg.feature_name}, long>"
        repository_type = f"I{cfg.feature_name}WriteRepository"
        mediator_param = "        IMediator _mediator,\n"
        base_args = "_mediator, _repository, _baseService"
    else:
        base_type = f"MyErp6ApplicationReadService<{cfg.feature_name}>"
        repository_type = f"IReadRepositoryAsync<{cfg.feature_name}>"
        mediator_param = ""
        base_args = "_repository, _baseService"

    def validator_target(name: str) -> str:
        if generate_input_dto:
            return f"x.Value.{to_pascal_case(name)}"
        return f"x.{name}"

    def validator_kind(kind: str) -> str:
        if kind == "Required":
            return "NotEmpty"
        if kind == "MaxLength":
            return "MaximumLength"
        return kind

    return {
        # Core names
        "feature_name": cfg.feature_name,
        "feature_name_plural": cfg.feature_name_plural,
        "endpoint_name": cfg.endpoint_name,
        "is_command": cfg.is_command,
        "http_method": cfg.http_method,
        "route": cfg.route,
        "response_data_type": cfg.response_data_type,
        "input_dto_name": input_dto_name,
        "input_properties": cfg.input_properties,
        "input_params": cfg.input_params,
        "validation_rules": cfg.validation_rules,
        # Derived
        "use_case": use_case,
        "folder": folder,
        "request_name": request_name,
        "handler_name": handler_name,
        "service_interface_name": service_interface_name,
        "service_class_name": service_class_name,
        "service_param_name": service_param_name,
        "service_method_name": service_method_name,
        "tpos_result_type": tpos_result_type,
        "request_ctor_params": request_ctor_params,
        "request_ctor_args": request_ctor_args,
        "service_params": service_params,
        "controller_params": controller_params,
        "handler_service_call_args": handler_service_call_args,
        "generate_input_dto": generate_input_dto,
        "is_multi_param": is_multi_param,
        # For handler/service new file
        "base_type": base_type,
        "repository_type": repository_type,
        "mediator_param": mediator_param,
        "base_args": base_args,
        "request_type_interface": f"ICommand<{tpos_result_type}>" if cfg.is_command else f"IRequest<{tpos_result_type}>",
        "handler_interface": f"IRequestHandler<{request_name}, {tpos_result_type}>",
        # Helpers
        "http_attribute": _http_attribute(cfg.http_method),
        "route_attribute": _route_attribute(cfg.route),
        "kebab_feature_route": to_kebab_case(cfg.feature_name_plural),
        "split_words": split_words,
        "to_pascal_case": to_pascal_case,
        "to_camel_case": to_camel_case,
        "validator_target": validator_target,
        "validator_kind": validator_kind,
    }


def _create_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        keep_trailing_newline=True,
        trim_blocks=False,
        lstrip_blocks=False,
    )
    env.filters["to_camel_case"] = to_camel_case
    env.filters["to_pascal_case"] = to_pascal_case
    env.filters["to_kebab_case"] = to_kebab_case
    env.filters["split_words"] = split_words
    return env


def generate_endpoint(
    cfg: EndpointConfig,
    solution_dir: str | Path,
    dry_run: bool | None = None,
) -> list[str]:
    if dry_run is None:
        dry_run = cfg.dry_run

    solution = Path(solution_dir)
    ctx = _build_context(cfg)
    env = _create_env()
    results: list[str] = []

    use_case = ctx["use_case"]
    folder = ctx["folder"]
    request_name = ctx["request_name"]
    handler_name = ctx["handler_name"]
    service_interface_name = ctx["service_interface_name"]
    service_class_name = ctx["service_class_name"]
    service_method_name = ctx["service_method_name"]
    endpoint_name = ctx["endpoint_name"]

    # 1. Request/Command/Query record (new file)
    tpl = env.get_template("request.cs.j2")
    content = tpl.render(ctx)
    req_path = solution / f"TMT.MyErp6.{use_case}" / cfg.feature_name_plural / folder / f"{request_name}.cs"
    results.append(upsert_member(req_path, request_name, content, "", None, solution, dry_run))

    # 2. Input DTO (new file, if needed)
    if ctx["generate_input_dto"]:
        tpl = env.get_template("dto.cs.j2")
        content = tpl.render(ctx)
        dto_path = solution / "TMT.MyErp6.Application.Contracts" / cfg.feature_name_plural / "Dtos" / f"{ctx['input_dto_name']}.cs"
        results.append(upsert_member(dto_path, ctx["input_dto_name"], content, "", None, solution, dry_run))

    # 3. Validator (new file, for commands only)
    if cfg.is_command:
        tpl = env.get_template("validator.cs.j2")
        content = tpl.render(ctx)
        val_path = solution / "TMT.MyErp6.Application" / cfg.feature_name_plural / "Validators" / f"{request_name}Validator.cs"
        results.append(upsert_member(val_path, f"class {request_name}Validator", content, "", None, solution, dry_run))

    # 4. Handler (append or create)
    handler_file = solution / f"TMT.MyErp6.{use_case}" / cfg.feature_name_plural / f"{handler_name}.cs"
    tpl_method = env.get_template("handler_method.cs.j2")
    method_content = tpl_method.render(ctx)

    if not handler_file.exists():
        tpl_new = env.get_template("handler_new.cs.j2")
        new_content = tpl_new.render(ctx)
    else:
        new_content = ""

    results.append(upsert_member(
        handler_file, service_method_name, new_content, method_content,
        ctx["handler_interface"] if not handler_file.exists() else None,
        solution, dry_run,
    ))

    # 5. Service interface (append or create)
    svc_iface_file = solution / "TMT.MyErp6.Application.Contracts" / cfg.feature_name_plural / f"{service_interface_name}.cs"
    tpl_iface = env.get_template("service_interface_method.cs.j2")
    iface_method = tpl_iface.render(ctx)

    if not svc_iface_file.exists():
        # Build full new interface file
        new_iface = (
            f"using MyErp6.Domain.Shared.TPosResult;\n"
            + (f"using MyErp6.Application.Contracts.{cfg.feature_name_plural}.Dtos;\n" if ctx["generate_input_dto"] else "")
            + f"\nnamespace MyErp6.Application.Contracts.{cfg.feature_name_plural}\n"
            + "{\n"
            + f"    public interface {service_interface_name}\n"
            + "    {\n"
            + iface_method
            + "    }\n"
            + "}\n"
        )
    else:
        new_iface = ""

    results.append(upsert_member(
        svc_iface_file, service_method_name, new_iface, iface_method,
        None, solution, dry_run,
    ))

    # 6. Service class (append or create)
    svc_file = solution / "TMT.MyErp6.Application" / cfg.feature_name_plural / "Services" / f"{service_class_name}.cs"
    tpl_svc = env.get_template("service_method.cs.j2")
    svc_method = tpl_svc.render(ctx)

    if not svc_file.exists():
        tpl_new_svc = env.get_template("service_new.cs.j2")
        new_svc = tpl_new_svc.render(ctx)
    else:
        new_svc = ""

    results.append(upsert_member(
        svc_file, service_method_name, new_svc, svc_method,
        None, solution, dry_run,
    ))

    # 7. Controller (append or create)
    ctrl_file = solution / "TMT.MyERP6.HttpApi.Public.Host" / "PublicControllers" / f"{cfg.feature_name}Controller.cs"
    tpl_ctrl = env.get_template("controller_action.cs.j2")
    ctrl_action = tpl_ctrl.render(ctx)

    if not ctrl_file.exists():
        tpl_new_ctrl = env.get_template("controller_new.cs.j2")
        new_ctrl = tpl_new_ctrl.render(ctx)
    else:
        new_ctrl = ""

    results.append(upsert_member(
        ctrl_file, endpoint_name + "Async", new_ctrl, ctrl_action,
        None, solution, dry_run,
    ))

    return results


def generate_di_checklist(cfg: EndpointConfig) -> str:
    svc_interface = "I" + cfg.feature_name + ("CommandService" if cfg.is_command else "QueryService")
    svc_class = cfg.feature_name + ("CommandService" if cfg.is_command else "QueryService")
    lines = [
        f"  - Ensure {svc_interface} -> {svc_class} is registered.",
    ]
    if cfg.is_command:
        lines.append("  - Ensure validators are discovered by AddValidatorsFromAssembly.")
    return "\n".join(lines)
