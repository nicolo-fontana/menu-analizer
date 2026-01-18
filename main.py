from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.media import Image
from dotenv import load_dotenv
from models.menu import Menu
from utils import generate_dish_image
import os
import tempfile
from pathlib import Path
from agno.models.ollama import Ollama
import asyncio
import threading
import concurrent.futures

load_dotenv()

# Configurazione
POE_BASE_URL = "https://api.poe.com/v1"
IMAGE_MODEL_NAME = "nano-banana"

model_type = "no"

if model_type == "local":
    model = Ollama(id="gemma3:12b-it-qat", host="http://192.168.15.32:11434")
else:
    model = OpenAIChat(name="gemini-2.0-flash-lite", base_url=POE_BASE_URL)

# Inizializza FastAPI
app = FastAPI(
    title="Menu Analyzer API",
    description="API per analizzare menu di ristoranti e generare immagini dei piatti",
    version="1.0.0",
)

# Configura CORS per permettere richieste dal frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specifica i domini esatti
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crea directory per upload temporanei
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.get("/")
async def root():
    """Endpoint di benvenuto"""
    return {
        "message": "Menu Analyzer API",
        "version": "1.0.0",
        "endpoints": {"process_menu": "/api/process-menu", "health": "/health"},
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/api/process-menu")
async def process_menu(request: Request, file: UploadFile = File(...)):
    """
    Processa un'immagine di un menu di ristorante.

    Args:
        file: Immagine del menu (PNG, JPG, JPEG)

    Returns:
        JSON con la struttura del menu (piatti, bevande, prezzi) e URL delle immagini generate
    """
    # Validazione del tipo di file
    allowed_types = ["image/png", "image/jpeg", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo di file non supportato. Usa: {', '.join(allowed_types)}",
        )

    # Crea file temporaneo per salvare l'upload
    try:
        # Leggi il contenuto del file
        contents = await file.read()

        # Salva in un file temporaneo
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".png", dir=UPLOAD_DIR
        ) as temp_file:
            temp_file.write(contents)
            temp_filepath = temp_file.name

        try:
            # Verifica se il client ha disconnesso
            if await request.is_disconnected():
                print("Client disconnesso durante l'upload")
                return

            # Carica l'immagine
            menu_image = Image(filepath=temp_filepath)

            # Crea l'agente AI per analizzare il menu
            agent = Agent(
                model=model,
                name="Agente di prova",
                description="Sei un agente AI esperto nella visualizzazione e interpretazione di menu dei ristoranti",
                output_schema=Menu,
            )

            # Verifica se il client ha disconnesso prima di analizzare
            if await request.is_disconnected():
                print("Client disconnesso prima dell'analisi")
                return

            # Analizza il menu con possibilità di interruzione
            try:
                # Flag di interruzione condiviso
                stop_event = threading.Event()

                # Esegui in un thread executor con timeout check
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    # Avvia il task in background
                    future = executor.submit(
                        agent.run,
                        "Riportami tutti il menu nel formato di output stabilito",
                        images=[menu_image],
                    )

                    # Monitora la connessione mentre il task è in esecuzione
                    while not future.done():
                        if await request.is_disconnected():
                            print(
                                "Client disconnesso durante l'analisi - termino l'esecuzione"
                            )
                            stop_event.set()
                            # Cancella il future
                            future.cancel()
                            # Attendi brevemente per permettere la cancellazione
                            await asyncio.sleep(0.5)
                            # Shutdown dell'executor per interrompere il thread
                            executor.shutdown(wait=False, cancel_futures=True)
                            print("Executor terminato - task interrotto")
                            return
                        await asyncio.sleep(0.1)

                    # Ottieni il risultato
                    try:
                        out = future.result(timeout=1)
                    except concurrent.futures.CancelledError:
                        print("Future cancellato")
                        return
                    except Exception as e:
                        print(f"Errore durante l'analisi: {e}")
                        raise

                # Verifica se il client ha disconnesso dopo l'analisi
                if await request.is_disconnected():
                    print("Client disconnesso dopo l'analisi")
                    return

                # Genera un'immagine per ogni piatto
                for piatto in out.content.piatti:
                    # Verifica disconnessione prima di ogni generazione
                    if await request.is_disconnected():
                        print(
                            f"Client disconnesso durante la generazione delle immagini"
                        )
                        return

                    print(f"Genero l'immagine per: {piatto.nome}")

                    # Genera l'immagine con possibilità di interruzione
                    with concurrent.futures.ThreadPoolExecutor(
                        max_workers=1
                    ) as img_executor:
                        img_future = img_executor.submit(
                            generate_dish_image,
                            nome=piatto.nome,
                            descrizione=piatto.descrizione or "",
                            base_url=POE_BASE_URL,
                            model_name=IMAGE_MODEL_NAME,
                        )

                        # Monitora la connessione
                        while not img_future.done():
                            if await request.is_disconnected():
                                print(
                                    f"Client disconnesso durante generazione immagine - termino"
                                )
                                img_future.cancel()
                                img_executor.shutdown(wait=False, cancel_futures=True)
                                return
                            await asyncio.sleep(0.1)

                        try:
                            image_url = img_future.result(timeout=1)
                        except concurrent.futures.CancelledError:
                            print("Generazione immagine cancellata")
                            return
                        except Exception as e:
                            print(f"Errore generazione immagine: {e}")
                            # Usa placeholder se fallisce
                            image_url = ""

                    # Aggiungi l'URL dell'immagine all'oggetto del piatto
                    piatto.image_url = image_url
                    print(f"URL immagine estratto: {image_url}")

                # Converti il risultato in dizionario
                result = out.content.model_dump()

                return {
                    "success": True,
                    "data": result,
                    "message": "Menu analizzato con successo",
                }

            except asyncio.CancelledError:
                print("Task cancellato - client disconnesso")
                raise

        finally:
            # Rimuovi il file temporaneo
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)

    except asyncio.CancelledError:
        print("Richiesta cancellata dal client")
        # Non sollevare eccezione, semplicemente ritorna
        return
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Errore durante l'elaborazione del menu: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
