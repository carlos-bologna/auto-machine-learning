# Instruções

## Docker

### Build
Construa uma imagem Docker a partir do aquivo de instruções Dockerfile com o seguinte comando:

```
$ TAG_VERSAO=1.0
$ sudo docker build --tag rpa_xgboost:$TAG_VERSAO .
```

### Run 
Depois da imagem construída, você pode testar a imagem local com o comando abaixo:

```
$ sudo docker run rpa_xgboost:$TAG_VERSAO
```

Abaixo um exemplo de execução da imagem criada, com um mapeamento de diretórios, para que você tenha acesso aos seus arquivos de dentro do container:

```
$ sudo docker run --mount type=bind,source=/home,target=/tmp rpa_xgboost:$TAG_VERSAO
```

Execução da imagem com a passagem de argumentos

```
$ sudo docker run --mount type=bind,source=/home,target=/tmp rpa_xgboost:$TAG_VERSAO --workdir rpa --id 123
```

Caso queira executar a imagem e permanecer dentro dela interativamente:

```
$ sudo docker run -it --entrypoint /bin/bash --mount type=bind,source=/home,target=/tmp rpa_xgboost:$TAG_VERSAO
```
