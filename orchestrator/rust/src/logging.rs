use log::LevelFilter;
use log4rs::append::file::FileAppender;
use log4rs::encode::pattern::PatternEncoder;
use log4rs::config::{Appender, Config, Root};

pub fn log_init(workdir: &str){

    let logfile = FileAppender::builder()
        .encoder(Box::new(PatternEncoder::new("{{\"id\": \"orchestrator\", \"process\": {I}, \"datetime\": \"{d(%Y-%m-%d %H:%M:%S,%3f)}\", \"level\": \"{l}\", \"message\": {{\"{m}\"}}}}\n")))
        .build(format!("{}/log/orchestrator.log", workdir)).unwrap();

    let config = Config::builder()
        .appender(Appender::builder().build("logfile", Box::new(logfile)))
        .build(Root::builder()
                   .appender("logfile")
                   .build(LevelFilter::Info)).unwrap();

    log4rs::init_config(config).unwrap();

}