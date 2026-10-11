# Model Evaluation

A model must be evaluated on data it did not train on.

## Train / validation / test
- Training set: fit the model.
- Validation set: tune hyperparameters.
- Test set: report final performance once.

## Cross-validation
K-fold cross-validation splits data into k folds, trains on k-1, validates on the held-out fold, and averages scores.

## Confusion matrix
For classification, the confusion matrix counts true positives, false positives, true negatives, and false negatives.
