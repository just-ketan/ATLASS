"""Research extension engine tests."""

from pathlib import Path

from tests.conftest import make_sample_document

from atlasse_v2.baseline.baseline_generator import BaselineGenerator
from atlasse_v2.blueprint.blueprint_generator import BlueprintGenerator
from atlasse_v2.core.types import EvidenceLabel
from atlasse_v2.graph.semantic_graph import SemanticPaperGraph
from atlasse_v2.memory.research_memory import ResearchMemory
from atlasse_v2.reproduction.reproduction_engine import ReproductionEngine
from atlasse_v2.research.engine import ResearchExtensionEngine
from atlasse_v2.research.types import ResearchContext
from atlasse_v2.specification.spec_builder import SpecBuilder
from atlasse_v2.retrieval.evidence_ranker import EvidenceRanker


def _build_context(tmp_path):
    doc = make_sample_document()
    memory = ResearchMemory(doc.paper_id).build_from_document(doc)
    ranker = EvidenceRanker(memory, use_cross_encoder=False)
    spec = SpecBuilder(ranker).build(doc.paper_id)
    graph = SemanticPaperGraph(doc.paper_id).build_from_document(doc)
    blueprint = BlueprintGenerator(graph, spec=spec).generate(doc.paper_id)
    baseline = BaselineGenerator(graph, spec=spec).generate(doc.paper_id)
    repro = ReproductionEngine().build_report(baseline, spec, data_dir=str(tmp_path))
    return ResearchContext.from_pipeline(
        paper_id=doc.paper_id,
        spec=spec,
        blueprint=blueprint,
        baseline=baseline,
        reproduction_report=repro,
        graph=graph,
    )


def test_research_extension_labels(tmp_path):
    ctx = _build_context(tmp_path)
    engine = ResearchExtensionEngine()
    report = engine.run(ctx)

    assert report["mode"] == "research"
    assert report["failure_analysis"]["root_causes"]
    assert report["experiment_plan"]["count"] >= 3
    assert report["notebook"]["markdown"]
    assert "paper_supported" in report["notebook"]["label_legend"]

    for exp in report["experiment_plan"]["experiments"]:
        assert exp["item"]["label"] in {e.value for e in EvidenceLabel}
        assert exp["item"]["label_display"]

    path = engine.save(report, base_dir=str(tmp_path / "research_reports"))
    assert Path(path).exists()


def test_research_export(tmp_path):
    ctx = _build_context(tmp_path)
    engine = ResearchExtensionEngine()
    report = engine.run(ctx)
    manifest = engine.export(
        report,
        ["markdown", "csv", "configs", "jupyter"],
        base_dir=str(tmp_path / "research_reports"),
    )
    assert manifest["files"]
    assert not manifest.get("errors") or len(manifest["errors"]) < len(manifest["files"])


def test_pipeline_run_research_mode(tmp_path):
    from atlasse_v2.parsing.document_store import DocumentStore
    from atlasse_v2.pipeline import PaperPipeline

    doc = make_sample_document()
    data_dir = str(tmp_path)
    DocumentStore.save(doc, base_dir=f"{data_dir}/parsed")
    memory = ResearchMemory(doc.paper_id).build_from_document(doc)
    memory.save(base_dir=f"{data_dir}/memory_indices")
    ranker = EvidenceRanker(memory, use_cross_encoder=False)
    spec = SpecBuilder(ranker).build(doc.paper_id)
    SpecBuilder(ranker).save(spec, base_dir=f"{data_dir}/specifications")
    graph = SemanticPaperGraph(doc.paper_id).build_from_document(doc)
    graph.save(base_dir=f"{data_dir}/knowledge_graphs")
    BlueprintGenerator(graph, spec=spec).save(
        BlueprintGenerator(graph, spec=spec).generate(doc.paper_id),
        base_dir=f"{data_dir}/blueprints",
    )
    BaselineGenerator(graph, spec=spec).save(
        BaselineGenerator(graph, spec=spec).generate(doc.paper_id),
        base_dir=f"{data_dir}/baselines",
    )
    repro = ReproductionEngine().build_report(
        BaselineGenerator(graph, spec=spec).generate(doc.paper_id),
        spec,
        data_dir=data_dir,
    )
    ReproductionEngine().save(repro, base_dir=f"{data_dir}/reproduction_reports")

    pipeline = PaperPipeline(data_dir=data_dir)
    report = pipeline.run_research_mode(doc.paper_id)
    assert report["paper_id"] == doc.paper_id
    assert pipeline.get_research_report(doc.paper_id) is not None
