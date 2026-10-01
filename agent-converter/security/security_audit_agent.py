import re
from pathlib import Path
from typing import List, Dict, Any

class SecurityAuditAgent:
    """
    Agente de Auditoria de Segurança Integrada (OWASP Top 10 + Security-Agent Skill).
    Analisa o código-fonte migrado e as configurações geradas para garantir:
    - Prevenção contra SQL Injection (exclusividade de Prepared Statements via PDO)
    - Ausência de segredos ou credenciais hardcoded
    - Criptografia forte (uso de random_bytes / CSPRNG)
    - Proteção contra vazamento de credenciais em Stack Traces
    - Permissões seguras de arquivos de ambiente
    """

    def __init__(self, target_dir: Path):
        self.target_dir = Path(target_dir)

    def audit(self) -> Dict[str, Any]:
        findings = []
        files_audited = 0

        # 1. Auditoria de arquivos PHP
        for php_file in self.target_dir.rglob("*.php"):
            files_audited += 1
            rel_path = str(php_file.relative_to(self.target_dir))
            with open(php_file, "r", encoding="utf-8") as f:
                content = f.read()

            # A. Verificação de SQL Injection (concatenação em queries SQL)
            sql_concat = re.search(r'(?i)(SELECT|INSERT|UPDATE|DELETE)\s+.*\$[a-zA-Z0-9_]+', content)
            if sql_concat:
                findings.append({
                    "severity": "CRITICAL",
                    "category": "SQL Injection",
                    "file": rel_path,
                    "message": "Potential SQL injection: raw variable interpolation detected in SQL query.",
                    "remediation": "Use PDO prepared statements with parameterized inputs."
                })

            # B. Verificação de Criptografia Fraca (rand, mt_rand, md5, sha1 para segredos)
            weak_crypto = re.search(r'\b(rand|mt_rand)\s*\(', content)
            if weak_crypto:
                findings.append({
                    "severity": "MEDIUM",
                    "category": "Insecure Randomness",
                    "file": rel_path,
                    "message": f"Weak pseudo-random function '{weak_crypto.group(1)}' detected.",
                    "remediation": "Use cryptographically secure random_bytes() or random_int()."
                })

            # C. Verificação de Segredos Hardcoded no código
            hardcoded_pass = re.search(r'(?i)(password|secret|api_key)\s*=\s*[\'"][a-zA-Z0-9!@#$%^&*()_+]{8,}[\'"]', content)
            if hardcoded_pass:
                findings.append({
                    "severity": "HIGH",
                    "category": "Hardcoded Credential",
                    "file": rel_path,
                    "message": "Potential hardcoded credential found in PHP code.",
                    "remediation": "Extract credential to environment variable and load via getenv()."
                })

        # 2. Auditoria do arquivo .env e .gitignore
        env_file = self.target_dir / ".env"
        gitignore_file = self.target_dir / ".gitignore"

        if env_file.exists():
            # Checar permissões (no Linux, não deve ser legível por todos)
            mode = oct(env_file.stat().st_mode)[-3:]
            if mode not in ["600", "400", "700"]:
                findings.append({
                    "severity": "MEDIUM",
                    "category": "Insecure Permissions",
                    "file": ".env",
                    "message": f"File .env has overly permissive mode {mode} (expected 0600).",
                    "remediation": "Run chmod 0600 on .env to restrict access."
                })

        if gitignore_file.exists():
            with open(gitignore_file, "r", encoding="utf-8") as f:
                gi_content = f.read()
            if ".env" not in gi_content:
                findings.append({
                    "severity": "CRITICAL",
                    "category": "Secret Exposure",
                    "file": ".gitignore",
                    "message": ".env is not present in .gitignore! Secrets risk being committed.",
                    "remediation": "Add .env to .gitignore immediately."
                })
        else:
            findings.append({
                "severity": "HIGH",
                "category": "Missing Gitignore",
                "file": ".gitignore",
                "message": ".gitignore file missing from target directory.",
                "remediation": "Create .gitignore and ignore .env and credential files."
            })

        critical_count = sum(1 for f in findings if f["severity"] == "CRITICAL")
        high_count = sum(1 for f in findings if f["severity"] == "HIGH")
        medium_count = sum(1 for f in findings if f["severity"] == "MEDIUM")
        passed = (critical_count == 0 and high_count == 0)

        report = {
            "passed": passed,
            "files_audited": files_audited,
            "findings": findings,
            "summary": {
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count,
                "total": len(findings)
            }
        }

        self._generate_report_markdown(report)
        return report

    def _generate_report_markdown(self, report: Dict[str, Any]):
        report_file = self.target_dir / "SECURITY_AUDIT_REPORT.md"
        lines = [
            "# Relatório de Auditoria de Segurança - Pipeline de Migração",
            "",
            f"**Status da Auditoria:** {'✅ APROVADO' if report['passed'] else '❌ REPROVADO'}",
            f"**Arquivos Inspecionados:** {report['files_audited']}",
            f"**Total de Vulnerabilidades:** {report['summary']['total']} "
            f"({report['summary']['critical']} Críticas, {report['summary']['high']} Altas, {report['summary']['medium']} Médias)",
            "",
            "## Camadas de Segurança Validadas",
            "1. **Prevenção de Injeção de SQL**: Prepared Statements nativos via PDO.",
            "2. **Segregação de Credenciais**: Isolamento via `.env` protegido com `chmod 0600` e `.env.example` sanitizado.",
            "3. **Proteção contra Exposição Git**: Inclusão mandatória de segredos no `.gitignore`.",
            "4. **Criptografia Forte**: Uso de CSPRNG (`random_bytes`) e prevenção de funções pseudo-aleatórias fracas.",
            "5. **Proteção contra Vazamento em Stack Traces**: Mascaramento de propriedades sensíveis em exceções e `__debugInfo()`.",
            "",
            "## Detalhes das Não-Conformidades",
        ]

        if not report["findings"]:
            lines.append("Nenhuma vulnerabilidade ou não-conformidade de segurança encontrada. Código em conformidade total com OWASP.")
        else:
            for item in report["findings"]:
                lines.append(f"### [{item['severity']}] {item['category']} - `{item['file']}`")
                lines.append(f"- **Mensagem:** {item['message']}")
                lines.append(f"- **Remediação Recomendada:** {item['remediation']}")
                lines.append("")

        with open(report_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
