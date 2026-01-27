"""
OpenAPI Spec Fixing Utilities for Skydio API

This module contains functions to fix and clean up the Skydio OpenAPI specification
to make it compatible with various code generators like openapi-python-client.

Usage:
    from fix_openapi_spec import fix_openapi_spec

    fixed_spec = fix_openapi_spec(openapi_spec)
"""

import copy


def clean_ref_objects(obj):
    """
    Recursively clean up OpenAPI spec by removing extra properties from $ref objects.
    """
    if isinstance(obj, dict):
        if "$ref" in obj:
            return {"$ref": obj["$ref"]}
        else:
            return {key: clean_ref_objects(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [clean_ref_objects(item) for item in obj]
    else:
        return obj


def strip_json_schema_meta_properties(obj):
    """
    Recursively strip JSON Schema meta-properties that confuse code generators.
    """
    meta_properties = {"$id", "$schema"}

    if isinstance(obj, dict):
        return {
            key: strip_json_schema_meta_properties(value)
            for key, value in obj.items()
            if key not in meta_properties
        }
    elif isinstance(obj, list):
        return [strip_json_schema_meta_properties(item) for item in obj]
    else:
        return obj


def fix_file_type(obj):
    """
    Recursively fix non-standard "type": "file" by converting to "type": "string"
    with "format": "binary".
    """
    if isinstance(obj, dict):
        if obj.get("type") == "file":
            new_obj = {k: v for k, v in obj.items() if k != "type"}
            new_obj["type"] = "string"
            new_obj["format"] = "binary"
            return {key: fix_file_type(value) for key, value in new_obj.items()}
        else:
            return {key: fix_file_type(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [fix_file_type(item) for item in obj]
    else:
        return obj


def fix_invalid_const(obj):
    """
    Recursively fix invalid 'const' values where const is a list.

    In JSON Schema, 'const' must be a single value. If it's a list,
    convert it to 'enum' instead.
    """
    if isinstance(obj, dict):
        if "const" in obj and isinstance(obj["const"], list):
            # Convert const (list) to enum
            new_obj = {k: v for k, v in obj.items() if k != "const"}
            new_obj["enum"] = obj["const"]
            return {key: fix_invalid_const(value) for key, value in new_obj.items()}
        else:
            return {key: fix_invalid_const(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [fix_invalid_const(item) for item in obj]
    else:
        return obj


def fix_array_with_enum(obj):
    """
    Recursively fix arrays that have 'enum' at the array level.

    In JSON Schema, if you have type: array with enum, the enum should be
    on the items, not on the array itself. This fixes schemas like:
    {type: array, enum: [...], items: {type: string}}
    to:
    {type: array, items: {type: string, enum: [...]}}
    """
    if isinstance(obj, dict):
        # Check if this is an array with enum at the wrong level
        if (
            obj.get("type") == "array"
            and "enum" in obj
            and "items" in obj
            and isinstance(obj["enum"], list)
        ):
            # Move enum to items
            new_obj = {k: v for k, v in obj.items() if k != "enum"}
            items = new_obj.get("items", {})
            if isinstance(items, dict):
                items = dict(items)  # Copy
                items["enum"] = obj["enum"]
                new_obj["items"] = items
            return {key: fix_array_with_enum(value) for key, value in new_obj.items()}
        else:
            return {key: fix_array_with_enum(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [fix_array_with_enum(item) for item in obj]
    else:
        return obj


def rename_dotted_schema_names(openapi_spec):
    """
    Rename schema names containing dots to use underscores instead.

    Schema names with dots (e.g., "flight_deck.ReturnSettings") cause issues
    with code generation. This function renames them and updates all $ref
    references throughout the spec.
    """
    if "components" not in openapi_spec or "schemas" not in openapi_spec["components"]:
        return openapi_spec

    schemas = openapi_spec["components"]["schemas"]

    # Build a mapping of old names to new names
    rename_map = {}
    new_names_set = set()

    # First pass: determine all new names to avoid collisions
    for old_name in list(schemas.keys()):
        if "." in old_name:
            base_new_name = old_name.replace(".", "_")
            new_name = base_new_name

            # Handle collisions
            suffix = 2
            while new_name in schemas or new_name in new_names_set:
                new_name = f"{base_new_name}{suffix}"
                suffix += 1

            rename_map[old_name] = new_name
            new_names_set.add(new_name)
            print(f"  Renaming schema: {old_name} -> {new_name}")

    if not rename_map:
        return openapi_spec

    # Rename schemas in components/schemas
    new_schemas = {}
    for name, schema in schemas.items():
        new_name = rename_map.get(name, name)
        new_schemas[new_name] = schema
    openapi_spec["components"]["schemas"] = new_schemas

    # Update all $ref references throughout the spec
    def update_refs(obj):
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref = obj["$ref"]
                # Check if this ref points to a renamed schema
                for old_name, new_name in rename_map.items():
                    old_ref = f"#/components/schemas/{old_name}"
                    new_ref = f"#/components/schemas/{new_name}"
                    if ref == old_ref:
                        obj = {"$ref": new_ref}
                        break
                return obj
            else:
                return {key: update_refs(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [update_refs(item) for item in obj]
        else:
            return obj

    return update_refs(openapi_spec)


def strip_inline_schema_titles(openapi_spec):
    """
    Strip 'title' properties from inline schemas to prevent openapi-python-client
    from generating duplicate model names.

    openapi-python-client creates model names from titles, and when the same
    titled schema appears at multiple paths, it creates duplicates.
    By stripping titles from inline schemas (keeping only top-level component schemas),
    we avoid this issue.
    """

    def strip_titles(obj):
        """Recursively strip title from inline object schemas"""
        if isinstance(obj, dict):
            # If this has a title and looks like an object schema, remove the title
            if (
                "title" in obj
                and "$ref" not in obj
                and (
                    obj.get("type") == "object"
                    or "properties" in obj
                    or "oneOf" in obj
                    or "anyOf" in obj
                    or "allOf" in obj
                )
            ):
                # Remove title and continue processing nested content
                return {
                    key: strip_titles(value)
                    for key, value in obj.items()
                    if key != "title"
                }
            else:
                return {key: strip_titles(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [strip_titles(item) for item in obj]
        else:
            return obj

    # Process the entire spec
    result = {}
    for key, value in openapi_spec.items():
        if key == "components":
            result["components"] = {}
            for comp_key, comp_value in value.items():
                if comp_key == "schemas":
                    # For top-level schemas, keep their title but strip from nested content
                    processed_schemas = {}
                    for schema_name, schema_def in comp_value.items():
                        if isinstance(schema_def, dict):
                            processed_schema = {}
                            for prop_key, prop_value in schema_def.items():
                                if prop_key == "title":
                                    # Keep top-level schema title
                                    processed_schema[prop_key] = prop_value
                                else:
                                    # Strip titles from nested content
                                    processed_schema[prop_key] = strip_titles(
                                        prop_value
                                    )
                            processed_schemas[schema_name] = processed_schema
                        else:
                            processed_schemas[schema_name] = schema_def
                    result["components"]["schemas"] = processed_schemas
                else:
                    result["components"][comp_key] = strip_titles(comp_value)
        else:
            result[key] = strip_titles(value)

    return result


def fix_action_args_schema(openapi_spec):
    """
    Fix the skills.ActionArgs schema to create a clean, flat structure.

    The original schema has deeply nested recursive structures that confuse
    code generators. This function:
    1. Extracts the full oneOf from a nested level (which has all action types)
    2. Creates separate schemas for each action type wrapper
    3. Creates a clean ActionArgs schema with $refs to all action wrappers
    4. Creates Action and SequenceActionArgs schemas with proper $refs
    """
    if "components" not in openapi_spec or "schemas" not in openapi_spec["components"]:
        return openapi_spec

    schemas = openapi_spec["components"]["schemas"]

    # Check if skills.ActionArgs exists (may have been renamed to skills_ActionArgs)
    action_args_key = None
    for key in ["skills.ActionArgs", "skills_ActionArgs"]:
        if key in schemas:
            action_args_key = key
            break

    if action_args_key is None:
        print("  skills.ActionArgs not found, skipping fix")
        return openapi_spec

    action_args_schema = schemas[action_args_key]
    # Determine the naming convention (dotted or underscored)
    use_dots = "." in action_args_key
    sep = "." if use_dots else "_"

    # Find the full oneOf by traversing into the nested structure
    def find_full_oneof(obj, depth=0):
        """Recursively find a oneOf array that has more than just sequence"""
        if isinstance(obj, dict):
            if "oneOf" in obj and isinstance(obj["oneOf"], list):
                oneof = obj["oneOf"]
                if len(oneof) > 1:
                    return oneof
            for value in obj.values():
                result = find_full_oneof(value, depth + 1)
                if result:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = find_full_oneof(item, depth + 1)
                if result:
                    return result
        return None

    full_oneof = find_full_oneof(action_args_schema)

    if not full_oneof:
        print("  Could not find full oneOf in skills.ActionArgs, skipping fix")
        return openapi_spec

    print(f"  Found full oneOf with {len(full_oneof)} action types")

    # Schema names
    action_args_name = f"skills{sep}ActionArgs"
    action_name = f"skills{sep}Action"
    sequence_args_name = f"skills{sep}SequenceActionArgs"

    # Extract each action type and create separate wrapper schemas
    new_oneof_refs = []
    for option in full_oneof:
        props = option.get("properties", {})
        # Find the action-specific property (not isSkippable)
        action_prop_name = None
        action_prop_value = None
        for prop_name, prop_value in props.items():
            if prop_name != "isSkippable":
                action_prop_name = prop_name
                action_prop_value = prop_value
                break

        if not action_prop_name:
            continue

        # Create a wrapper schema name
        wrapper_name = (
            f"skills{sep}ActionArgs{action_prop_name[0].upper()}{action_prop_name[1:]}"
        )

        # Handle sequence specially - it needs recursive reference
        if action_prop_name == "sequence":
            # Create SequenceActionArgs schema
            if (
                isinstance(action_prop_value, dict)
                and "properties" in action_prop_value
            ):
                seq_schema = copy.deepcopy(action_prop_value)
                # Replace the nested actions.items with $ref to Action
                if "actions" in seq_schema.get("properties", {}):
                    seq_schema["properties"]["actions"]["items"] = {
                        "$ref": f"#/components/schemas/{action_name}"
                    }
                schemas[sequence_args_name] = seq_schema
                print(f"  Created {sequence_args_name} schema")

            # Create wrapper that references SequenceActionArgs
            wrapper_schema = {
                "type": "object",
                "properties": {
                    "isSkippable": props.get("isSkippable", {"type": "boolean"}),
                    "sequence": {"$ref": f"#/components/schemas/{sequence_args_name}"},
                },
                "required": option.get("required", ["sequence"]),
            }
        else:
            # For other actions, the prop_value should already be a $ref or simple schema
            wrapper_schema = {
                "type": "object",
                "properties": {
                    "isSkippable": props.get("isSkippable", {"type": "boolean"}),
                    action_prop_name: action_prop_value,
                },
                "required": option.get("required", [action_prop_name]),
            }

        schemas[wrapper_name] = wrapper_schema
        new_oneof_refs.append({"$ref": f"#/components/schemas/{wrapper_name}"})

    # Create the new ActionArgs schema with refs to all wrappers
    new_action_args_schema = {
        "title": "Action Args",
        "description": "Typed arguments passed into the action to initialize it.",
        "oneOf": new_oneof_refs,
    }

    # Create the Action schema
    action_schema = {
        "title": "Action",
        "type": "object",
        "description": "A single operation done by the vehicle.",
        "properties": {
            "actionKey": {
                "type": "string",
                "description": "Unique identifier for the action",
            },
            "args": {"$ref": f"#/components/schemas/{action_args_name}"},
        },
        "required": ["actionKey", "args"],
    }

    # Update the schemas
    if action_args_key != action_args_name:
        del schemas[action_args_key]
    schemas[action_args_name] = new_action_args_schema
    schemas[action_name] = action_schema

    print(f"  Created {action_name} schema")
    print(
        f"  Updated {action_args_name} schema with {len(new_oneof_refs)} action type refs"
    )

    return openapi_spec


def fix_openapi_spec(openapi_spec):
    """
    Apply all fixes to the OpenAPI specification.

    This is the main entry point that applies all necessary fixes
    to make the Skydio OpenAPI spec compatible with code generators.

    Args:
        openapi_spec: The raw OpenAPI specification dict

    Returns:
        The fixed OpenAPI specification dict
    """
    # Clean up the spec
    print("Cleaning up OpenAPI spec...")
    openapi_spec = clean_ref_objects(openapi_spec)
    openapi_spec = strip_json_schema_meta_properties(openapi_spec)
    openapi_spec = fix_file_type(openapi_spec)
    openapi_spec = fix_invalid_const(openapi_spec)
    openapi_spec = fix_array_with_enum(openapi_spec)

    # Apply additional fixes for better code generation
    print("Applying schema fixes...")
    openapi_spec = rename_dotted_schema_names(openapi_spec)
    openapi_spec = strip_inline_schema_titles(openapi_spec)
    openapi_spec = fix_action_args_schema(openapi_spec)

    return openapi_spec
