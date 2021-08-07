import argparse, logging, json
import pandas as pd
import joblib
import yaml
from glob import glob
from shutil import copytree
from custom_encoder import CustomEncoder

# Arguments
parser = argparse.ArgumentParser(description='Parâmetros necessários para a execução correta do código:')

parser.add_argument(
    '--workdir',
    metavar='W',
    help='eg.: 2020-01-31-1344')

# Global Variables
args        = parser.parse_args()
workdir     = args.workdir
id          = 'deploy'

# Log Config
logging.basicConfig(
    level=logging.INFO,
    filename=f'/tmp/{workdir}/log/deploy.log', 
    format='{{"id": "{}", "process": %(process)d, "datetime": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}}'.format(id))

def info(key, value):
    logging.info(f'{{"{key}": {json.dumps(value, cls=CustomEncoder)}}}')

# Read Log Files
def read_log_as_dataframe(workdir):
    filenames = glob(f'/tmp/{workdir}/log/*.log')
    dfrows = []
    for file in filenames:
        with open(file) as json_file:
            for record in json_file:
                
                record_dict = json.loads(record)
                message     = record_dict['message']

                if isinstance(message, dict):

                    key = list(message.keys())[0]
                    dfrows.append(
                        pd.DataFrame({
                            'id': [record_dict['id']],
                            'process': [record_dict['process']],
                            'datetime': [record_dict['datetime']],
                            'level':  [record_dict['level']],
                            'key': [key],
                            'value': [str(message[key])]
                        })
                    )
    df = pd.concat(dfrows, ignore_index=True)
    return df

def get_best_preprocess(df):
    
    preprocess_id = 'preprocess_basic' #Fixed for while

    pipeline = joblib.load(f'/tmp/{workdir}/model/{preprocess_id}.pkl')
    
    return preprocess_id, pipeline

def get_best_model(df):
    
    metric_df = df[df.key == 'metric-test']
    metric_df.reset_index(drop=True, inplace=True)
    metric_df = metric_df.astype({'value': 'float'})
    
    best_model_id = metric_df.iloc[metric_df['value'].idxmax()].id
    best_model = joblib.load(f'/tmp/{workdir}/model/{best_model_id}.pkl')

    # Get top 3 models
    metric_df.sort_values(by=['value'], inplace=True, ascending=False)
    top_models_dict = {} # From Python 3.6 onwards, the standard dict type maintains insertion order by default.
    for _, row in metric_df.iloc[0:3, :].iterrows():
        top_models_dict[f'${row.id}$'] = row.value #Put model_id between $ (eg.: $ramdomforest$) to convert it auto to fancy name in doc step.
    
    return best_model_id, best_model, top_models_dict

def gen_demo_page(df, preprocess_id, workdir):
    
    sample = df[(df.id == preprocess_id) & (df.key == 'sample')]['value'].values

    sample_dict = yaml.safe_load(sample[0])

    form = []

    for key, value in sample_dict.items():
        form.append(f'<div class="input-group mb-3"><div class="input-group-prepend"><span class="input-group-text" id="">{key}</span></div>')
        form.append(f'<input type="text" id="{key}" name="{key}" value="{value}" class="form-control"></div>')

    # Read Template
    f = open("template/demo.html_", "r")
    html = f.read()
    f.close()

    html = html.replace('$form$', ' '.join(form))

    text_file = open(f'/tmp/{workdir}/deploy/templates/demo.html', "w")
    n = text_file.write(html)
    text_file.close()

    return None

def gen_api_script(df, preprocess_id, workdir):
    
    schema = df[(df.id == preprocess_id) & (df.key == 'columns-dtypes')]['value'].values[0]

    # Read Template
    f = open("template/main.py_", "r")
    python_script = f.read()
    f.close()

    python_script = python_script.replace('$schema$', schema)

    text_file = open(f'/tmp/{workdir}/deploy/main.py', "w")
    n = text_file.write(python_script)
    text_file.close()

    return None

# Main function
def main():
    
    # Read Log Files
    df = read_log_as_dataframe(workdir)
    
    # Filter empty key value
    #df = df[df.key.notnull() & df.value.notnull()]

    # Get The Best Preprocess Object
    preprocess_id, pipe = get_best_preprocess(df)

    # Get The Best Model Object
    model_id, model, top_models_dict = get_best_model(df)

    # Log top 3 models
    info('best_model_id', model_id)
    info('model_rank', top_models_dict)

    # Add Model into Pipeline
    pipe.steps.append(('Model', model))

    # Write Pipeline
    filename = f'/tmp/{workdir}/deploy/pipeline.pkl'
    joblib.dump(pipe, filename)

    # Generate Demo Page
    gen_demo_page(df, preprocess_id, workdir)

    # Generate API Python Main Page
    gen_api_script(df, preprocess_id, workdir)

    # Copy API files    
    copytree('api/.', f'/tmp/{workdir}/deploy/', dirs_exist_ok=True)

if __name__ == "__main__":
    main()
