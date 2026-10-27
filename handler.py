
import runpod
import torch
import requests
import tempfile
import os

from chatterbox.mtl_tts import ChatterboxMultilingualTTS

model = None


def load_model():
    global model

    if model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Carregando Chatterbox em: {device}")

        model = ChatterboxMultilingualTTS.from_pretrained(
            device=device
        )

    return model

def generate_audio(text, language, reference_path, output_path):
    voice = load_model()

    audio = voice.generate(
        text,
        language_id=language,
        audio_prompt_path=reference_path,
        exaggeration=0.3,
        cfg_weight=0.5,
        temperature=0.7
    )

    import torchaudio

    torchaudio.save(
        output_path,
        audio.cpu(),
        voice.sr
    )

    return output_path

def download_reference(reference_url):
    response = requests.get(reference_url, timeout=120)
    response.raise_for_status()

    with tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False
    ) as temp_file:
        temp_file.write(response.content)
        return temp_file.name

def handler(job):
    data = job.get("input", {})

    text = data.get("text", "")
    language = data.get("language", "es")
    reference_url = data.get("reference_url", "")

    if not isinstance(text, str) or not text.strip():
        return {"error": "Nenhum texto enviado."}

    if not isinstance(reference_url, str) or not reference_url:
        return {"error": "Nenhuma referência de voz enviada."}

    # Teste inicial: limitar o texto a 300 caracteres
    if len(text) > 300:
        return {"error": "O teste aceita até 300 caracteres."}

    reference_path = None
    output_path = None

    try:
        import uuid

        reference_path = download_reference(reference_url)

        output_path = os.path.join(
            tempfile.gettempdir(),
            f"valentino_{uuid.uuid4().hex}.wav"
        )

        generate_audio(
            text=text,
            language=language,
            reference_path=reference_path,
            output_path=output_path
        )

        return {
            "status": "generated",
            "message": "Áudio gerado com sucesso.",
            "characters": len(text),
            "language": language,
            "file_size": os.path.getsize(output_path)
        }

    except Exception as e:
        print(f"Erro na geração: {e}")
        return {"error": "Falha ao gerar o áudio. Consulte os logs."}

    finally:
        for path in (reference_path, output_path):
            if path and os.path.exists(path):
                os.remove(path)


runpod.serverless.start({"handler": handler})
