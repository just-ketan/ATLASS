"""Shared type enumerations for the ATLASS v2 research cognition engine."""

from enum import Enum


class SectionType(str, Enum):
    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    RELATED_WORK = "related_work"
    METHOD = "method"
    ARCHITECTURE = "architecture"
    EXPERIMENTS = "experiments"
    IMPLEMENTATION = "implementation"
    DATASETS = "datasets"
    RESULTS = "results"
    DISCUSSION = "discussion"
    LIMITATIONS = "limitations"
    FUTURE_WORK = "future_work"
    APPENDIX = "appendix"
    REFERENCES = "references"
    UNKNOWN = "unknown"


class EntityType(str, Enum):
    METHOD = "method"
    DATASET = "dataset"
    LOSS = "loss"
    OPTIMIZER = "optimizer"
    METRIC = "metric"
    MODEL = "model"
    MODULE = "module"
    TASK = "task"
    INPUT = "input"
    OUTPUT = "output"
    CONTRIBUTION = "contribution"
    LIMITATION = "limitation"
    FUTURE_WORK = "future_work"
    HYPERPARAMETER = "hyperparameter"
    EXPERIMENT = "experiment"
    BASELINE = "baseline"
    CLAIM = "claim"
    OBSERVATION = "observation"


class EdgeType(str, Enum):
    USES_DATASET = "uses_dataset"
    EVALUATES_ON = "evaluates_on"
    IMPROVES = "improves"
    TRAINED_WITH = "trained_with"
    COMPARES_AGAINST = "compares_against"
    DEPENDS_ON = "depends_on"
    EXTENDS = "extends"
    PROPOSES = "proposes"
    REPORTS = "reports"


class ModelFamily(str, Enum):
    CNN = "cnn"
    TRANSFORMER = "transformer"
    DIFFUSION = "diffusion"
    GAN = "gan"
    VAE = "vae"
    GNN = "graph_neural_network"
    RNN = "rnn"
    LSTM = "lstm"
    MLP = "mlp"
    RL = "rl"
    SIAMESE = "siamese"
    UNET = "unet"
    SEQ2SEQ = "seq2seq"
    VIT = "vision_transformer"
    MOE = "moe"
    ENCODER_DECODER = "encoder_decoder"
    RETRIEVAL = "retrieval"
    LORA = "lora"
    PEFT = "peft"
    NERF = "nerf"
    UNKNOWN = "unknown"


class ReproductionLevel(str, Enum):
    SMOKE_TEST = "smoke_test"
    PARTIAL = "partial_reproduction"
    FULL = "paper_reproduction"


class ReproductionStatus(str, Enum):
    EXECUTABLE = "executable"
    ARCHITECTURE_MATCHED = "architecture_matched"
    DATASET_UNAVAILABLE = "dataset_unavailable"
    HYPERPARAMETERS_MISSING = "hyperparameters_missing"
    TRAINING_INFEASIBLE = "training_infeasible"
    METRIC_COMPARABLE = "metric_comparable"
