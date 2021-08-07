# Modules
import argparse, logging, json
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import uniform, randint
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix
import joblib
import scorecardpy as sc
from custom_encoder import CustomEncoder
import shap
import matplotlib.pyplot as plt

# Constants
n = 30

# Arguments
parser = argparse.ArgumentParser(description='Parâmetros necessários para a execução correta do código:')

parser.add_argument(
    '--id',
    metavar='I',
    help='The id of Docker image. eg.: preprocess_basic. The ID is different from Docker Image Id.')

parser.add_argument(
    '--workdir',
    metavar='W',
    help='eg.: 2020-01-31-1344')

parser.add_argument(
    '--metric',
    metavar='M',
    help='eg.: roc_auc')

# Global Variables
args        = parser.parse_args()
workdir     = args.workdir
id          = args.id
metric      = args.metric

# Log Config
logging.basicConfig(
    level=logging.INFO,
    filename=f'/tmp/{workdir}/log/{id}.log', 
    format='{{"id": "{}", "process": %(process)d, "datetime": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}}'.format(id))

def info(key, value):
    logging.info(f'{{"{key}": {json.dumps(value, cls=CustomEncoder)}}}')

# Main function
def main():
    # Read database
    path = f'/tmp/{workdir}'
    train = pd.read_csv(f'{path}/data/train.csv')
    test = pd.read_csv(f'{path}/data/test.csv')

    # Select target 
    y_train = train['target']
    y_test = test['target']

    # Select features
    X_train = train.drop(columns = 'target', axis=1)
    X_test = test.drop(columns = 'target', axis=1)
    
    # Pipeline
    estimators = [('mod', RandomForestClassifier())]
    pipe = Pipeline(estimators)

    # Tuning
    loc_split   = 2 / len(X_train)
    loc_leaf    = 1 / len(X_train)
    distributions = dict(mod__n_estimators=randint(10, 1000),
                         mod__criterion=['gini','entropy'],
                         mod__min_samples_split=uniform(loc_split, .5 - loc_split),
                         mod__min_samples_leaf=uniform(loc_leaf, .5 - loc_leaf),
                         mod__max_features=['auto', 'sqrt', 'log2'],    
                         mod__min_impurity_decrease=uniform(),
                         mod__oob_score=[True,False],
                         mod__warm_start=[True,False])

    search = RandomizedSearchCV(pipe,
                                distributions,
                                n_iter = n,
                                scoring = metric,
                                n_jobs=-1)

    # Fit model
    search.fit(X_train, y_train)

    # Metrics
    prob_train  = search.predict_proba(X_train)[:,1]
    auc_train   = roc_auc_score(y_train, prob_train)

    prob_test   = search.predict_proba(X_test)[:,1]
    auc_test    = roc_auc_score(y_test, prob_test)
    
    pred_train  = search.predict(X_train)
    acc_train   = accuracy_score(y_train, pred_train)

    pred_test   = search.predict(X_test)
    acc_test    = accuracy_score(y_test, pred_test)

    cm_train    = confusion_matrix(y_train, pred_train)
    cm_test     = confusion_matrix(y_test, pred_test)

    # Log for Hyperparameters
    info('hyperparameters', search.best_params_)
    
    # Logs for metrics
    info('metric-id', metric)
    info('metric-train', auc_train)
    info('metric-test', auc_test)
    info('acc-train', acc_train)
    info('acc-test', acc_test)
    info('cm_train', {'c00': cm_train[0,0], 'c01': cm_train[0,1], 'cm10': cm_train[1,0], 'cm11': cm_train[1,1]})
    info('cm_test', {'c00': cm_test[0,0], 'c01': cm_test[0,1], 'cm10': cm_test[1,0], 'cm11': cm_test[1,1]})

    # Feature importances
    importances = search.best_estimator_.named_steps['mod'].feature_importances_
    features = X_train.columns
    n_features = len(features)
    feature_importances = {}
    for i in range(n_features):
        feature_importances[features[i]] = importances[i]

    info('feature_importances', feature_importances)

    # Shap Values
    explainer   = shap.TreeExplainer(model=search.best_estimator_.named_steps['mod'])
    shap_values = explainer.shap_values(X_train)

    shap.summary_plot(
        shap_values[1], 
        X_train, 
        show=False, 
        max_display=10)

    plt.tight_layout()
    plt.savefig(f'{path}/doc/{id}_shapvaluesummary.svg')
    info('shapvaluesummary-img', f'{id}_shapvaluesummary.svg')

    # Shap Value Sample
    sample = 0 #any index
    shap.force_plot(
        explainer.expected_value[1],
        shap_values[1][sample, :],
        X_train.iloc[sample, :],
        show = False,
        matplotlib = True,
        figsize = (20, 4),
        text_rotation = -15
    )

    plt.tight_layout()
    plt.savefig(f'{path}/doc/{id}_shapvaluesample.svg')
    info('shapvaluesample-img', f'{id}_shapvaluesample.svg')

    # PSI
    psi = sc.perf_psi(
        score = {'train': pd.DataFrame({'prob': prob_train}), 'test': pd.DataFrame({'prob': prob_test})},
        label = {'train': y_train, 'test': y_test},
        show_plot = False
    )

    info('psi', psi['psi'].PSI[0])

    # Save model
    filename = f'{path}/model/{id}.pkl'
    joblib.dump(search, filename)

if __name__ == "__main__":
    main()
