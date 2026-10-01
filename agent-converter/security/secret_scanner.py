import re
import json
from pathlib import Path
from typing import Dict, List, Tuple
from security.secret_vault import SecretVault

class SecretScanner:
    """
    Scanner estático de segredos e credenciais em arquivos .NET/C#.
    Identifica connection strings, credenciais de banco, tokens de API e chaves privadas,
    extraindo-os com segurança para o SecretVault e impedindo vazamentos no código destino.
    """

    def __init__(self, vault: SecretVault):
        self.vault = vault

    def scan_directory(self, source_dir: Path) -> List[Tuple[str, str, str]]:
        """
        Varre o diretório de origem procurando por segredos.
        Retorna lista de (arquivo_relativo, tipo_segredo, chave_atribuida).
        """
        detections = []
        source_dir = Path(source_dir)

        # 1. Varredura em arquivos de configuração (.json, .config)
        for conf_file in source_dir.rglob("*.json"):
            if "bin" in conf_file.parts or "obj" in conf_file.parts:
                continue
            detections.extend(self._scan_json_config(conf_file, source_dir))

        # 2. Varredura em código C# (*.cs)
        for cs_file in source_dir.rglob("*.cs"):
            if "bin" in cs_file.parts or "obj" in cs_file.parts:
                continue
            detections.extend(self._scan_csharp_source(cs_file, source_dir))

        return detections

    def _scan_json_config(self, file_path: Path, base_dir: Path) -> List[Tuple[str, str, str]]:
        detections = []
        rel_path = str(file_path.relative_to(base_dir))

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Buscar ConnectionStrings
            if isinstance(data, dict):
                conn_strings = data.get("ConnectionStrings", {})
                for conn_name, conn_val in conn_strings.items():
                    if isinstance(conn_val, str):
                        self._parse_and_extract_connection_string(conn_val, detections, rel_path)

                # Buscar Payment / API keys
                for section, vals in data.items():
                    if isinstance(vals, dict):
                        for k, v in vals.items():
                            if isinstance(v, str) and any(kw in k.lower() for kw in ["key", "secret", "password", "token"]):
                                env_name = f"{section.upper()}_{k.upper()}"
                                self.vault.register_secret(env_name, v)
                                detections.append((rel_path, f"API Secret: {k}", env_name))
        except Exception:
            pass

        return detections

    def _scan_csharp_source(self, file_path: Path, base_dir: Path) -> List[Tuple[str, str, str]]:
        detections = []
        rel_path = str(file_path.relative_to(base_dir))

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Regex para connection strings em C#
        conn_matches = re.findall(r'(?i)"(Server=[^"]+;Password=[^"]+)"', content)
        for match in conn_matches:
            self._parse_and_extract_connection_string(match, detections, rel_path)

        # Regex para chaves literais no código
        token_matches = re.findall(r'(?i)(api[_-]?key|secret|token|password)\s*=\s*"([^"]{8,})"', content)
        for key_type, token_val in token_matches:
            if not any(token_val.startswith(p) for p in ["http://", "https://", "SKU-", "ORD-"]):
                env_key = f"APP_{key_type.upper()}"
                self.vault.register_secret(env_key, token_val)
                detections.append((rel_path, f"Hardcoded String: {key_type}", env_key))

        return detections

    def _parse_and_extract_connection_string(self, conn_str: str, detections: list, rel_path: str):
        # Server / Host
        host_m = re.search(r'(?i)(Server|Data Source|Host)\s*=\s*([^;]+)', conn_str)
        if host_m:
            self.vault.register_secret("DB_HOST", host_m.group(2))
            detections.append((rel_path, "Database Host", "DB_HOST"))

        # Database
        db_m = re.search(r'(?i)(Database|Initial Catalog)\s*=\s*([^;]+)', conn_str)
        if db_m:
            self.vault.register_secret("DB_NAME", db_m.group(2))
            detections.append((rel_path, "Database Name", "DB_NAME"))

        # User Id
        user_m = re.search(r'(?i)(User Id|Uid|User)\s*=\s*([^;]+)', conn_str)
        if user_m:
            self.vault.register_secret("DB_USER", user_m.group(2))
            detections.append((rel_path, "Database Username", "DB_USER"))

        # Password
        pass_m = re.search(r'(?i)(Password|Pwd)\s*=\s*([^;]+)', conn_str)
        if pass_m:
            self.vault.register_secret("DB_PASSWORD", pass_m.group(2))
            detections.append((rel_path, "Database Password", "DB_PASSWORD"))

        self.vault.register_secret("DB_PORT", "3306")
        self.vault.register_secret("DB_DRIVER", "mysql")
