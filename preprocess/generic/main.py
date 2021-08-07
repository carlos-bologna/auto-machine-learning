import os, argparse, logging
import pandas as pd
import vtreat
import joblib
import json
from random import randint  
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from pandas_profiling import ProfileReport
from custom_encoder import CustomEncoder

# Constants
SPLIT_SIZE = 0.2

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
    '--database',
    metavar='D',
    help='eg.: train.csv')

parser.add_argument(
    '--database_delimiter',
    metavar='S',
    default=';',
    help='The perapator of fields. eg.: ;')

parser.add_argument(
    '--target',
    metavar='T',
    help='eg.: target')

# Global Variables
args                = parser.parse_args()
id                  = args.id
workdir             = args.workdir
database            = args.database
database_delimiter  = args.database_delimiter
target              = args.target

# Log Config
logging.basicConfig(
    level=logging.INFO,
    filename=f'/tmp/{workdir}/log/{id}.log', 
    format='{{"id": "{}", "process": %(process)d, "datetime": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}}'.format(id))
    
def info(key, value):
    logging.info(f'{{"{key}": {json.dumps(value, cls=CustomEncoder)}}}')

def get_sample(df):
    idx = randint(0, len(df))
    return dict(df.iloc[idx])

def target_treatment(df, target):
    '''
    Rename target column to 'target'.
    Replace target value to numbers, according to their frequency.
    The most frequent becomes value 0, the second becomes 1, and so on.
    '''

    df = df.rename(columns={target: 'target'})

    # Rank by frequency
    count = df['target'].value_counts(dropna=False)
    info('target-count', count)
    rank = (count.rank(ascending=False, method='first') - 1).astype(int)
    info('target-label', rank)
    
    # Rename Columns
    df_rank = rank.reset_index(name='rank').rename(columns={'index': 'target'})

    # Replace named target by frequency rank
    df['target'] = pd.merge(df, df_rank, on='target', how='left')['rank']
    return df

# Main function
def main():
    
    # Log
    info('original-database', database)
    info('database-columns-delimiter', database_delimiter)
    info('original-target-column', target)

    # Read database
    df = pd.read_csv('/tmp/' + database, sep=f'{database_delimiter}')
    profile = ProfileReport(df, config_file='profile_config.yaml').get_description()

    # Log
    info('total-rows', len(df))
    info('total-cols', len(df.columns))
    info('columns', list(df.columns))
    info('columns-dtypes', df.dtypes.apply(lambda x: x.name).to_dict())
    info('sample', get_sample(df)) #Get sample before change target column name
    info('variables-profiling', profile['variables'])   
    info('profiling-messages', profile['messages'])
    info('variables-correlations', profile['correlations'])

    # Treat target column
    df = target_treatment(df, target)
    
    # Split database
    train, test = train_test_split(df, stratify = df['target'], test_size=SPLIT_SIZE)

    # Start Pipeline Steps
    pipeline_steps = []

    # vtreat
    transform = vtreat.BinomialOutcomeTreatment(
        outcome_name='target',    # outcome variable
        cols_to_copy=['target'],  # columns to "carry along" but not treat as input variables
        params = {
            'indicator_min_fraction': 0.1, #10% default value
            'filter_to_recommended': True # remove (default)
        })
    pipeline_steps.append(('VTreat', transform))

    # Log
    info('test-split-size', SPLIT_SIZE)
    info('train-rows', len(train))
    info('test-rows', len(test))

    # Pipeline Set
    pipe = Pipeline(pipeline_steps)

    # Pipeline Train and Fit
    train = pipe.fit_transform(train, train['target'])
    
    # Pipeline Fit Only (for test dataset)
    test = pipe.transform(test)

    #VTreat Log Info
    info('variable_treatments', transform.score_frame_)
    info('indicator_min_fraction', transform.params_['indicator_min_fraction'])
    info('filter_to_recommended', transform.params_['filter_to_recommended'])

    # Save Pipeline object
    filename = f'/tmp/{workdir}/model/{id}.pkl'
    joblib.dump(pipe, filename)

    # Destination path
    path = f'/tmp/{workdir}/data/'
    
    # Write result
    train.to_csv(path + 'train.csv', sep = ',', index = False)
    test.to_csv(path + 'test.csv', sep = ',', index = False)

if __name__ == "__main__":
    main()
