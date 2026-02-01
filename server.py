#!/usr/bin/env python3
"""
Serveur MCP pour l'automatisation des candidatures
"""

import asyncio
import json
import subprocess
import requests
import sys
import platform
from pathlib import Path
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp import types

# Logging dans un fichier au lieu de stdout (pour ne pas interférer avec MCP)
import logging
import os

log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, 'mcp_server.log')

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration - OpenRouter API
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = "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"
OPENROUTER_MODEL = "deepseek/deepseek-r1-0528:free"  # Modèle fiable sur OpenRouter

# Utiliser le répertoire du script pour les fichiers
SCRIPT_DIR = Path(__file__).parent
JOBS_FILE = SCRIPT_DIR / "jobs_all.json"
SCRAPER_PATH = SCRIPT_DIR / "indeedScrap.py"

USER_PROFILE = {
    "name": "Safaa",
    "skills": ["Python", "Docker", "n8n", "Automation", "AI/ML", "Git"],
    "experience": "Junior - 2 ans",
    "education": "BUT Informatique",
    "languages": ["Français", "Anglais"],
    "location": "Paris",
    "interests": ["DevOps", "Data Engineering", "AI Development"]
}

# Créer le serveur
server = Server("job-automation-mcp")


def call_openrouter(prompt: str, system_prompt: str = "") -> str:
    """Appelle l'IA OpenRouter"""
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:8001",
            "X-Title": "Job Automation MCP",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": OPENROUTER_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        logging.info(f"Calling OpenRouter API with model: {OPENROUTER_MODEL}")
        response = requests.post(OPENROUTER_API_URL, json=payload, headers=headers, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "Erreur: pas de réponse")
        else:
            error_detail = response.text
            logging.error(f"OpenRouter API error {response.status_code}: {error_detail}")
            return f"Erreur API OpenRouter: {response.status_code} - {error_detail[:200]}"
    except Exception as e:
        logging.error(f"OpenRouter call error: {str(e)}")
        return f"Erreur: {str(e)}"


def load_jobs() -> list[dict]:
    """Charge les jobs depuis le fichier JSON"""
    if not JOBS_FILE.exists():
        return []
    try:
        with open(JOBS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Liste tous les outils disponibles"""
    return [
        types.Tool(
            name="search_jobs",
            description="Cherche des offres d'emploi sur Indeed",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Mot-clé (ex: Python developer)"
                    },
                    "location": {
                        "type": "string",
                        "description": "Localisation",
                        "default": "Paris"
                    }
                },
                "required": ["keyword"]
            }
        ),
        types.Tool(
            name="get_jobs_summary",
            description="Résumé intelligent de toutes les offres avec l'IA",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="analyze_job_match",
            description="Analyse la compatibilité d'un job avec le profil",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_index": {
                        "type": "integer",
                        "description": "Index du job (0 = premier)"
                    }
                },
                "required": ["job_index"]
            }
        ),
        types.Tool(
            name="get_best_matches",
            description="Trouve les meilleures offres pour le profil",
            inputSchema={
                "type": "object",
                "properties": {
                    "top_n": {
                        "type": "integer",
                        "description": "Nombre de suggestions",
                        "default": 5
                    }
                }
            }
        ),
        types.Tool(
            name="generate_cover_letter",
            description="Génère une lettre de motivation personnalisée",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_index": {
                        "type": "integer",
                        "description": "Index du job"
                    },
                    "tone": {
                        "type": "string",
                        "description": "Ton de la lettre",
                        "enum": ["professionnel", "enthousiaste", "créatif"],
                        "default": "professionnel"
                    }
                },
                "required": ["job_index"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict
) -> list[types.TextContent]:
    """Exécute un outil"""
    
    if name == "search_jobs":
        keyword = arguments.get("keyword", "")
        location = arguments.get("location", "Paris")
        
        try:
            if not SCRAPER_PATH.exists():
                return [types.TextContent(
                    type="text",
                    text=f"❌ Script scraper non trouvé à {SCRAPER_PATH}"
                )]
            
            result = subprocess.run(
                [sys.executable, str(SCRAPER_PATH), keyword],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=120
            )
            
            if result.returncode != 0:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Erreur scraping: {result.stderr}"
                )]
            
            jobs = load_jobs()
            
            if not jobs:
                return [types.TextContent(
                    type="text",
                    text=f"Aucune offre trouvée pour '{keyword}'"
                )]
            
            summary = f"✅ {len(jobs)} offres trouvées pour '{keyword}' à {location}\n\n"
            for i, job in enumerate(jobs[:5], 1):
                summary += f"{i}. {job.get('job_title', 'N/A')}\n"
                summary += f"   🏢 {job.get('company', 'N/A')}\n"
                summary += f"   📍 {job.get('location', 'N/A')}\n"
                summary += f"   📝 {job.get('contract', 'N/A')}\n\n"
            
            return [types.TextContent(type="text", text=summary)]
        
        except Exception as e:
            return [types.TextContent(type="text", text=f"❌ Erreur: {str(e)}")]
    
    elif name == "get_jobs_summary":
        jobs = load_jobs()
        
        if not jobs:
            return [types.TextContent(
                type="text",
                text="Aucune offre. Lancez search_jobs() d'abord."
            )]
        
        jobs_brief = [{
            "titre": j.get('job_title', ''),
            "entreprise": j.get('company', ''),
            "contrat": j.get('contract', ''),
            "lieu": j.get('location', '')
        } for j in jobs[:15]]
        
        prompt = f"""
Analyse ces {len(jobs)} offres d'emploi:

{json.dumps(jobs_brief, ensure_ascii=False, indent=2)}

Fournis:
1. Nombre total d'offres
2. Top 5 entreprises
3. Types de contrats
4. Compétences demandées
5. Opportunités pour profil junior
"""
        
        ai_response = call_openrouter(prompt, "Tu es un expert RH.")
        return [types.TextContent(type="text", text=ai_response)]
    
    elif name == "analyze_job_match":
        job_index = arguments.get("job_index", 0)
        jobs = load_jobs()
        
        if not jobs or job_index >= len(jobs):
            return [types.TextContent(
                type="text",
                text=f"Index invalide. {len(jobs)} offres disponibles."
            )]
        
        job = jobs[job_index]
        
        prompt = f"""
Analyse compatibilité:

PROFIL: {json.dumps(USER_PROFILE, ensure_ascii=False)}

OFFRE:
Titre: {job.get('job_title')}
Entreprise: {job.get('company')}
Description: {job.get('description', '')[:800]}

Fournis: score/10, points forts, manques, recommandation.
"""
        
        ai_response = call_openrouter(prompt, "Tu es un expert RH.")
        return [types.TextContent(type="text", text=ai_response)]
    
    elif name == "get_best_matches":
        top_n = arguments.get("top_n", 5)
        jobs = load_jobs()
        
        if not jobs:
            return [types.TextContent(type="text", text="Aucune offre disponible.")]
        
        jobs_brief = [{
            "index": i,
            "titre": j.get('job_title'),
            "entreprise": j.get('company')
        } for i, j in enumerate(jobs)]
        
        prompt = f"""
Sélectionne les {top_n} meilleures offres pour ce profil:

PROFIL: {json.dumps(USER_PROFILE, ensure_ascii=False)}

OFFRES: {json.dumps(jobs_brief[:20], ensure_ascii=False)}

Pour chaque: index, raison, score/10.
"""
        
        ai_response = call_openrouter(prompt, "Tu es expert en matching.")
        return [types.TextContent(type="text", text=ai_response)]
    
    elif name == "generate_cover_letter":
        job_index = arguments.get("job_index", 0)
        tone = arguments.get("tone", "professionnel")
        jobs = load_jobs()
        
        if not jobs or job_index >= len(jobs):
            return [types.TextContent(type="text", text="Index invalide.")]
        
        job = jobs[job_index]
        
        prompt = f"""
Génère lettre de motivation {tone}:

PROFIL: {json.dumps(USER_PROFILE, ensure_ascii=False)}

OFFRE: {job.get('job_title')} chez {job.get('company')}

250-300 mots, structure classique, en français.
"""
        
        ai_response = call_openrouter(prompt, "Tu es expert en lettres de motivation.")
        result = f"📄 LETTRE DE MOTIVATION\n{'='*50}\n\n{ai_response}"
        return [types.TextContent(type="text", text=result)]
    
    else:
        raise ValueError(f"Outil inconnu: {name}")


@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """Liste les ressources"""
    return [
        types.Resource(
            uri="profile://user",
            name="Profil utilisateur",
            mimeType="application/json"
        ),
        types.Resource(
            uri="jobs://database",
            name="Base de données jobs",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Lit une ressource"""
    logging.info(f"Lecture de la ressource: {uri} (type: {type(uri)})")
    
    # Selon la version du SDK, uri peut être un string ou un objet ReadResourceRequest
    if isinstance(uri, str):
        uri_str = uri
    elif hasattr(uri, 'uri'):
        uri_str = uri.uri
    else:
        uri_str = str(uri)
    
    logging.info(f"URI extrait: {uri_str}")
    
    if uri_str == "profile://user":
        result = json.dumps(USER_PROFILE, indent=2, ensure_ascii=False)
        logging.info(f"Retour profil: {result[:100]}...")
        return result
    elif uri_str == "jobs://database":
        jobs = load_jobs()
        result = json.dumps(jobs, indent=2, ensure_ascii=False)
        logging.info(f"Retour jobs: {len(jobs)} offres")
        return result
    else:
        logging.error(f"Ressource inconnue: {uri_str}")
        raise ValueError(f"Ressource inconnue: {uri_str}")

async def main():
    """Lance le serveur MCP"""
    try:
        logging.info("🚀 Serveur MCP Job Automation démarré")
        logging.info(f"📂 Jobs: {JOBS_FILE}")
        logging.info(f"🔧 Scraper: {SCRAPER_PATH}")
        logging.info(f"🤖 IA: OpenRouter ({OPENROUTER_MODEL})")
        logging.info("✅ En attente de connexions...")
        
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="job-automation-mcp",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    )
                )
            )
    except Exception as e:
        logging.error(f"❌ ERREUR: {e}")
        import traceback
        logging.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    try:
        logging.info("Démarrage du serveur MCP...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("👋 Arrêt du serveur")
    except Exception as e:
        logging.error(f"❌ Erreur fatale: {e}")
        import traceback
        logging.error(traceback.format_exc())
