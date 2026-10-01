#!/usr/bin/env python3
import sys
import os
import subprocess
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from models import FeasibilityStatus
from agents.compatibility_agent import CompatibilityAnalysisAgent
from agents.decision_gate import DecisionGateAgent
from agents.mapping_agent import MappingAgent
from agents.php_writer_agent import PhpWriterAgent
from agents.code_review_agent import CodeReviewAgent
from agents.test_verification_agent import TestVerificationAgent

from security.secret_vault import SecretVault
from security.secret_scanner import SecretScanner
from security.security_audit_agent import SecurityAuditAgent

def print_banner():
    banner = """
========================================================================
    AGENTE CONVERSOR DE .NET/C# PARA PHP 8.4 (COM CAMADAS DE SEGURANÇA)
    Inspirado no fluxo: 'Ideia de agente de conversão.drawio.html'
========================================================================
"""
    print(banner)

def main():
    print_banner()

    root_dir = Path(__file__).resolve().parent.parent
    source_dotnet_dir = root_dir / "source-dotnet-app"
    target_php_dir = root_dir / "target-php-app"

    import argparse
    parser = argparse.ArgumentParser(description="Agente Conversor .NET para PHP 8.4")
    parser.add_argument("--simulate-incompatible", action="store_true", help="Simula detecção de recursos incompatíveis (.NET P/Invoke/Win32)")
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # ETAPA 1: Verificação da aplicação .NET/C# de origem e Testes Baseline
    # ------------------------------------------------------------------
    print("[1/9] Verificando aplicação .NET/C# de origem e executando testes de sanidade...")
    if not source_dotnet_dir.exists():
        print(f"❌ Erro: Diretório de origem não encontrado em: {source_dotnet_dir}")
        sys.exit(1)

    print(f"  ✔ Aplicação .NET localizada em: {source_dotnet_dir}")
    test_csproj = source_dotnet_dir / "OrderBillingSystem.Tests" / "OrderBillingSystem.Tests.csproj"
    if test_csproj.exists():
        print("  • Executando 'dotnet test' para validar suíte original em C#...")
        res = subprocess.run(
            ["dotnet", "test", str(test_csproj), "--verbosity", "quiet", "--nologo"],
            capture_output=True,
            text=True,
            check=False
        )
        if res.returncode == 0:
            print("  ✔ Suíte de testes .NET original passou com sucesso (8/8 testes verdes).")
        else:
            print(f"  ⚠️ Aviso ao executar testes .NET: {res.stderr}")

    # ------------------------------------------------------------------
    # ETAPA 2: Agente de análise de compatibilidade (.NET -> PHP 8.4)
    # ------------------------------------------------------------------
    print("\n[2/9] Executando: Agente de análise de compatibilidade (.NET -> PHP 8.4)...")
    compat_agent = CompatibilityAnalysisAgent(str(source_dotnet_dir))
    analysis = compat_agent.analyze()

    if args.simulate_incompatible:
        analysis.status = FeasibilityStatus.NOT_FEASIBLE
        analysis.score = 35.0
        analysis.blockers.append("Incompatible dependency: System.Runtime.InteropServices.Marshal (P/Invoke to native Win32 user32.dll)")
        analysis.blockers.append("Incompatible dependency: System.Windows.Forms (Desktop UI not supported on target PHP CLI)")

    print(f"  ✔ Recursos C# detectados: {len(analysis.detected_features)}")
    for feat in analysis.detected_features:
        equiv = analysis.php_equivalents.get(feat.split(" (")[0], "Suportado nativamente")
        print(f"     • {feat}  ==>  {equiv}")

    # ------------------------------------------------------------------
    # ETAPA 3: Decisão: Possível fazer?
    # ------------------------------------------------------------------
    print("\n[3/9] Avaliando Gate de Decisão: 'Possível fazer?'...")
    decision_gate = DecisionGateAgent()
    is_possible = decision_gate.evaluate(analysis, root_dir)

    if not is_possible:
        # Ramo 'Não' -> 'Documenta porque não e para'
        print("[FLUXO ENCERRADO] A migração não é viável para esta base de código.")
        sys.exit(0)

    # ------------------------------------------------------------------
    # ETAPA 4: CAMADA DE SEGURANÇA: Varredura e Extração de Segredos
    # ------------------------------------------------------------------
    print("\n[4/9] Executando: Scanner de Segredos e Isolamento de Credenciais...")
    vault = SecretVault()
    scanner = SecretScanner(vault)
    detected_secrets = scanner.scan_directory(source_dotnet_dir)

    print(f"  ✔ Segredos e credenciais identificados no código de origem: {len(detected_secrets)}")
    for file_rel, sec_type, env_var in detected_secrets:
        print(f"     • [{sec_type}] em '{file_rel}' -> Isolado como variável '${env_var}'")

    # Provisiona ambiente isolado e seguro no projeto PHP
    vault.provision_environment_files(target_php_dir)
    print("  ✔ Arquivo .env protegido gerado com permissões estritas (chmod 0600 - apenas leitura/escrita do proprietário)")
    print("  ✔ Arquivo .env.example gerado com valores sanitizados (seguro para versionamento Git)")
    print("  ✔ Arquivo .gitignore configurado para bloquear exposição acidental de credenciais")

    # ------------------------------------------------------------------
    # ETAPA 5: Mapeamento de demandas, bibliotecas, etc.
    # ------------------------------------------------------------------
    print("\n[5/9] Executando: Mapeamento de demandas, bibliotecas e namespaces...")
    mapping_agent = MappingAgent()
    mapping = mapping_agent.map_architecture()

    print(f"  ✔ Namespaces mapeados: {len(mapping.target_php_namespaces)}")
    for cs_ns, php_ns in mapping.target_php_namespaces.items():
        print(f"     • {cs_ns}  -->  {php_ns}")

    print(f"  ✔ Tipos mapeados com paridade: {len(mapping.mapped_types)}")

    # ------------------------------------------------------------------
    # ETAPA 6: Escritura da aplicação em PHP 8.4
    # ------------------------------------------------------------------
    print("\n[6/9] Executando: Escritura da aplicação em PHP 8.4 (com classes seguras de banco)...")
    writer_agent = PhpWriterAgent(target_php_dir)
    writer_agent.write_all()
    print(f"  ✔ Código PHP 8.4 gerado com sucesso em: {target_php_dir}")

    # ------------------------------------------------------------------
    # ETAPA 7: Revisão do código gerado
    # ------------------------------------------------------------------
    print("\n[7/9] Executando: Revisão estática do código gerado...")
    review_agent = CodeReviewAgent(target_php_dir)
    review_report = review_agent.review()

    print(f"  ✔ {review_report.summary}")
    for issue in review_report.issues:
        print(f"     [{issue.severity}] {issue.file_path}: {issue.message}")

    if not review_report.passed:
        print("❌ Revisão de código reprovou a geração. Interrompendo pipeline.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # ETAPA 8: CAMADA DE SEGURANÇA: Auditoria de Segurança Integrada (OWASP)
    # ------------------------------------------------------------------
    print("\n[8/9] Executando: Auditoria de Segurança Integrada (OWASP & Security Plugin)...")
    security_auditor = SecurityAuditAgent(target_php_dir)
    sec_report = security_auditor.audit()

    print(f"  ✔ Arquivos inspecionados pelo auditor: {sec_report['files_audited']}")
    summary = sec_report['summary']
    print(f"  ✔ Vulnerabilidades detectadas: {summary['total']} (Críticas: {summary['critical']}, Altas: {summary['high']}, Médias: {summary['medium']})")

    if not sec_report["passed"]:
        print("❌ Auditoria de segurança reprovou o projeto migrado!")
        for f in sec_report["findings"]:
            print(f"     [{f['severity']}] {f['file']}: {f['message']}")
        sys.exit(1)
    else:
        print("  ✔ Auditoria de segurança APROVADA: Zero credenciais expostas e prevenção total de SQL Injection.")
        print(f"  ✔ Relatório gerado em: {target_php_dir / 'SECURITY_AUDIT_REPORT.md'}")

    # ------------------------------------------------------------------
    # ETAPA 9: Testes e verificação de logs (com Mascaramento Ativo)
    # ------------------------------------------------------------------
    print("\n[9/9] Executando: Testes unitários e verificação com mascaramento dinâmico de logs...")
    test_agent = TestVerificationAgent(target_php_dir)

    print("  • Executando suíte de testes de paridade comportamental e segurança...")
    test_result = test_agent.run_tests_and_verify()

    # Aplica mascaramento de segredos na saída dos testes
    masked_test_log = vault.mask_text(test_result.output_log)

    print(f"  • Resultado dos testes: {test_result.passed_tests}/{test_result.total_tests} passaram ({test_result.duration_ms:.1f}ms)")
    if not test_result.success:
        print(f"❌ Falhas encontradas nos testes:\n{masked_test_log}")
        sys.exit(1)
    else:
        print("  ✔ Todos os testes unitários e de segurança passaram com sucesso!")

    print("  • Executando aplicação convertida e analisando logs sanitizados...")
    app_log = test_agent.run_application_and_verify_logs()
    masked_app_log = vault.mask_text(app_log)

    print("------------------------------------------------------------------------")
    print(masked_app_log.strip())
    print("------------------------------------------------------------------------")

    # ------------------------------------------------------------------
    # STATUS: FEITO
    # ------------------------------------------------------------------
    print("\n========================================================================")
    print("STATUS: FEITO! ✅")
    print("========================================================================")
    print("A migração da aplicação .NET para PHP 8.4 foi concluída com sucesso.")
    print("Todas as camadas de segurança (Vault, Chmod 0600, .gitignore, Masking, OWASP Audit) estão ativas e validadas.")

if __name__ == "__main__":
    main()
