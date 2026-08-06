"""Agent orchestration and trace tests."""

from pathlib import Path

from atlasse_v2.agents.orchestrator import AgentOrchestrator
from atlasse_v2.evaluation.golden_acceptance import GOLDEN_PROFILES, make_golden_pdf


def test_orchestrator_full_trace(tmp_path):
    pdf = tmp_path / "2106.09685.pdf"
    make_golden_pdf(pdf, GOLDEN_PROFILES["2106.09685"])

    orch = AgentOrchestrator(data_dir=str(tmp_path))
    summary, trace = orch.process_with_trace(str(pdf), paper_id="2106.09685")

    assert summary["paper_id"] == "2106.09685"
    assert summary["agent_trace_saved"]
    assert trace["success"]
    assert len(trace["steps"]) == 8
    agent_names = {s["agent_name"] for s in trace["steps"]}
    assert agent_names == {
        "document_agent",
        "retrieval_agent",
        "research_agent",
        "evidence_agent",
        "specification_agent",
        "blueprint_agent",
        "baseline_agent",
        "evaluation_agent",
    }

    loaded = orch.get_trace("2106.09685")
    assert loaded is not None
    assert loaded["paper_id"] == "2106.09685"


def test_job_queue_runs_ingest(tmp_path):
    from atlasse_v2.infra import JobQueue

    pdf = tmp_path / "lora_job.pdf"
    make_golden_pdf(pdf, GOLDEN_PROFILES["2106.09685"])
    data_dir = str(tmp_path / "data")
    jobs = JobQueue(job_dir=f"{data_dir}/jobs")

    def _work():
        orch = AgentOrchestrator(data_dir=data_dir)
        summary, _ = orch.process_with_trace(str(pdf), paper_id="job_lora")
        return summary

    job_id = jobs.submit(_work)
    for _ in range(200):
        status = jobs.get(job_id)
        if status and status["status"] in ("completed", "failed"):
            break
        import time
        time.sleep(0.05)

    status = jobs.get(job_id)
    assert status["status"] == "completed"
    assert status["result"]["paper_id"] == "job_lora"
