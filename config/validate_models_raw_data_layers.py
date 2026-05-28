#!/usr/bin/env python3

import ast
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODELS_RAW_DATA_FILE = REPO_ROOT / "config" / "models_raw_data.json"
HELPERS_DIR = REPO_ROOT / "helpers"

LAYER_HELPER_FUNCTIONS = {
    "fetch_coastlines": "Coastlines",
    "fetch_static_polygons": "StaticPolygons",
    "fetch_rotations": "Rotations",
    "fetch_COBs": "COBs",
    "fetch_continental_polygons": "ContinentalPolygons",
}


def _str_constant(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _extract_zip_basename(path_expression):
    path = _str_constant(path_expression)

    if path is None and isinstance(path_expression, ast.JoinedStr):
        path = "".join(
            value.value
            for value in path_expression.values
            if isinstance(value, ast.Constant) and isinstance(value.value, str)
        )

    if not path or not path.endswith(".zip"):
        return None

    return path.rsplit("/", 1)[-1][:-4]


def _get_model_config(model_name, all_models):
    visited = set()
    current_name = model_name

    while isinstance(all_models.get(current_name), str):
        if current_name in visited:
            return None
        visited.add(current_name)
        target = all_models[current_name]
        current_name = target[1:] if target.startswith("@") else target

    model_cfg = all_models.get(current_name)
    if isinstance(model_cfg, dict):
        return model_cfg
    return None


def _collect_layers_from_helper(helper_file):
    tree = ast.parse(helper_file.read_text(encoding="utf-8"))
    layers = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_name = None
            if isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                func_name = node.func.id

            if func_name in {"zip_files", "zip_folder"}:
                layer = None
                if len(node.args) > 2:
                    layer = _str_constant(node.args[2])
                if layer is None and len(node.args) > 1:
                    layer = _extract_zip_basename(node.args[1])
                if layer:
                    layers.add(layer)
            elif func_name == "zip_files_ex":
                if len(node.args) > 2:
                    layer = _str_constant(node.args[2])
                    if layer:
                        layers.add(layer)
            elif func_name == "fetch_and_zip_files":
                if len(node.args) > 2:
                    layer = _str_constant(node.args[2])
                    if layer:
                        layers.add(layer)
            elif func_name in LAYER_HELPER_FUNCTIONS:
                layers.add(LAYER_HELPER_FUNCTIONS[func_name])
        elif isinstance(node, ast.With):
            for item in node.items:
                context_expr = item.context_expr
                if not isinstance(context_expr, ast.Call):
                    continue

                zipfile_call = context_expr.func
                if isinstance(zipfile_call, ast.Attribute):
                    func_name = zipfile_call.attr
                elif isinstance(zipfile_call, ast.Name):
                    func_name = zipfile_call.id
                else:
                    func_name = None

                if func_name != "ZipFile" or len(context_expr.args) == 0:
                    continue

                layer = _extract_zip_basename(context_expr.args[0])
                if layer:
                    layers.add(layer)

    layers.discard("Rotations")
    return sorted(layers)


def main():
    with MODELS_RAW_DATA_FILE.open(encoding="utf-8") as f:
        all_models = json.load(f)

    helper_files = sorted(HELPERS_DIR.glob("collect_*.py"))
    helper_model_names = {
        helper_file.stem[len("collect_") :] for helper_file in helper_files
    }

    issues = []

    for model_name, model_cfg in all_models.items():
        if not isinstance(model_cfg, dict) or "Layers" not in model_cfg:
            continue
        if model_name == "vars":
            continue
        if model_name not in helper_model_names:
            issues.append(f"{model_name}: missing helper script collect_{model_name}.py")

    for helper_file in helper_files:
        helper_model_name = helper_file.stem[len("collect_") :]
        model_cfg = _get_model_config(helper_model_name, all_models)

        if model_cfg is None or "Layers" not in model_cfg:
            continue

        expected_layers = _collect_layers_from_helper(helper_file)
        actual_layers = sorted(model_cfg["Layers"].keys())

        if expected_layers != actual_layers:
            missing_layers = sorted(set(expected_layers) - set(actual_layers))
            extra_layers = sorted(set(actual_layers) - set(expected_layers))
            issue = (
                f"{helper_model_name}: expected={expected_layers}, "
                f"actual={actual_layers}"
            )
            if missing_layers:
                issue += f", missing={missing_layers}"
            if extra_layers:
                issue += f", extra={extra_layers}"
            issues.append(issue)

    if issues:
        print("Layer validation failed:")
        for issue in issues:
            print(f"- {issue}")
        raise SystemExit(1)

    print("Layer validation passed.")


if __name__ == "__main__":
    main()
