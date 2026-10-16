# Valentino AI Studio v2 — integração Chatterbox

## TUTORIAL

# Valentino AI Studio

Programa para gerar narrações com inteligência artificial usando uma referência de voz.

## 1. Requisitos

Antes de começar, instale:

- [Python 3.11](https://www.python.org/downloads/)
- [Visual Studio Code](https://code.visualstudio.com/)
- [FFmpeg](https://ffmpeg.org/download.html)

O FFmpeg precisa estar configurado no PATH do Windows.

**Observação:** o programa pode funcionar usando apenas o processador (CPU), mas a geração de áudio pode ser bastante demorada.

## 2. Preparar o projeto

Extraia o arquivo ZIP e abra a pasta do projeto no VS Code.

Abra o terminal do VS Code (`Ctrl + J`) e execute:

```powershell
python -m venv .venv
```

Ative o ambiente virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a ativação, execute:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Depois, tente ativar novamente.

## 3. Instalar as dependências

Se o projeto tiver um arquivo `requirements.txt`, execute:

```powershell
python -m pip install -r requirements.txt
```

A instalação pode demorar alguns minutos.

## 4. Iniciar o programa

No terminal, execute:

```powershell
python -m uvicorn main:app
```

Depois, abra no navegador:

http://127.0.0.1:8000

## 5. Gerar áudio

1. Selecione um arquivo de referência de voz que você tenha autorização para utilizar.
2. Cole o texto que deseja narrar.
3. Selecione o idioma.
4. Clique para iniciar a geração.
5. Aguarde a conclusão e baixe o MP3.

## 6. Encerrar o programa

No terminal do VS Code, pressione `Ctrl + C`.

Para iniciar novamente, ative o ambiente virtual e execute:

```powershell
python -m uvicorn main:app
```

## Observações

- Na primeira execução, o programa pode precisar baixar os modelos de inteligência artificial.
- O tempo de geração depende do hardware do computador.
- Mantenha o terminal aberto durante a geração.
- Utilize apenas vozes para as quais você tenha permissão de uso.


-----



## Instalação (Windows, PowerShell)

1. Extraia o conteúdo do ZIP para `C:\Dev\valentino-ai-studio-v2` (mescle/substitua arquivos; **não apague `.venv`**).
2. Ative: `.\.venv\Scripts\Activate.ps1`
3. Instale: `python -m pip install -r requirements.txt`
4. O Chatterbox já deve estar instalado e testado na `.venv`. Caso contrário: `python -m pip install chatterbox-tts`.
5. Verifique `ffmpeg -version` no terminal. Se não funcionar, instale FFmpeg e adicione-o ao PATH.
6. Inicie: `python -m uvicorn main:app --reload`
7. Acesse `http://127.0.0.1:8000`.
8. Envie uma amostra de voz de uso autorizado e teste 1–2 frases antes de enviar um roteiro longo.

O motor é executado em CPU. A primeira geração pode baixar pesos do modelo; geração de horas de áudio pode demorar muito. O progresso por blocos é persistido em `data/`, e `Tentar novamente` reaproveita WAVs já concluídos. **Não execute duas instâncias do servidor** nem altere os arquivos durante um trabalho. O `--reload` reinicia o processo ao editar código; use sem `--reload` durante trabalhos longos.

O limite de caracteres não garante uma duração exata de quatro horas; revise a duração do arquivo final. A interface só oferece os idiomas cadastrados para o Chatterbox Multilingual, não todos os idiomas do mundo. Use apenas vozes com permissão para reprodução e verifique as licenças dos componentes.
