import sys
from pathlib import Path

import pydantic
import pytest
import yaml

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[4]
        / "collections"
        / "ansible_collections"
        / "osac"
        / "service"
        / "plugins"
        / "filter"
    ),
)

from find_template_roles import (
    Metadata,
    ProtobufAnyValue,
    ProtobufType,
    TemplateParameter,
    TemplateParameterDefinition,
    TemplateTypeEnum,
    TypeMapping,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_definition(**overrides) -> TemplateParameterDefinition:
    defaults = {"name": "test_param", "title": "Test", "description": "A test param"}
    defaults.update(overrides)
    return TemplateParameterDefinition(**defaults)


def _discover_osac_yamls(roles_dir: Path) -> list[Path]:
    yamls: list[Path] = []
    for ext in ("yaml", "yml"):
        yamls.extend(roles_dir.glob(f"*/meta/osac.{ext}"))
    return sorted(yamls)


# ---------------------------------------------------------------------------
# TestTemplateParameterDefinitionDefaults
# ---------------------------------------------------------------------------

class TestTemplateParameterDefinitionDefaults:

    @pytest.mark.parametrize(
        "value, expected_type",
        [
            ("hello", str),
            (42, int),
            (3.14, float),
            (True, bool),
        ],
        ids=["str", "int", "float", "bool"],
    )
    def test_scalar_defaults(self, value, expected_type):
        defn = _make_definition(default=value)
        assert defn.default == value
        assert isinstance(defn.default, expected_type)

    @pytest.mark.parametrize(
        "value, expected_type",
        [
            ([], list),
            (["a", "b"], list),
            ({}, dict),
            ({"key": "val"}, dict),
        ],
        ids=["empty_list", "non_empty_list", "empty_dict", "non_empty_dict"],
    )
    def test_collection_defaults(self, value, expected_type):
        defn = _make_definition(default=value)
        assert defn.default == value
        assert isinstance(defn.default, expected_type)

    def test_none_default(self):
        defn = _make_definition()
        assert defn.default is None

    def test_explicit_none_default(self):
        defn = _make_definition(default=None)
        assert defn.default is None


# ---------------------------------------------------------------------------
# TestTemplateParameterFromDefinition
# ---------------------------------------------------------------------------

class TestTemplateParameterFromDefinition:

    @pytest.mark.parametrize(
        "default_value, ansible_type, expected_proto_type",
        [
            ("hello", "string", ProtobufType.STRING),
            (42, "int", ProtobufType.INT),
            (3.14, "float", ProtobufType.FLOAT),
            (True, "bool", ProtobufType.BOOL),
            ([], "list", ProtobufType.ANY),
            ({"k": "v"}, "dict", ProtobufType.ANY),
        ],
        ids=["str", "int", "float", "bool", "list", "dict"],
    )
    def test_type_mapping_and_default(
        self, default_value, ansible_type, expected_proto_type
    ):
        defn = _make_definition(default=default_value, type=ansible_type)
        param = TemplateParameter.from_definition(defn)

        assert param.type == expected_proto_type
        assert param.default is not None
        assert param.default.type == expected_proto_type
        assert param.default.value == default_value

    def test_none_default_produces_none(self):
        defn = _make_definition(default=None, type="string")
        param = TemplateParameter.from_definition(defn)
        assert param.default is None

    def test_unknown_ansible_type_falls_back_to_string(self):
        defn = _make_definition(type="unknown_type")
        param = TemplateParameter.from_definition(defn)
        assert param.type == ProtobufType.STRING


# ---------------------------------------------------------------------------
# TestProtobufAnyValueSerialization
# ---------------------------------------------------------------------------

class TestProtobufAnyValueSerialization:

    @pytest.mark.parametrize(
        "default_value, expected_type_url",
        [
            ("hello", ProtobufType.STRING),
            (42, ProtobufType.INT),
            (3.14, ProtobufType.FLOAT),
            (True, ProtobufType.BOOL),
            ([], ProtobufType.ANY),
            ({"k": "v"}, ProtobufType.ANY),
        ],
        ids=["str", "int", "float", "bool", "list", "dict"],
    )
    def test_serialization_produces_correct_type_url(
        self, default_value, expected_type_url
    ):
        defn = _make_definition(default=default_value)
        param = TemplateParameter.from_definition(defn)
        dumped = param.default.model_dump(by_alias=True)

        assert "@type" in dumped
        assert dumped["@type"] == expected_type_url
        assert dumped["value"] == default_value

    def test_serialization_uses_alias_not_field_name(self):
        pav = ProtobufAnyValue(type=ProtobufType.STRING, value="test")
        dumped = pav.model_dump(by_alias=True)
        assert "@type" in dumped
        assert "type" not in dumped


# ---------------------------------------------------------------------------
# TestRealTemplateMetadata
# ---------------------------------------------------------------------------

class TestRealTemplateMetadata:

    def test_roles_dir_exists(self, roles_dir):
        assert roles_dir.exists(), f"Template roles directory not found: {roles_dir}"

    def test_at_least_one_osac_yaml_found(self, roles_dir):
        yamls = _discover_osac_yamls(roles_dir)
        assert len(yamls) > 0, "No osac.yaml files found in template roles"

    @pytest.fixture(params=None)
    def osac_yaml_path(self, roles_dir, request):
        return request.param

    @staticmethod
    def _load_yaml(path: Path) -> dict:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_all_osac_yamls_parse(self, roles_dir):
        yamls = _discover_osac_yamls(roles_dir)
        failures = []
        for path in yamls:
            try:
                data = self._load_yaml(path)
                Metadata.model_validate(data)
            except Exception as e:
                failures.append(f"{path.parent.parent.name}: {e}")
        assert not failures, "Metadata parsing failures:\n" + "\n".join(failures)

    def test_all_parameters_produce_valid_template_parameters(self, roles_dir):
        yamls = _discover_osac_yamls(roles_dir)
        failures = []
        for path in yamls:
            data = self._load_yaml(path)
            metadata = Metadata.model_validate(data)
            for param_def in metadata.parameters:
                try:
                    TemplateParameter.from_definition(param_def)
                except Exception as e:
                    failures.append(
                        f"{path.parent.parent.name}/{param_def.name}: {e}"
                    )
        assert not failures, (
            "TemplateParameter conversion failures:\n" + "\n".join(failures)
        )

    def test_all_defaults_produce_valid_protobuf_serialization(self, roles_dir):
        yamls = _discover_osac_yamls(roles_dir)
        failures = []
        for path in yamls:
            data = self._load_yaml(path)
            metadata = Metadata.model_validate(data)
            for param_def in metadata.parameters:
                param = TemplateParameter.from_definition(param_def)
                if param.default is not None:
                    try:
                        dumped = param.default.model_dump(by_alias=True)
                        assert "@type" in dumped
                        assert "value" in dumped
                    except Exception as e:
                        failures.append(
                            f"{path.parent.parent.name}/{param_def.name}: {e}"
                        )
        assert not failures, (
            "ProtobufAnyValue serialization failures:\n" + "\n".join(failures)
        )


# ---------------------------------------------------------------------------
# TestTypeMappingCompleteness
# ---------------------------------------------------------------------------

class TestTypeMappingCompleteness:

    @pytest.mark.parametrize(
        "key",
        ["str", "string", "list", "dict", "bool", "int", "float", "path", "json", "bytes"],
    )
    def test_ansible_string_keys_present(self, key):
        assert key in TypeMapping

    @pytest.mark.parametrize(
        "python_type",
        [str, int, float, bool, list, dict],
    )
    def test_python_builtin_types_present(self, python_type):
        assert python_type in TypeMapping


# ---------------------------------------------------------------------------
# TestMetadataTemplateTypes
# ---------------------------------------------------------------------------

class TestMetadataTemplateTypes:

    @pytest.mark.parametrize(
        "role_name, expected_type",
        [
            ("ocp_small", TemplateTypeEnum.cluster),
            ("ocp_virt_vm", TemplateTypeEnum.compute_instance),
            ("cudn_net", TemplateTypeEnum.network),
            ("bm_host_agent_provisioning", TemplateTypeEnum.bare_metal_instance),
            ("vast_storage", TemplateTypeEnum.storage_provider),
        ],
    )
    def test_template_type_parsed_correctly(
        self, roles_dir, role_name, expected_type
    ):
        meta_path = None
        for ext in ("yaml", "yml"):
            candidate = roles_dir / role_name / "meta" / f"osac.{ext}"
            if candidate.exists():
                meta_path = candidate
                break
        assert meta_path is not None, f"osac.yaml not found for role {role_name}"

        with meta_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        metadata = Metadata.model_validate(data)
        assert metadata.template_type == expected_type

    def test_compute_instance_has_spec_defaults(self, roles_dir):
        meta_path = roles_dir / "ocp_virt_vm" / "meta" / "osac.yaml"
        with meta_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        metadata = Metadata.model_validate(data)
        assert metadata.spec_defaults is not None
        assert metadata.spec_defaults.boot_disk is not None
        assert metadata.spec_defaults.image is not None

    def test_network_has_capabilities(self, roles_dir):
        meta_path = roles_dir / "cudn_net" / "meta" / "osac.yaml"
        with meta_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        metadata = Metadata.model_validate(data)
        assert metadata.capabilities is not None
        assert metadata.capabilities.supports_ipv4 is True

    def test_cluster_with_parameters(self, roles_dir):
        meta_path = roles_dir / "ocp_4_20_ai_maas" / "meta" / "osac.yaml"
        with meta_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        metadata = Metadata.model_validate(data)
        assert len(metadata.parameters) > 0
        param_names = [p.name for p in metadata.parameters]
        assert "hardware_profiles" in param_names
        assert "external_models" in param_names

    def test_validate_default_rejects_unsupported_type(self):
        with pytest.raises(pydantic.ValidationError):
            TemplateParameter(
                name="bad",
                title="Bad",
                description="Bad param",
                default=object(),
            )
