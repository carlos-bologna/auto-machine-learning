extern crate config;
extern crate csv;
extern crate serde;
extern crate chrono;

mod settings;
mod logging;

use settings::Settings;
use logging::log_init;
use std::process::Command;
use std::thread;
use std::fs;
use std::env;
use std::process;
use std::result::Result;
use std::sync::Arc;
use std::io::stdin;
use std::str;
// For Datatime manipulation
use std::time::SystemTime;
use chrono::prelude::DateTime;
use chrono::Local;

fn loginfo(key: String, msg: String){
    log::info!("{}\": \"{}", key, msg);
}


fn get_database(settings: Arc<Settings>) -> Result<(), &'static str> {
    
    // Read database file from file system.deploy()
    let paths = fs::read_dir("./").unwrap();

    let mut files = Vec::new();

    paths
        .filter_map(Result::ok)
        .filter_map(|d| {
            d.path()
                .to_str()
                .and_then(|f| if f.ends_with(".csv") | f.ends_with(".tab") { Some(d) } else { None })
        })
        .for_each(|f| files.push(f.path()));

    match files.len() {
        0 => {
            return Err("Ops...não encontrei nenhuma base de dados no diretório corrente. \
            Eu preciso de dados (muitos dados) para que eu possa aprender com eles. \
            Sugiro você rodar este programa em um diretório contendo algum arquivo do tipo CSV, assim eu usarei este arquivo para aprender.");
        }

        1 => {
            let new_database = &files[0];
            let mut database = settings.defaults.database.lock().unwrap();
            database.clear();
            database.push_str(new_database.to_str().unwrap());
            Ok(())
        },

        _ => 
        {
            println!("Eu encontrei mais de um arquivo de dados no diretório corrente, \
            com qual deles devo trabalhar?");

            for (i, f) in files.iter().enumerate(){
                println!("{}: {}", i+1, f.to_str().unwrap());
            };
            
            loop{
                
                println!("Digite o número correspondente à base de dados desejada: ");
    
                let mut input = String::new();
    
                match stdin().read_line(&mut input) {
                    
                    Ok(_) => {
                        
                        let parsed = input.trim_end().parse::<u64>();
    
                        match parsed {
    
                            Ok(n) => {
    
                                let new_database = &files.get((n - 1) as usize);
                                
                                if let Some(file) = new_database {
                                    let mut database = settings.defaults.database.lock().unwrap();
                                    database.clear();
                                    database.push_str(file.to_str().unwrap());
                                    break;
    
                                } else{
                                    println!("O número que você escolheu não consta no menu que mostramos.");
                                    continue;
                                }
    
                            },
                            Err(_) => {
                                println!("Valor inválido.");
                                continue;
                            }
                            
                        }
    
                        
                    }
                    Err(_) => return Err("Ocorreu um erro técnico quando tentamos te perguntar qual a informação alvo para treinarmos o algoritmo\
                    esta é a informação que chamamos de variável resposta."),
                }
            
            }
            Ok(())
        }
    }
}

fn get_database_delimiter(settings: Arc<Settings>) -> u8 {

    let database = settings.defaults.database.lock().unwrap();

    let delimiters = vec![b',', b';', b'\t'];

    let mut delimiter = delimiters[0];

    for d in &delimiters{

        let mut reader = csv::ReaderBuilder::new().delimiter(*d).from_path(database.as_str()).unwrap();

        let headers = reader.headers().unwrap();
        let num_headers = headers.len();

        if let Some(result) = reader.records().next(){
            let num_cols = result.unwrap().len();

            if (num_headers == num_cols) & (num_headers > 1) & (num_cols > 1){
                delimiter = *d;
                break;
            }
        }
    }
    let mut database_delimiter = settings.defaults.database_delimiter.lock().unwrap();
    database_delimiter.clear();
    database_delimiter.push_str(str::from_utf8(&[delimiter]).unwrap());
    delimiter
}

fn get_target(settings: Arc<Settings>) -> Result<(), &'static str> {

    let delimiter = get_database_delimiter(settings.clone());

    let database = settings.defaults.database.lock().unwrap();
    
    let mut target_column = settings.defaults.target_column.lock().unwrap();

    //let mut reader = match csv::Reader::from_path(database.as_str()){
    //    Ok(file)    => file,
    //    Err(_)      => return Err("Erro na tentativa de ler o banco de dados")
    //};

    let mut reader = match csv::ReaderBuilder::new().delimiter(delimiter).from_path(database.as_str()){
        Ok(file)    => file,
        Err(_)      => return Err("Erro na tentativa de ler o banco de dados")
    };

    let headers = match reader.headers(){
        Ok(head)    => head,
        Err(_)      => return Err("Erro na tentativa de ler as colunas do banco de dados")
    };

    let mut columns = Vec::new();

    headers
        .iter()
        .for_each(|col| columns.push(col));

    if columns.contains(&target_column.as_str()){
        Ok(())
    }else{

        println!("Qual a informação que devo aprender a prever? Esta informação é o que chamados de variável resposta no aprendizado de máquina.");

        for (i, col) in columns.iter().enumerate(){
            println!("{}: {}", i+1, col);
        };
        
        loop{
            
            println!("Digite uma opção: ");

            let mut input = String::new();

            match stdin().read_line(&mut input) {
                
                Ok(_) => {
                    
                    let parsed = input.trim_end().parse::<u64>();

                    match parsed {

                        Ok(n) => {

                            let new_target_column = &columns.get((n - 1) as usize);
                            
                            if let Some(col) = new_target_column {

                                target_column.clear();
                                target_column.push_str(col);
                                break;

                            } else{
                                println!("O número que você escolheu não consta no menu que mostramos.");
                                continue;
                            }

                        },
                        Err(_) => {
                            println!("Valor inválido.");
                            continue;
                        }
                        
                    }

                    
                }
                Err(_) => return Err("Ocorreu um erro técnico quando tentamos te perguntar qual a informação alvo para treinarmos o algoritmo\
                esta é a informação que chamamos de variável resposta."),
            }
        
        }
        Ok(())
    }
    
}

fn spawn_preprocess(settings: Arc<Settings>) {

    // Make a vector to hold the children which are spawned.
    let mut children = vec![];

    for transform in settings.transforms.iter() {

        let transform_ = Arc::clone(&transform);
        let settings_ = Arc::clone(&settings);

        children.push(thread::spawn(move || {
                
            let status = Command::new("docker")
                .arg("run")
                .arg("--mount")
                .arg(format!("type=bind,source={},target=/tmp", settings_.defaults.current_dir.lock().unwrap().as_str()))
                .arg(format!("{}:{}", transform_.image, transform_.version))
                .arg("--id")
                .arg(format!("{}", transform_.id))
                .arg("--workdir")
                .arg(settings_.defaults.workdir.lock().unwrap().as_str())
                .arg("--database")
                .arg(settings_.defaults.database.lock().unwrap().as_str())
                .arg("--database_delimiter")
                .arg(settings_.defaults.database_delimiter.lock().unwrap().as_str())
                .arg("--target")
                .arg(settings_.defaults.target_column.lock().unwrap().as_str())
                .status()
                .expect(
                    "A etapa de preprocessamento da base de dados sofreu uma falha. \
                Sugiro comunicar o time mantenedor deste projeto.",
                );

            if status.success() {
                Ok(())
            }
            else{
                return Err("Erro na modelagem")
            }

        }));
    }

    for child in children {
        // Wait for the thread to finish. Returns a result.
        let _ = child.join();
    }
}

fn preprocess(settings: Arc<Settings>) -> Result<(), &'static str> {
    
    match get_database(settings.clone()) {
        Ok(_) => {
            match get_target(settings.clone()) {
                Ok(_) => spawn_preprocess(settings.clone()),
                Err(e) => return Err(e),
            };
        }
        Err(e) => return Err(e),
    };
    Ok(())
}

fn learn(settings: Arc<Settings>) -> Result<(), &'static str> {
    
    // Make a vector to hold the children which are spawned.
    let mut children = vec![];

    for model in settings.models.iter() {

        let model_ = Arc::clone(&model);
        let settings_ = Arc::clone(&settings);

        loginfo(model_.id.to_string(), model.name.to_string());
            
        children.push(Command::new("docker")
            .arg("run")
            .arg("--mount")
            .arg(format!("type=bind,source={},target=/tmp", settings_.defaults.current_dir.lock().unwrap().as_str()))
            .arg(format!("{}:{}", model_.image, model_.version))
            .arg("--id")
            .arg(format!("{}", model_.id))
            .arg("--workdir")
            .arg(settings_.defaults.workdir.lock().unwrap().as_str())
            .arg("--metric")
            .arg(settings_.defaults.metric.lock().unwrap().as_str())
            .spawn()
            .expect(
                "A etapa de modelagem sofreu uma falha. \
            Sugiro comunicar o time mantenedor deste projeto.",
            ));

    }

    for child in children {
        // Wait for the thread to finish. Returns a result.
        let _ = child.wait_with_output().expect("failed to wait on child");
    }

    Ok(())
}

fn doc(settings: Arc<Settings>) -> Result<(), &'static str> {
    
    let settings_ = Arc::clone(&settings);

    let _output = Command::new("docker")
            .arg("run")
            .arg("--mount")
            .arg(format!("type=bind,source={},target=/tmp", settings_.defaults.current_dir.lock().unwrap().as_str()))
            .arg(format!("{}", settings_.defaults.doc_image.lock().unwrap().as_str()))
            .arg("--workdir")
            .arg(settings_.defaults.workdir.lock().unwrap().as_str())
            .output()
            .expect(
                "A etapa de documentação do estudo sofreu uma falha. \
            Sugiro comunicar o time mantenedor deste projeto.",
            );
            
    //println!("process exited with: {}", status);
    //assert!(status.success());
    Ok(())
    
}

fn deploy(settings: Arc<Settings>) -> Result<(), &'static str>{

    let settings_ = Arc::clone(&settings);

    Command::new("docker")
            .arg("run")
            .arg("--mount")
            .arg(format!("type=bind,source={},target=/tmp", settings_.defaults.current_dir.lock().unwrap().as_str()))
            .arg(format!("{}", settings_.defaults.deploy_image.lock().unwrap().as_str()))
            .arg("--workdir")
            .arg(settings_.defaults.workdir.lock().unwrap().as_str())
            .status()
            .expect(
                "A etapa de deploy do estudo sofreu uma falha. \
            Sugiro comunicar o time mantenedor deste projeto.",
            );

    let _output = Command::new("docker")
            .arg("build")
            .arg("--tag")
            .arg(format!("{}", settings_.defaults.project_name.lock().unwrap().as_str()))
            .arg(format!("{}/{}/deploy", 
                settings_.defaults.current_dir.lock().unwrap().as_str(), 
                settings_.defaults.workdir.lock().unwrap().as_str()))
            .output()
            .expect(
                "A etapa de deploy (geração da imagem Docker) do estudo sofreu uma falha. \
            Sugiro comunicar o time mantenedor deste projeto.",
            );
        
    Ok(())
}

fn create_workdir(settings: Arc<Settings>) -> Result<(), ()> {

    // Set current path for future uses
    let new_current_dir = env::current_dir().unwrap();
    let mut current_dir = settings.defaults.current_dir.lock().unwrap();
    current_dir.clear();
    current_dir.push_str(new_current_dir.to_str().unwrap());

    // Create DateTime from SystemTime
    let datetime = DateTime::<Local>::from(SystemTime::now());

    // Formats the combined date and time with the specified format string.
    let timestamp_str = datetime.format("%Y-%m-%d-%Hh%M").to_string();
    
    let mut workdir = settings.defaults.workdir.lock().unwrap();
    workdir.clear();
    workdir.push_str(&timestamp_str);

    fs::create_dir_all(format!("{}/data", timestamp_str)).unwrap();
    fs::create_dir_all(format!("{}/model", timestamp_str)).unwrap();
    fs::create_dir_all(format!("{}/doc", timestamp_str)).unwrap();
    fs::create_dir_all(format!("{}/deploy/templates", timestamp_str)).unwrap();
    fs::create_dir_all(format!("{}/deploy/static", timestamp_str)).unwrap();
    fs::create_dir_all(format!("{}/log", timestamp_str)).unwrap();
    
    Ok(())

}

// This is the `main` thread
fn main() {
    
    // Settings
    let settings = Settings::new();

    let settings_ = match settings {
        Ok(s) => Arc::new(s),
        Err(error) => {
            println!("Ops...deu um problema ao tentar abrir seu arquivo de configuração. \
            Provavelmente você deva ter alterado o arquivo, adicionando ou excluindo algum modelo ou preprocessamento e, \
            durante esta alteração, algo deu errado. \
            Verifique se esqueceu de alguma coisa. As vezes, pode ter sido o esquecimento de um sinal ou aspas. \
            Caso não encontre o problema, vou mostrar a seguir o erro técnico que ocorreu, talvez possa te ajudar: {:?}", error);

            process::exit(1);
        }
    };
    
    // Workdir
    match create_workdir(settings_.clone()) {
        Ok(_) => (),

        Err(error) => {
            println!("Ops...deu um problema ao tentar criar a pasta aonde o programa irá colocar o resultado do trabalho. \
            Em geral, este problema é contornado apenas executando o programa novamente após se passar 1 minutos. \
            Caso o problema persista, pode ser algo mais técnico e, neste caso, sugerimos informar a equipe mantenedora deste projeto, \
            informando a seguinte mensagem técnica: {:?}", error);

            process::exit(1);
        }
    };

    // Logger
    log_init(settings_.clone().defaults.workdir.lock().unwrap().as_str());
    //log::info!("Start");

    // Project Name
    Settings::gen_proj_name(&settings_);
    loginfo("project-name".to_string(), settings_.clone().defaults.project_name.lock().unwrap().as_str().to_string());
    //log::info!("project-name\": \"{}", settings_.clone().defaults.project_name.lock().unwrap().as_str());

    // Run Dockers
    
    match preprocess(settings_.clone()) {
        Ok(_)   => match learn(settings_.clone()) {
            Ok(_)   => {
                match deploy(settings_.clone()){
                    Ok(_)   => {
                        match doc(settings_.clone()){
                            Ok(_)   => (),
                            Err(e)  => println!("{}", e)
                        };
                    },
                    Err(e)  => println!("{}", e)
                };
            }
            Err(e)  => println!("{}", e),
        },
        Err(e)  => println!("{}", e),
    };
    
    // End

    //log::info!("End");
}
