
# API YouTube Downloader

Como utilizar a API para baixar vídeos do YouTube em sua maquina.

## Como utilizar

1. Clone este repositório em sua máquina:
   ```bash
   git clone https://github.com/ViniciusDizatnikis/Youtube_Downloader-API.git
   ```

2. Abra o projeto em sua IDE.

3. Abra um terminal na pasta raiz do projeto clonado.

4. Execute o seguinte comando para iniciar o servidor:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. Aguarde o servidor iniciar. Quando estiver rodando, acesse:
   ```
   http://localhost:8000
   ```

6. Agora você pode fazer requisições para a API no endereço acima.

## Informações

Para mais informações sobre a API, consulte a documentação personalizada em:

[Documentação da API opção 1](https://terrible-harrie-viniciusdizatnikis-773b6ba1.koyeb.app)

[Documentação da API opção 2](https://youtube-downloader-api-s9lh.onrender.com)

[docs/documentation.rst](https://github.com/ViniciusDizatnikis/Youtube_Downloader-API/blob/master/docs/documentation.rst)

---

> **Observação:** Certifique-se de ter o Python e o Uvicorn instalados. Caso não tenha, instale-os via pip:
> ```bash
> pip install -r requirements.txt
> ```
