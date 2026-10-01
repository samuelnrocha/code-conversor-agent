import os
import re
import stat
from pathlib import Path
from typing import Dict, Set, List

class SecretVault:
    """
    Cofre Seguro de Credenciais e Mascarador de Segredos.
    Garante que senhas, tokens e connection strings:
    1. Sejam isolados em cofre volátil e nunca commitados no repositório.
    2. Sejam salvos apenas em .env com permissão estrita 0600 (apenas leitura do dono).
    3. Tenham um .env.example público apenas com valores mascarados/vazios.
    4. Sejam estritamente ignorados pelo .gitignore.
    5. Sejam mascarados dinamicamente nos logs da aplicação e dos agentes.
    """

    def __init__(self):
        self._secrets: Dict[str, str] = {} # key -> value
        self._secret_values: Set[str] = set()

    def register_secret(self, key: str, value: str):
        if value and len(value.strip()) > 3:
            self._secrets[key] = value.strip()
            self._secret_values.add(value.strip())

    def get_secrets(self) -> Dict[str, str]:
        return dict(self._secrets)

    def mask_text(self, text: str) -> str:
        """Substitui qualquer ocorrência de segredo registrado por [REDACTED]"""
        if not text:
            return text

        masked = text
        for key, val in self._secrets.items():
            if val and len(val) >= 4:
                masked = masked.replace(val, f"[REDACTED_{key.upper()}]")

        # Regras genéricas para tokens e senhas caso passem despercebidos
        masked = re.sub(r'(?i)(password|pwd|secret|token)\s*[:=]\s*([^\s;,\'"]+)', r'\1=[REDACTED]', masked)
        masked = re.sub(r'sec_live_[a-zA-Z0-9]{16,}', '[REDACTED_API_KEY]', masked)
        masked = re.sub(r'whsec_[a-zA-Z0-9]{12,}', '[REDACTED_WEBHOOK_SECRET]', masked)
        return masked

    def provision_environment_files(self, target_dir: Path):
        """Gera .env seguro e .env.example público e atualiza .gitignore"""
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        env_path = target_dir / ".env"
        example_path = target_dir / ".env.example"
        gitignore_path = target_dir / ".gitignore"

        # 1. Escrever .env real com permissões restritas (0600)
        env_lines = [
            "# ========================================================================",
            "# ARQUIVO DE CONFIGURAÇÃO DE AMBIENTE - SEGREDO RESTRITO",
            "# NUNCA COMETA ESTE ARQUIVO NO CONTROLE DE VERSÃO (GIT)",
            "# ========================================================================",
            ""
        ]
        example_lines = [
            "# ========================================================================",
            "# EXEMPLO DE CONFIGURAÇÃO DE AMBIENTE (SEGURO PARA COMMIT)",
            "# Copie para .env e preencha as credenciais reais no servidor seguro.",
            "# ========================================================================",
            ""
        ]

        for k, v in sorted(self._secrets.items()):
            env_lines.append(f"{k}={v}")
            example_lines.append(f"{k}=your_{k.lower()}_here")

        with open(env_path, "w", encoding="utf-8") as f:
            f.write("\n".join(env_lines) + "\n")

        # Aplicar chmod 0600 (leitura e escrita apenas pelo proprietário)
        try:
            os.chmod(env_path, stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            pass

        with open(example_path, "w", encoding="utf-8") as f:
            f.write("\n".join(example_lines) + "\n")

        # 2. Assegurar que .gitignore bloqueia arquivos de credenciais
        secret_patterns = [
            ".env",
            ".env.local",
            ".env.*.local",
            "*.secret",
            "*.key",
            "*.pem",
            "appsettings.Development.json",
            "appsettings.Production.json"
        ]

        existing_ignores = ""
        if gitignore_path.exists():
            with open(gitignore_path, "r", encoding="utf-8") as f:
                existing_ignores = f.read()

        missing = [p for p in secret_patterns if p not in existing_ignores]
        if missing:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write("\n# Security: Secrets & Environment Credentials\n")
                for p in missing:
                    f.write(f"{p}\n")
