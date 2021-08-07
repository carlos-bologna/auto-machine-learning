import os, argparse, logging, json
import pandas as pd
from glob import glob
from html_to_pdf_converter import get_pdf_from_html
import shutil
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

# Log Config
logging.basicConfig(
    level=logging.INFO,
    filename=f'/tmp/{workdir}/log/doc.log', 
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

def get_best_preprocess_id(df):
    
    preprocess_id = 'preprocess_basic' #Fixed for while

    return preprocess_id


def get_best_model_id(df):
    
    metric_df = df[df.key == 'metric-test']
    metric_df.reset_index(drop=True, inplace=True)
    metric_df = metric_df.astype({'value': 'float'})
    model_id = metric_df.iloc[metric_df['value'].idxmax()].id
    
    return model_id

def update_folder(orig, dest):
    try:
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(orig, dest)
    except OSError as e:
        print("Error: failed to update folder %s to %s : %s" % (orig, dest, e.strerror))

# Main function
def main():
    
    # Read Temnplate
    f = open("template/main.html", "r")
    doc = f.read()
    f.close()

    # Read Log Files
    df = read_log_as_dataframe(workdir)
    
    # Filter empty key value
    df = df[df.key.notnull() & df.value.notnull()]

    # Get Best Preprocess
    best_preprocess_id = get_best_preprocess_id(df)

    # Get Best Model
    best_model_id = get_best_model_id(df)

    # Filter Keys
    logs = ["orchestrator", "deploy"]
    logs.append(best_preprocess_id)
    logs.append(best_model_id)
    
    # Filter Logs
    df = df[df.id.isin(logs)]

    # ----------------------------- #
    # Replace Variables in Template #
    # ----------------------------- #
    for _, row in df.iterrows():
        doc = doc.replace(f'${row.key}$', row.value)

    # Run it again, but only in Orchestrator, in order to chance model_id to model Name.
    # Only when the key was printed between double $ 
    # (eg.: $$best_model_id$$ -> $randomforest$ -> run replace again -> Random Forest)
    df = df[df.id == 'orchestrator'] 
    for _, row in df.iterrows():
        doc = doc.replace(f'${row.key}$', row.value)

    # Write HTML
    text_file = open(f'/tmp/{workdir}/doc/doc.html', "w")
    _ = text_file.write(doc)
    text_file.close()

    # Copy CSS, images and JS files
    update_folder('./template/css', f'/tmp/{workdir}/doc/css')
    update_folder('./template/img', f'/tmp/{workdir}/doc/img')
    update_folder('./template/js', f'/tmp/{workdir}/doc/js')
    
    result = get_pdf_from_html(f'/tmp/{workdir}/doc/doc.html')
        
    # result = get_pdf_from_html('https://www.google.com')
    with open(f'/tmp/{workdir}/doc/doc.pdf', 'wb') as file:
        file.write(result)

    print(os.getcwd())    

if __name__ == "__main__":
    main()
