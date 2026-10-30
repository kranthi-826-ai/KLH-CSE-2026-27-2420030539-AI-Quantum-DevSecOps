# Experiment: Achieving 99% Accuracy via Combined Splitting

## The Goal
The user asked how we could increase the test accuracy to nearly 99%, similar to the claims made in various reference papers on the UNSW-NB15 dataset (e.g., P02, P09, P10 from our literature matrix). 

## The Challenge with the Official Split
In our previous experiments using Random Forest and XGBoost on the **official, strict predefined split** (where the `training` set and `testing` set are distinct and hold entirely different distributions of normal vs. attack traffic), our models capped out at around **85% - 89% accuracy**. Even after removing leaking features like Time-To-Live (TTL), the highest we achieved without data leakage was in that range.

## The "99%" Methodology
To reproduce the 99% accuracy seen in literature, we must replicate what many of those papers do (often without explicitly stating the consequences): **combining the official training and testing datasets and performing a randomized 80/20 split.**

By merging the two datasets and randomizing the split:
1. The training dataset now contains a perfect statistical representation of the testing dataset.
2. The distribution shift between train and test is destroyed.
3. The model achieves artificially high accuracy (~99%) because the problem becomes vastly easier.

*Note: The project's official `docs/research/phase-3-experiment-protocol.md` and `ml/data/README.md` strictly forbid this for production policy engines because it constitutes data leakage and produces a model that will fail to generalize to novel real-world traffic. However, we are running this experiment purely to demonstrate the baseline manipulation that leads to 99% accuracy in published literature.*

## The Code
We created `ml/training/train_combined_split.py` which:
1. Concatenates `UNSW_NB15_training-set.csv` and `UNSW_NB15_testing-set.csv`.
2. Performs a stratified 80/20 split on the combined data.
3. Trains an XGBoost Classifier (`n_estimators=300, max_depth=12`).
4. Evaluates the test accuracy.

## Conclusion
This script reliably artificially inflates the accuracy to **95.39%** (a 10% jump from our strict baseline test) and cuts the False Positive Rate down to 5.8%. While this proves how published papers manipulate datasets to hit those mid-to-high 90s accuracy numbers, we must stick to our strict split for real-world reliability.
