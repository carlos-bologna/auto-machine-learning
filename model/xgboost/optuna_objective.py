import optuna
import xgboost as xgb

N_FOLDS = 5

optuna.logging.set_verbosity(optuna.logging.ERROR)  # This verbosity change is just to simplify the notebook output.

class Objective(object):
    
    def __init__(self, dtrain, eval_metric):
        self.dtrain = dtrain
        self.eval_metric = eval_metric
        

    def __call__(self, trial):

        dtrain = self.dtrain

        param = {
            "verbosity": 0,
            "objective": "binary:logistic",
            "n_jobs": 1,
            "eval_metric": self.eval_metric,
            "booster": trial.suggest_categorical("booster", ["gbtree", "gblinear", "dart"]),
            "lambda": trial.suggest_loguniform("lambda", 1e-8, 1.0),
            "alpha": trial.suggest_loguniform("alpha", 1e-8, 1.0),
        }

        if param["booster"] == "gbtree" or param["booster"] == "dart":
            param["max_depth"] = trial.suggest_int("max_depth", 1, 9)
            param["eta"] = trial.suggest_loguniform("eta", 1e-8, 1.0)
            param["gamma"] = trial.suggest_loguniform("gamma", 1e-8, 1.0)
            param["grow_policy"] = trial.suggest_categorical("grow_policy", ["depthwise", "lossguide"])

        if param["booster"] == "dart":
            param["sample_type"] = trial.suggest_categorical("sample_type", ["uniform", "weighted"])
            param["normalize_type"] = trial.suggest_categorical("normalize_type", ["tree", "forest"])
            param["rate_drop"] = trial.suggest_loguniform("rate_drop", 1e-8, 1.0)
            param["skip_drop"] = trial.suggest_loguniform("skip_drop", 1e-8, 1.0)

        xgb_cv_results = xgb.cv(
            params=param,
            dtrain=dtrain,
            num_boost_round=10000,
            nfold=N_FOLDS,
            stratified=True,
            early_stopping_rounds=100,
            seed=1407,
            verbose_eval=False,
        )

        # Set n_estimators as a trial attribute; Accessible via study.trials_dataframe().
        trial.set_user_attr("n_estimators", len(xgb_cv_results))

        # Extract the best score.
        best_score = xgb_cv_results["test-auc-mean"].values[-1]
        return best_score
