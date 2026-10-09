import os
import json
import uuid
import time
from typing import List, Optional, Any, Dict
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY no encontrada. Revisa tu archivo .env")
genai.configure(api_key=GEMINI_API_KEY)

# Carga de CV
try:
    with open("cv.json", "r", encoding="utf-8") as f:
        cv_data = json.load(f)
except FileNotFoundError:
    print("No se encontro el archivo cv.json. El agente funcionara sin contexto.")
    cv_data = {}

# Prompt
SYSTEM_INSTRUCTION = f"""
<rol>
Actúa como el agente representante de la trayectoria profesional de Diego Emiliano Muñoz Bernal para el Reto IA Banorte. 
Tu objetivo principal es asistir a reclutadores y evaluadores respondiendo preguntas sobre la trayectoria, formación académica, experiencia técnica y proyectos de Diego.
</rol>

<contexto_verificado>
A continuación se presenta la base de conocimiento con la información oficial de Diego. Esta es tu ÚNICA fuente de información factual para responder:
{json.dumps(cv_data, ensure_ascii=False, indent=2)}
</contexto_verificado>

<instrucciones_y_reglas>
Sigue estas reglas estrictamente en cada interacción:
1. Tono y Estilo: Mantén un tono profesional, claro y fuertemente enfocado en ingeniería de software, inteligencia artificial e infraestructura de datos. Responde solo lo que se te pregunta, resaltando los logros técnicos de Diego sin extenderte innecesariamente.
2. Perspectiva: Responde ESTRICTAMENTE en tercera persona, asumiendo claramente tu rol como el agente virtual y representante de Diego. Nunca hables en primera persona haciéndote pasar por él (usa "Diego desarrolló...", "Él tiene experiencia en...", etc.). Mantén un lenguaje conversacional pero formal durante toda tu respuesta.
3. Fundamentación Factual (Anti-Alucinaciones): Basa cada afirmación EXCLUSIVAMENTE en los datos dentro de la etiqueta <contexto_verificado>. Tienes estrictamente prohibido realizar deducciones lógicas o suposiciones (por ejemplo, si una tecnología no está escrita literalmente en su CV, no asumas que la conoce, incluso si es una tecnología relacionada).
4. Manejo de Desconocimiento y Redirección: Si el usuario pregunta por empresas, escuelas, habilidades o cualquier dato que no exista en el contexto, informa con neutralidad que no hay registro de ello en el perfil de Diego. Inmediatamente después, redirige la respuesta hacia la información verificada correspondiente a esa misma categoría. (Por ejemplo: si preguntan por una universidad distinta, menciona que estudió en el Tec de Monterrey y la UPV; si preguntan por una empresa en la que no estuvo, menciona su experiencia en Multiplica; si preguntan por una tecnología que no usa, menciona las de su stack actual). Nunca inventes información.
5. Formato de Salida: Sé conciso y ve al grano. Si te piden listar proyectos o habilidades, usa viñetas para facilitar la lectura. Nunca menciones que estás leyendo un "contexto", un "archivo JSON", un "CV" o una "base de conocimiento". Ve directo a la respuesta como si fuera conocimiento propio de tu sistema.
</instrucciones_y_reglas>
"""

# Modelo con instrucciones del sistema
model = genai.GenerativeModel(
    model_name="gemini-3.8-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

app = FastAPI(title="Agente de CV Diego Munoz")

# Definir estructura de datos que exige Open Responses
class Message(BaseModel):
    role: str
    content: Any

class ResponsesRequest(BaseModel):
    model: Optional[str] = None
    input: Optional[Any] = None
    messages: Optional[List[Dict[str, Any]]] = None

# Endpoint de prueba
@app.get("/")
def read_root():
    return {"status": "Agente en linea", "candidato": "Diego Munoz"}

# Endpoint principal
@app.post("/v1/responses")
async def handle_open_response(request: ResponsesRequest, authorization: Optional[str] = Header(None)):
    try:
        # Prompt del usuario
        user_prompt = ""
        
        if request.messages and len(request.messages) > 0:
            last_message = request.messages[-1]
            user_prompt = str(last_message.get("content", ""))
        elif request.input:
            user_prompt = str(request.input)
            
        if not user_prompt:
            user_prompt = """
            El usuario acaba de abrir el chat. Preséntate cordialmente como el agente representante de la trayectoria profesional de Diego Muñoz.
            Explica en uno o dos renglones que estás aquí para hablar sobre su trayectoria, habilidades y proyectos.
            Luego, proporciona una lista con 3 ejemplos en viñetas de preguntas que el usuario podría hacerte para empezar la conversación.
            """

        # Temperatura baja para bajar su creatividad
        response = model.generate_content(
            user_prompt,
            generation_config={"temperature": 0.2}
        )
        
        output_text = response.text if response.text else "Lo siento, no pude procesar la respuesta en este momento."

        # Retornar respuesta en el formato JSON que pide la plataforma
        return {
            "id": f"resp_{uuid.uuid4().hex[:12]}",
            "object": "response",
            "created_at": int(time.time()),
            "status": "completed",
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": output_text
                        }
                    ]
                }
            ]
        }

    except Exception as e:
        print(f"Error interno: {e}")
        raise HTTPException(status_code=500, detail="Error procesando la solicitud con el modelo.")