API YouTube Downloader
======================

Introdução
----------

Bem-vindo à documentação do projeto de estudo: **API YouTube Downloader**. Esta API permite obter informações sobre vídeos do YouTube e realizar downloads em diferentes formatos e resoluções.

Este projeto foi desenvolvido com o objetivo de estudar e explorar as funcionalidades da linguagem Python. Ele foi criado logo após uma disciplina da faculdade que abordava essa linguagem. Embora simples, o projeto oferece uma base sólida para compreender conceitos importantes e aplicar diversas funcionalidades.

A API foi construída utilizando ``FastAPI`` e faz uso da biblioteca 
``pytubefix <https://github.com/JuanBindez/pytubefix>``_ para interagir com o YouTube. Todas as requisições devem ser feitas para o seguinte endpoint base:

::

    https://terrible-harrie-viniciusdizatnikis-773b6ba1.koyeb.app

ou

::

    https://youtube-downloader-api-s9lh.onrender.com

Vale lembrar que a API pode não estar online em determinados momentos, pois está hospedada em serviços gratuitos que possuem limitações de uso e créditos. Além disso, pode ocorrer o bloqueio do IP pelo YouTube caso as requisições sejam feitas sem o uso de tokens apropriados.

Este projeto é ótimo para usar em localhost, caso não queira ver anúncios em sites. Caso queira utilizá-lo em seu computador, siga os passos de como utilizar no **`GitHub <https://github.com/ViniciusDizatnikis/Youtube_Downloader-API>`_**.

.. warning::

   **Aviso Legal:** Esta API destina-se exclusivamente a fins pessoais e educacionais. Certifique-se de respeitar os Termos de Serviço do YouTube e as leis de direitos autorais vigentes.


Autenticação
------------

Atualmente, esta API não requer autenticação para uso. Todos os endpoints estão abertos para requisições.

.. note::

   **Nota:** Devido à natureza pública da API, limites de taxa podem ser aplicados para prevenir abusos.


Endpoints
---------

A seguir estão todos os endpoints disponíveis na **API**:

.. container:: endpoint

    **GET /**

    Retorna a página HTML inicial da API.

.. container:: endpoint

    **GET /config**

    Retorna informações de configuração da API, incluindo versão e detalhes sobre o método de token.

    Resposta de Exemplo:

    .. code-block:: json

        {
          "version": "1.0.0",
          "author": "Vinicius Dizatnikis",
          "lib": "pytubefix",
          "token_method": {
            "using_token": "Using the token method with a client may sometimes result in an unsuccessful request...",
            "not_using_token": "Not using the token method will result in a successful request, but your IP might be blocked by YouTube",
            "clients": [
              "WEB", "WEB_EMBED", "WEB_MUSIC", ..., "IOS_KIDS"
            ]
          }
        }

.. container:: endpoint

    **POST /resolutions**

    Retorna as resoluções disponíveis para um vídeo específico do YouTube.

    Parâmetros:

    +----------------+---------+------------+----------------------------------------------+
    | Nome           | Tipo    | Obrigatório| Descrição                                    |
    +================+=========+============+==============================================+
    | url            | string  | Sim        | URL completa do vídeo do YouTube             |
    +----------------+---------+------------+----------------------------------------------+
    | token_method   | string  | Não        | Método de token para evitar bloqueio (veja seção Token Method) |
    +----------------+---------+------------+----------------------------------------------+

    Exemplo de Requisição:

    .. code-block:: json

        {
          "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
          "token_method": "WEB"
        }

    Resposta de Exemplo:

    .. code-block:: json

        {
          "status": "success",
          "token_method": true,
          "client_of_token": "WEB",
          "Result": {
            "title": "Never Gonna Give You Up",
            "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
            "durations": 213,
            "resolutions": [
              {"itag": 22, "quality": "720p", "type": "video/mp4"},
              {"itag": 18, "quality": "360p", "type": "video/mp4"},
              {"itag": 140, "quality": "audio", "type": "audio/mp4"}
            ]
          }
        }

.. container:: endpoint

    **POST /info**

    Retorna informações detalhadas sobre um vídeo do YouTube.

    Parâmetros:

    +----------------+---------+------------+----------------------------------------------+
    | Nome           | Tipo    | Obrigatório| Descrição                                    |
    +================+=========+============+==============================================+
    | url            | string  | Sim        | URL completa do vídeo do YouTube             |
    +----------------+---------+------------+----------------------------------------------+
    | token_method   | string  | Não        | Método de token para evitar bloqueio          |
    +----------------+---------+------------+----------------------------------------------+

    Resposta de Exemplo:

    .. code-block:: json

        {
          "status": "success",
          "token_method": false,
          "Result": {
            "title": "Never Gonna Give You Up",
            "author": "Rick Astley",
            "description": "Official video for Rick Astley's hit song...",
            "views": 123456789,
            "length": "3:33",
            "upload_date": "2009-10-25",
            "keywords": ["rick", "astley", "never", "gonna"],
            "thumbnails": {
              "default": "https://i.ytimg.com/vi/dQw4w9WgXcQ/default.jpg",
              "medium": "https://i.ytimg.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
              "high": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"
            }
          }
        }

.. container:: endpoint

    **POST /download**

    Inicia o processo de download de um vídeo do YouTube. Retorna um ID de arquivo que pode ser usado para baixar o conteúdo.

    Parâmetros:

    +----------------+---------+------------+--------------------------------------------------+
    | Nome           | Tipo    | Obrigatório| Descrição                                        |
    +================+=========+============+==================================================+
    | url            | string  | Sim        | URL completa do vídeo do YouTube                 |
    +----------------+---------+------------+--------------------------------------------------+
    | itag           | integer | Sim        | Código do formato desejado (obtido via /resolutions) |
    +----------------+---------+------------+--------------------------------------------------+
    | token_method   | string  | Não        | Método de token para evitar bloqueio              |
    +----------------+---------+------------+--------------------------------------------------+

    Resoluções Permitidas:

    - ``1080p``, ``720p``, ``480p``, ``360p``, ``240p``, ``144p``, ``audio``

    Exemplo de Requisição:

    .. code-block:: json

        {
          "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
          "itag": 140,
          "token_method": "WEB"
        }

    Resposta de Exemplo:

    .. code-block:: json

        {
          "status": "success",
          "token_method": true,
          "client_of_token": "WEB",
          "Result": {
            "message": "Áudio convertido para MP3",
            "url_download": "https://api.seudominio.com/download/5f8d3a1b2c6d4e7f"
          }
        }

.. container:: endpoint

    **GET /download/{file_id}**

    Baixa o arquivo processado. O arquivo será automaticamente removido após o download.

    Parâmetros:

    +------------+---------+------------+----------------------------------------------+
    | Nome       | Tipo    | Obrigatório| Descrição                                    |
    +============+=========+============+==============================================+
    | file_id    | string  | Sim        | ID do arquivo obtido no endpoint /download   |
    +------------+---------+------------+----------------------------------------------+

    Resposta:

    Retorna o arquivo binário com os cabeçalhos apropriados para download.

    Notas:

    - Os arquivos são temporários e são automaticamente removidos após o download
    - O tempo limite para download é de aproximadamente 1 minuto
    - O nome do arquivo no cabeçalho de resposta será o título do vídeo


Token Method
------------

O método de token é uma técnica utilizada para evitar que o YouTube bloqueie seu endereço de IP. Ele permite especificar qual "cliente" (user agent) será utilizado durante a comunicação com a plataforma.

Clientes Disponíveis:

::

    [
      "WEB", "WEB_EMBED", "WEB_MUSIC", "WEB_CREATOR", "WEB_SAFARI", "MWEB", "WEB_KIDS",
      "ANDROID", "ANDROID_VR", "ANDROID_MUSIC", "ANDROID_CREATOR", "ANDROID_TESTSUITE",
      "ANDROID_PRODUCER", "ANDROID_KIDS", "IOS", "IOS_MUSIC", "IOS_CREATOR",
      "TV_EMBEDDED", "TV_ANDROID", "TV_ANDROID_APP", "TV_ANDROID_MUSIC",
      "TV_FIRETV", "TV_FIRETV_APP", "TV_ROKU", "TV_SAMSUNG", "TV_LG",
      "TV_VIZIO", "TV_APPLE", "TV_XBOX", "TV_PLAYSTATION", "TV_TIZEN",
      "TV_TIZEN_APP", "TV_ORIGIN", "TV_CRACKLE", "TV_WASABI",
      "TV_YOUTUBE_KIDS", "TV_YOUTUBE_KIDS_APP", "IOS_KIDS"
    ]

Dicas:

- Utilizar o método de token pode resultar em uma requisição mais lenta.
- Não utilizar o método pode causar bloqueio de IP pelo YouTube.


Como Usar
---------

1. Para obter as resoluções disponíveis de um vídeo:

   Faça uma requisição POST para ``/resolutions`` com a URL do vídeo e opcionalmente o método de token.

2. Para obter informações detalhadas do vídeo:

   Faça uma requisição POST para ``/info`` com a URL do vídeo.

3. Para baixar o vídeo ou áudio:

   Faça uma requisição POST para ``/download`` com a URL do vídeo e o ``itag`` do formato desejado.

4. Baixe o arquivo final usando o ``file_id`` retornado na resposta em uma requisição GET para ``/download/{file_id}``.


Exemplos
--------

Exemplo de requisição para obter resoluções:

.. code-block:: bash

    curl -X POST https://youtube-downloader-api-s9lh.onrender.com/resolutions \
         -H "Content-Type: application/json" \
         -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ","token_method":"WEB"}'

Exemplo de requisição para informações:

.. code-block:: bash

    curl -X POST https://youtube-downloader-api-s9lh.onrender.com/info \
         -H "Content-Type: application/json" \
         -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

Exemplo de requisição para download:

.. code-block:: bash

    curl -X POST https://youtube-downloader-api-s9lh.onrender.com/download \
         -H "Content-Type: application/json" \
         -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ", "itag":22, "token_method":"WEB"}'


Contato
-------

Para dúvidas, sugestões ou colaborações, acesse o repositório do projeto no GitHub:

`YouTube Downloader API - GitHub <https://github.com/ViniciusDizatnikis/Youtube_Downloader-API>`_

---

**Vinicius Dizatnikis**  
Desenvolvedor e mantenedor do projeto  
2025

