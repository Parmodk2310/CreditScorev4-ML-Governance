from creditscore.model.metrics import calculate_classification_metrics


def test_metrics_shape():
    result = calculate_classification_metrics([0, 0, 1, 1], [0.1, 0.4, 0.7, 0.9])
    assert result["roc_auc"] == 1.0
    assert set(result["confusion_matrix"]) == {"tn", "fp", "fn", "tp"}
