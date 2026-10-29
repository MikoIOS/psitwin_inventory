import json
from pathlib import Path

ARTICLES = json.loads((Path(__file__).resolve().parents[1] / 'knowledge/psitwin.json').read_text(encoding='utf-8'))
INTRODUCTION = '¡Hola! 👋 Soy Saiki Ψ, tu asistente inteligente de PsiTwin. Estoy aquí para ayudarte a gestionar tu inventario, conocer el estado de tus almacenes, interpretar predicciones de demanda y resolver dudas sobre cómo utilizar la plataforma. ¿Qué puedo hacer por ti hoy?'

def help_answer(normalized):
    if any(word in normalized for word in ('microfono', 'voz de saiki', 'conversacion por voz', 'transcripcion', 'reconocimiento', 'freetts', 'jorge')):
        article = next(a for a in ARTICLES if a['id'] == 'voz_saiki')
        return article['answer'], {'seccion': article['route'], 'articulo': article['id']}
    if any(word in normalized for word in ('sensor', 'monitoreo', 'temperatura', 'humedad')):
        article = next(a for a in ARTICLES if a['id'] == 'sensores')
        return article['answer'], {'seccion': article['route'], 'articulo': article['id']}
    # More specific nouns take precedence over generic "crear" / "registrar".
    for article in ARTICLES:
        if article['id'] == 'empresa' and any(noun in normalized for noun in ('producto', 'operario', 'almacen', 'zona', 'rack', 'inventario', 'sensor', 'pedido')):
            continue
        if any(keyword in normalized for keyword in article['keywords']):
            return article['answer'], {'seccion': article['route'], 'articulo': article['id']}
    return '¿Sobre qué sección de PsiTwin necesitas ayuda: productos, almacenes, inventario, operarios, sensores o pronósticos?', {}
