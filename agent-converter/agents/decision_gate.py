import sys
from pathlib import Path
from models import CompatibilityAnalysis, FeasibilityStatus

class DecisionGateAgent:
    """
    Controlador de decisão ("Possível fazer?"):
    - Se Não: Documenta detalhadamente as razões técnicas em relatório formal e interrompe o pipeline.
    - Se Sim: Autoriza a continuidade do pipeline de migração.
    """

    def evaluate(self, analysis: CompatibilityAnalysis, output_dir: Path) -> bool:
        if analysis.status == FeasibilityStatus.NOT_FEASIBLE:
            self._document_why_not_and_stop(analysis, output_dir)
            return False

        print("\n[DECISION GATE] Avaliação de viabilidade: SIM (100% compatível)")
        print(f"[DECISION GATE] Índice de compatibilidade com PHP 8.4: {analysis.score:.1f}%")
        return True

    def _document_why_not_and_stop(self, analysis: CompatibilityAnalysis, output_dir: Path):
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "DOCUMENTO_INVIABILIDADE_MIGRACAO.md"

        content = f"""# Relatório de Inviabilidade Técnica de Migração (.NET -> PHP 8.4)

> **Decisão:** NÃO É POSSÍVEL REALIZAR A MIGRAÇÃO AUTOMÁTICA
> **Score de Compatibilidade:** {analysis.score:.1f}%

## Bloqueadores Críticos Detectados
"""
        for blocker in analysis.blockers:
            content += f"- ❌ **{blocker}**\n"

        content += "\n## Avisos e Limitações\n"
        for warning in analysis.warnings:
            content += f"- ⚠️ {warning}\n"

        content += "\n## Recomendações da Análise\n"
        for rec in analysis.recommendations:
            content += f"- 💡 {rec}\n"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"\n[DECISION GATE] ❌ MIGRAÇÃO INVIÁVEL. Relatório gerado em: {report_path}")
        print("[DECISION GATE] O pipeline foi interrompido conforme fluxo do desenho.")
