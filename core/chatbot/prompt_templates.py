from __future__ import annotations

from core.chatbot.intent_parser import UserIntent


def greeting_response() -> str:
    return (
        "Selam! Bugünkü ruh haline göre sana film, dizi, müzik veya oyun "
        "önerebilirim. Bir tür, atmosfer, dönem ya da benzemesini istediğin "
        "bir içerik yazman yeterli."
    )


def recommendation_intro(intent: UserIntent) -> str:
    pieces: list[str] = []
    if intent.media_type:
        pieces.append(f"medya tipi: {intent.media_type}")
    if intent.genres:
        pieces.append(f"tür: {', '.join(intent.genres)}")
    if intent.moods:
        pieces.append(f"ruh hali: {', '.join(intent.moods)}")
    if intent.era:
        pieces.append(f"dönem: {intent.era}")

    if not pieces:
        return "İsteğini aldım. Aşağıda en yakın görünen önerileri sıraladım."

    return "İsteğini şu sinyallerle yorumladım: " + "; ".join(pieces) + "."
