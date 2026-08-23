"""
Model evaluation framework (Requirement 29). Operates on labeled
(true_class, predicted_class) pairs - it does not know or care where they
came from (a real validation run, a unit test, or eventually a real
dataset), which is what makes it reusable once a real dataset exists.

Per Requirement 30/31: no dataset is downloaded or bundled by this module.
`EvaluationDatasetConfig.NOT_CONFIGURED` is the honest, explicit statement
required by Requirement 29 when no validated dataset is available -
callers must check `is_configured` before trusting any metric report.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass, field


@dataclass(frozen=True)
class EvaluationDatasetConfig:
    """Describes where a validation dataset lives and its licensing -
    never the dataset itself. See docs/AI_EVALUATION.md."""

    is_configured: bool
    name: str | None = None
    source: str | None = None
    license: str | None = None
    classes: list[str] = field(default_factory=list)
    notes: str | None = None

    @classmethod
    def not_configured(cls) -> "EvaluationDatasetConfig":
        return cls(is_configured=False, notes="Evaluation dataset not yet configured.")


@dataclass(frozen=True)
class ClassMetrics:
    class_name: str
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1: float
    support: int  # number of true instances of this class in the eval set


@dataclass(frozen=True)
class EvaluationReport:
    dataset: EvaluationDatasetConfig
    total_samples: int
    correct: int
    accuracy: float | None
    per_class: list[ClassMetrics]
    confusion_matrix: dict[str, dict[str, int]]  # confusion_matrix[true][predicted] = count
    unknown_count: int
    low_confidence_count: int


def evaluate(
    labeled_pairs: list[tuple[str, str]],
    *,
    dataset: EvaluationDatasetConfig,
    unknown_label: str = "unknown",
    low_confidence_label: str = "low_confidence",
) -> EvaluationReport:
    """
    labeled_pairs: list of (true_class, predicted_class) tuples. Predicted
    class may be `unknown_label` or `low_confidence_label` for samples the
    safety layer declined to answer confidently - these are tracked
    separately and never silently counted as wrong-but-specific guesses.
    """
    total = len(labeled_pairs)
    if total == 0:
        return EvaluationReport(
            dataset=dataset,
            total_samples=0,
            correct=0,
            accuracy=None,
            per_class=[],
            confusion_matrix={},
            unknown_count=0,
            low_confidence_count=0,
        )

    confusion: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    class_support: Counter = Counter()
    unknown_count = 0
    low_confidence_count = 0
    correct = 0

    all_classes: set[str] = set()

    for true_class, predicted_class in labeled_pairs:
        confusion[true_class][predicted_class] += 1
        class_support[true_class] += 1
        all_classes.add(true_class)
        if predicted_class not in (unknown_label, low_confidence_label):
            all_classes.add(predicted_class)

        if predicted_class == unknown_label:
            unknown_count += 1
        elif predicted_class == low_confidence_label:
            low_confidence_count += 1
        elif predicted_class == true_class:
            correct += 1

    per_class: list[ClassMetrics] = []
    for class_name in sorted(all_classes):
        tp = confusion[class_name][class_name]
        fp = sum(confusion[t][class_name] for t in confusion if t != class_name)
        fn = sum(count for pred, count in confusion[class_name].items() if pred != class_name)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        per_class.append(
            ClassMetrics(
                class_name=class_name,
                true_positives=tp,
                false_positives=fp,
                false_negatives=fn,
                precision=precision,
                recall=recall,
                f1=f1,
                support=class_support.get(class_name, 0),
            )
        )

    return EvaluationReport(
        dataset=dataset,
        total_samples=total,
        correct=correct,
        accuracy=correct / total,
        per_class=per_class,
        confusion_matrix={t: dict(preds) for t, preds in confusion.items()},
        unknown_count=unknown_count,
        low_confidence_count=low_confidence_count,
    )
