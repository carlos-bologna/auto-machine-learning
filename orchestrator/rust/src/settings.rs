extern crate names;

use names::{Generator, Name};
use config::{ConfigError, Config, File};
use serde::Deserialize;
use std::sync::{Arc, Mutex};
use std::env;
use std::rc::Rc;

#[derive(Debug, Deserialize)]
pub struct Default {
    pub current_dir: Arc<Mutex<String>>,
    pub workdir: Arc<Mutex<String>>,
    pub database: Arc<Mutex<String>>,
    pub database_delimiter: Arc<Mutex<String>>,
    pub target_column: Arc<Mutex<String>>,
    pub metric: Arc<Mutex<String>>,
    pub doc_image: Arc<Mutex<String>>,
    pub deploy_image: Arc<Mutex<String>>,
    pub project_name: Arc<Mutex<String>>
}

#[derive(Debug, Deserialize)]
pub struct Model {
    pub id: Arc<String>,
    pub name: Arc<String>,
    pub image: Arc<String>,
    pub version: Arc<String>
}

#[derive(Debug, Deserialize)]
pub struct Transform {
    pub id: Arc<String>,
    pub name: Arc<String>,
    pub image: Arc<String>,
    pub version: Arc<String>
}

#[derive(Debug, Deserialize)]
pub struct Settings {
    pub defaults: Arc<Default>,
    pub models: Vec<Arc<Model>>,
    pub transforms: Vec<Arc<Transform>>
}

impl Settings {

    pub fn new() -> Result<Self, ConfigError> {
        
        let mut s = Config::new();

        let mut path = match env::current_exe() {
            Ok(exe_path) => exe_path,
            Err(e) => panic!("failed to get current exe path: {}", e),
        };

        // Remove exe filename from full path.
        path.pop();

        let path_ = Rc::new(path.display());
        let transform_config_path = format!("{}/config/transforms", path_.clone());
        let models_config_path = format!("{}/config/models", &path_.clone());
        let defaults_config_path = format!("{}/config/defaults", &path_.clone());

        // Start off by merging in the "default" configuration file
        s.merge(File::with_name(&*transform_config_path))?;
        s.merge(File::with_name(&*models_config_path))?;
        s.merge(File::with_name(&*defaults_config_path))?;

        /*
        // Start off by merging in the "default" configuration file
        s.merge(File::with_name("config/transforms"))?;
        s.merge(File::with_name("config/models"))?;
        s.merge(File::with_name("config/defaults"))?;
        */

        // You can deserialize (and thus freeze) the entire configuration as
        s.try_into()

    }

    pub fn gen_proj_name(&self) {
        
        let mut generator = Generator::default(Name::Plain);
        let name = generator.next().unwrap();
        
        let mut project_name = self.defaults.project_name.lock().unwrap();
        project_name.clear();
        project_name.push_str(&name);

    }
}