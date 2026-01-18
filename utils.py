import re
import openai


def extract_image_url(text: str) -> str:
    """
    Estrae l'URL dell'immagine da una stringa contenente markdown e URL.

    Args:
        text: Stringa che contiene markdown con immagini e/o URL diretti

    Returns:
        L'URL dell'immagine estratto
    """
    # Pattern per trovare URL di immagini (http/https seguito da estensione immagine o query params)
    url_pattern = r"https?://[^\s\)]+(?:\.(?:png|jpg|jpeg|gif|webp)|[^\s\)]*)"

    # Trova tutti gli URL nel testo
    urls = re.findall(url_pattern, text)

    if urls:
        # Ritorna il primo URL trovato (di solito quello nella sintassi markdown)
        return urls[0]

    return ""


def generate_dish_image(
    nome: str, descrizione: str, base_url: str, model_name: str
) -> str:
    """
    Genera un'immagine di un piatto di ristorante usando un modello AI.

    Args:
        nome: Nome del piatto
        descrizione: Descrizione del piatto
        base_url: URL base dell'API OpenAI
        model_name: Nome del modello da utilizzare per la generazione dell'immagine

    Returns:
        URL dell'immagine generata
    """
    client = openai.OpenAI(base_url=base_url)

    image_prompt = f"""
        Sei un assistente AI esperto nella creazione di immagini professionali e accattivanti di piatti di un ristorante.
        Crei sempre delle immagini con il prodotto descritto dall'utente senza mettere nessuna scritta in sovraimpressione all'immagine.

        Crea l'immagine del seguente prodotto:
        <prodotto>
        {nome}
        {descrizione}
        </prodotto>
    """

    chat = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": image_prompt,
            }
        ],
    )

    # Estrai l'URL dell'immagine dalla risposta
    image_url = extract_image_url(chat.choices[0].message.content)
    return image_url
    # return "https://pfst.cf2.poecdn.net/base/image/8d1d5c569feb14592678b196ba08cbbcff43d3262587c0f80682d7e2040359de?w=1024&h=1024"
