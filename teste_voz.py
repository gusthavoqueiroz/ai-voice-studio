import torch
import torchaudio
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

print("Carregando modelo Chatterbox...")

model = ChatterboxMultilingualTTS.from_pretrained(
    device="cpu"
)

print("Gerando áudio de teste...")

texto = (
    "La paz de Dios puede transformar tu corazón "
    "incluso en los momentos más difíciles de tu vida."
)

audio = model.generate(
    texto,
    language_id="es"
)

torchaudio.save(
    "teste_espanhol.wav",
    audio.cpu(),
    model.sr
)

print("Áudio gerado com sucesso!")