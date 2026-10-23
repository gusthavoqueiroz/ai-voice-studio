
import runpod
import torch

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


def handler(job):
    data = job.get("input", {})

    text = data.get("text", "")
    language = data.get("language", "es")

    if not text.strip():
        return {"error": "Nenhum texto enviado."}

    return {
        "status": "received",
        "characters": len(text),
        "language": language
    }


runpod.serverless.start({"handler": handler})
