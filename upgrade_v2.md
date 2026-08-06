ATLASS v2 — Research Cognition Refactor

ATLASS is NOT a PDF chatbot.

ATLASS is NOT a RAG system.

ATLASS is a research cognition engine.

The current implementation retrieves chunks and asks an LLM to synthesize answers.

This architecture fundamentally fails.

Examples:

identical paragraphs populate unrelated fields
datasets come from irrelevant text
objectives are extracted from introductions
blueprint modules are hallucinated
baselines become generic PyTorch templates

Do NOT fix prompts.

Redesign the reasoning engine.

High-Level Goal

Paper

↓

Structural parsing

↓

Evidence extraction

↓

Typed knowledge graph

↓

Research object graph

↓

Specification generation

↓

Blueprint generation

↓

Baseline synthesis

↓

Reproduction planning

Every downstream artifact must consume structured research objects instead of raw text.

Phase 1 — Robust Document Parsing

Replace regex section detection.

Implement a parser capable of identifying:

Abstract

Introduction

Related Work

Method

Architecture

Experiments

Implementation

Datasets

Results

Discussion

Limitations

Future Work

Appendix

References

Support:

GROBID

Docling

PyMuPDF

pdfplumber

fallback OCR

Store page numbers.

Store hierarchy.

Store section tree.

Store paragraph IDs.

Store figure references.

Store table references.

Store equations.

Never lose provenance.

Phase 2 — Semantic Paper Graph

Create a typed graph.

Entities:

Method

Dataset

Loss

Optimizer

Metric

Model

Module

Task

Input

Output

Contribution

Limitation

Future Work

Hyperparameter

Experiment

Baseline

Claim

Observation

Each entity stores

text

normalized name

page

section

paragraph id

confidence

citations

Graph edges:

uses_dataset

evaluates_on

improves

trained_with

compares_against

depends_on

extends

proposes

reports

Only graph objects may be consumed later.

Never raw paragraphs.

Phase 3 — Research Information Extraction

Implement dedicated extractors.

Not one giant prompt.

Create modules:

ProblemExtractor

ContributionExtractor

TaskExtractor

DatasetExtractor

MetricExtractor

MethodExtractor

ArchitectureExtractor

LossExtractor

TrainingExtractor

EvaluationExtractor

BaselineExtractor

LimitationExtractor

FutureWorkExtractor

Each extractor

retrieves only relevant evidence

asks a focused prompt

returns

value

supporting spans

confidence

citations

missing fields

Do NOT allow extractors to answer outside retrieved evidence.

Phase 4 — Evidence Ranking

Current retrieval is insufficient.

Implement:

BM25

Dense embeddings

CrossEncoder reranking

Section prior

Entity overlap

Recency inside paper

Score =

semantic

keyword

section weight

entity overlap

citation overlap

Only top reranked evidence reaches the LLM.

Phase 5 — Research Memory

Current chunks are too coarse.

Split paper into

paragraphs

semantic blocks

tables

captions

equations

algorithms

Store each independently.

Every chunk has

chunk_id

page

section

paragraph

entities

embedding

keywords

citations

This becomes permanent memory.

Phase 6 — Question Answering

Current QA simply summarizes.

Replace with pipeline.

Question

↓

Intent classifier

↓

Required entity types

↓

Retriever

↓

Reranker

↓

Evidence validator

↓

Answer generator

↓

Citation verifier

If evidence missing

say

"The paper does not specify."

Never hallucinate.

Phase 7 — System Specification

Current spec copies introduction paragraphs.

Instead.

Each field has a dedicated extractor.

Problem

Contribution

Task

Inputs

Outputs

Architecture

Loss

Optimizer

Datasets

Metrics

Training

Evaluation

Results

Limitations

Future Work

Each field stores

value

citations

confidence

missing

source chunks

No field should reuse another field's answer.

Phase 8 — Blueprint Generator

Do NOT generate folders from GPT imagination.

Blueprint derives from extracted architecture.

Pipeline:

Architecture graph

↓

Module decomposition

↓

Data flow

↓

Training flow

↓

Evaluation flow

↓

Inference flow

↓

Project tree

↓

Interfaces

↓

Dependencies

Each generated file must map back to evidence.

Example

TransformerEncoder

↓

src/model/encoder.py

Attention

↓

attention.py

Tokenizer

↓

tokenizer.py

Never generate modules unsupported by evidence.

Phase 9 — Baseline Generator

Current baseline is generic.

Instead.

Infer model family.

Possible families:

CNN

Transformer

Diffusion

GAN

VAE

Graph Neural Network

RNN

LSTM

MLP

RL

Siamese

UNet

Seq2Seq

Vision Transformer

MoE

Encoder Decoder

Retrieval

LoRA

PEFT

NeRF

etc.

Each family has templates.

Fill templates from research graph.

Missing values become explicit assumptions.

Phase 10 — Reproduction Engine

Separate

Smoke Test

Partial Reproduction

Paper Reproduction

Never compare synthetic metrics against paper metrics.

Instead classify:

Executable

Architecture matched

Dataset unavailable

Hyperparameters missing

Training infeasible

Metric comparable

Overall confidence

Phase 11 — Evaluation Framework

Create benchmark suite.

Evaluate against 100 arXiv papers.

Metrics:

Dataset extraction accuracy

Metric extraction accuracy

Contribution extraction

Architecture extraction

Hallucination rate

Evidence precision

Citation precision

Blueprint correctness

Baseline correctness

QA exact match

Track scores.

Regression test every commit.

Phase 12 — Agentic Pipeline

Replace linear pipeline.

Create agents.

Document Agent

Retrieval Agent

Research Agent

Evidence Agent

Specification Agent

Blueprint Agent

Baseline Agent

Evaluation Agent

Agents communicate through structured objects.

Never free-form text.

Phase 13 — UI Improvements

Backend already exposes stages.

Expose richer outputs.

Evidence viewer

Graph explorer

Architecture DAG

Section tree

Citation browser

Entity browser

Assumption tracker

Missing information tracker

Blueprint diff

Specification diff

Evidence inspector

Confidence heatmap

Phase 14 — Production Quality

Implement

Redis caching

Background jobs

Streaming responses

Incremental indexing

Persistent vector DB

Structured logging

OpenTelemetry

Unit tests

Integration tests

Golden paper tests

Snapshot tests

Benchmark harness

Phase 15 — Success Criteria

ATLASS should correctly answer papers such as

LoRA

ResNet

Transformer

BERT

CLIP

SAM

ViT

YOLO

DINO

Stable Diffusion

without repeating introduction paragraphs.

Every generated artifact must trace back to explicit evidence.

The generated baseline should represent the paper's actual architecture whenever sufficient evidence exists.

If information is unavailable, ATLASS must explicitly report uncertainty rather than invent details.

Prioritize correctness over completeness.

Never hallucinate.

document this as phase wise development track  under plan_v2.md and create tracker_v2.md with taks_v2.md documenting everything as instructed in above prompt