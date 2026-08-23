from app.core.config import get_settings
from app.services.ai.confidence import ConfidenceLevel, classify_confidence
from app.services.ai.evaluation import EvaluationDatasetConfig, evaluate
from app.services.ai.model_provider import DiseasePrediction, TopKPrediction
from app.services.ai.not_configured_provider import NotConfiguredModelProvider
from app.services.ai.prediction_validator import validate_disease_prediction

settings = get_settings()


class TestConfidenceEvaluator:
    def test_high_confidence(self):
        assert classify_confidence(0.90, settings) == ConfidenceLevel.HIGH

    def test_medium_confidence(self):
        assert classify_confidence(0.70, settings) == ConfidenceLevel.MEDIUM

    def test_low_confidence(self):
        assert classify_confidence(0.20, settings) == ConfidenceLevel.LOW

    def test_boundary_at_high_threshold_is_high(self):
        assert classify_confidence(settings.ai_confidence_high_threshold, settings) == ConfidenceLevel.HIGH

    def test_boundary_just_below_high_threshold_is_medium(self):
        assert classify_confidence(settings.ai_confidence_high_threshold - 0.01, settings) == ConfidenceLevel.MEDIUM


class TestNotConfiguredModelProvider:
    """Tests the actual production default - proves it never fabricates a result."""

    def test_is_not_ready(self):
        assert NotConfiguredModelProvider().is_ready() is False

    def test_supports_no_crops(self):
        assert NotConfiguredModelProvider().supported_crop_names() == []

    def test_predict_disease_is_unavailable(self):
        result = NotConfiguredModelProvider().predict_disease(b"fake", "tomato")
        assert result.available is False
        assert result.top_predictions == []

    def test_predict_stage_is_unavailable(self):
        result = NotConfiguredModelProvider().predict_stage(b"fake", "tomato")
        assert result.available is False
        assert result.stage_code is None


class TestPredictionValidator:
    def test_unavailable_model_maps_to_ai_unavailable(self):
        pred = DiseasePrediction(available=False)
        result = validate_disease_prediction(pred, crop_name="tomato", supported_crop_names=[], settings=settings)
        assert result.result_status.value == "ai_unavailable"
        assert result.requires_review is True

    def test_unsupported_crop_maps_to_unknown(self):
        pred = DiseasePrediction(available=True, top_predictions=[TopKPrediction("X", 0.99)])
        result = validate_disease_prediction(pred, crop_name="wheat", supported_crop_names=["tomato"], settings=settings)
        assert result.result_status.value == "unknown"
        assert result.predicted_class is None

    def test_crop_mismatch_is_never_silently_diagnosed(self):
        pred = DiseasePrediction(available=True, top_predictions=[TopKPrediction("X", 0.99)], crop_match=False)
        result = validate_disease_prediction(pred, crop_name="tomato", supported_crop_names=["tomato"], settings=settings)
        assert result.result_status.value == "crop_mismatch"
        assert result.predicted_class is None

    def test_low_confidence_never_names_a_class(self):
        pred = DiseasePrediction(available=True, top_predictions=[TopKPrediction("Early Blight", 0.10)], crop_match=True)
        result = validate_disease_prediction(pred, crop_name="tomato", supported_crop_names=["tomato"], settings=settings)
        assert result.result_status.value == "low_confidence"
        assert result.predicted_class is None

    def test_high_confidence_healthy(self):
        pred = DiseasePrediction(available=True, top_predictions=[TopKPrediction("Healthy", 0.95)], crop_match=True)
        result = validate_disease_prediction(pred, crop_name="tomato", supported_crop_names=["tomato"], settings=settings)
        assert result.result_status.value == "healthy"
        assert result.requires_review is False

    def test_high_confidence_disease(self):
        pred = DiseasePrediction(available=True, top_predictions=[TopKPrediction("Early Blight", 0.95)], crop_match=True)
        result = validate_disease_prediction(pred, crop_name="tomato", supported_crop_names=["tomato"], settings=settings)
        assert result.result_status.value == "disease_detected"
        assert result.predicted_class == "Early Blight"
        assert result.requires_review is False

    def test_medium_confidence_disease_requires_review(self):
        pred = DiseasePrediction(available=True, top_predictions=[TopKPrediction("Early Blight", 0.70)], crop_match=True)
        result = validate_disease_prediction(pred, crop_name="tomato", supported_crop_names=["tomato"], settings=settings)
        assert result.result_status.value == "disease_detected"
        assert result.requires_review is True  # medium confidence always requires review

    def test_no_predictions_at_all_maps_to_unknown(self):
        pred = DiseasePrediction(available=True, top_predictions=[], crop_match=True)
        result = validate_disease_prediction(pred, crop_name="tomato", supported_crop_names=["tomato"], settings=settings)
        assert result.result_status.value == "unknown"

    def test_top_k_predictions_are_preserved_in_result(self):
        preds = [TopKPrediction("Early Blight", 0.60), TopKPrediction("Late Blight", 0.25), TopKPrediction("Healthy", 0.15)]
        pred = DiseasePrediction(available=True, top_predictions=preds, crop_match=True)
        result = validate_disease_prediction(pred, crop_name="tomato", supported_crop_names=["tomato"], settings=settings)
        assert len(result.top_k_predictions) == 3
        assert result.top_k_predictions[1]["class_name"] == "Late Blight"


class TestEvaluationFramework:
    def test_not_configured_dataset_is_explicit(self):
        config = EvaluationDatasetConfig.not_configured()
        assert config.is_configured is False
        assert "not yet configured" in config.notes.lower()

    def test_empty_pairs_returns_none_accuracy(self):
        report = evaluate([], dataset=EvaluationDatasetConfig.not_configured())
        assert report.accuracy is None
        assert report.total_samples == 0

    def test_perfect_predictions_yield_100_percent_accuracy(self):
        pairs = [("healthy", "healthy"), ("early_blight", "early_blight")]
        report = evaluate(pairs, dataset=EvaluationDatasetConfig(is_configured=True, name="t"))
        assert report.accuracy == 1.0
        assert report.correct == 2

    def test_unknown_and_low_confidence_are_tracked_separately_from_wrong_answers(self):
        pairs = [("healthy", "unknown"), ("healthy", "low_confidence"), ("healthy", "early_blight")]
        report = evaluate(pairs, dataset=EvaluationDatasetConfig(is_configured=True, name="t"))
        assert report.unknown_count == 1
        assert report.low_confidence_count == 1
        assert report.correct == 0
        # accuracy denominator is total_samples, not "answered" samples -
        # unknown/low-confidence predictions still count against accuracy,
        # they're just tracked with their own counters too.
        assert report.total_samples == 3

    def test_per_class_metrics_are_computed(self):
        pairs = [
            ("healthy", "healthy"),
            ("healthy", "healthy"),
            ("early_blight", "healthy"),  # false negative for early_blight, false positive for healthy
        ]
        report = evaluate(pairs, dataset=EvaluationDatasetConfig(is_configured=True, name="t"))
        healthy_metrics = next(m for m in report.per_class if m.class_name == "healthy")
        assert healthy_metrics.true_positives == 2
        assert healthy_metrics.false_positives == 1
        blight_metrics = next(m for m in report.per_class if m.class_name == "early_blight")
        assert blight_metrics.false_negatives == 1
        assert blight_metrics.recall == 0.0
