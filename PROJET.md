# 🎯 Projet MCP Job Automation

## Qu'est-ce que c'est ?
Plateforme automatisée pour chercher, analyser et postuler à des offres d'emploi en utilisant **MCP** (Model Context Protocol) + **IA**.

---

## ✨ Fonctionnalités

### 🔍 **Recherche d'offres**
- Scrape automatiquement **Indeed.com** par mot-clé
- Récupère : titre, entreprise, localisation, type de contrat, description
- Sauvegarde dans `jobs_all.json`

### 🤖 **Analyse IA des offres**
- Résumé intelligent de toutes les offres trouvées
- Identifie : entreprises, compétences demandées, types de contrats
- Détecte les opportunités pour profils juniors

### 📊 **Matching profil-offre**
- Analyse la compatibilité avec votre profil
- Score de matching /10
- Identifie les points forts et manques
- Recommandations personnalisées

### 🏆 **Ranking intelligent**
- Classe les offres par pertinence
- Top N meilleures offres pour votre profil
- Score pour chaque positionnement

### 💌 **Génération de lettres**
- Crée lettres de motivation personnalisées
- 3 tons disponibles : professionnel, enthousiaste, créatif
- 250-300 mots adaptés à l'offre

---

## 🏗️ Architecture

```
N8N Workflow (orchestration)
    ↓ HTTP JSON-RPC
FastAPI Server (port 8001)
    ↓
MCP Server (stdio)
    ├─ search_jobs → IndeedScrap.py
    ├─ get_jobs_summary → OpenRouter IA
    ├─ analyze_job_match → OpenRouter IA
    ├─ get_best_matches → OpenRouter IA
    └─ generate_cover_letter → OpenRouter IA
```

---

## 🚀 Technos utilisées

- **MCP** : Protocol pour exposer les outils à l'IA
- **OpenRouter** : Accès aux modèles IA (Deepseek, GPT, etc.)
- **BeautifulSoup4** : Web scraping
- **FastAPI** : HTTP wrapper
- **N8N** : Orchestration des workflows
- **Python 3.11** : Runtime

---

## 📋 Outils disponibles

| Outil | Description |
|-------|-------------|
| `search_jobs` | Scrape Indeed et retourne les offres |
| `get_jobs_summary` | Analyse globale du marché job |
| `analyze_job_match` | Score de compatibilité pour une offre |
| `get_best_matches` | Top 5 meilleures offres |
| `generate_cover_letter` | Lettre de motivation personnalisée |

---

## 🎬 Workflow exemple

1. **Trigger** : "Cherche des offres Python"
2. **Scrape** : 15 offres trouvées sur Indeed
3. **Analyse** : IA identifie 3 offres pertinentes pour profil junior
4. **Scoring** : Job #5 = 8/10 de match
5. **Lettre** : Génère candidature personnalisée en 30 secondes

---

## 💰 Coûts

- **Hosting** : Gratuit (local ou petit serveur)
- **IA** : Gratuit (OpenRouter tier free) ou ~$0.01 par requête (tier payant)
- **Indeed** : Gratuit (scraping public)

---

## 🎯 Cas d'usage

✅ Jeune diplômé cherchant son premier CDI  
✅ Alternant en recherche de stage  
✅ Dev cherchant à changer de job  
✅ Automatisation des candidatures en masse  
✅ Analyse du marché job pour une région/compétence  

---

## 📊 Résultats actuels

- ✅ 15 offres trouvées (test "Java")
- ✅ Analyse détaillée en 5 secondes
- ✅ Score de matching précis
- ✅ Lettres en français naturel

---

## 🔧 Comment utiliser

```bash
# Lancer le serveur MCP
python mcp_http_server.py

# Ou directement le serveur stdio
python server.py

# Ou via n8n workflow
# (configuration dans pipeline.json)
```

---

## 🚦 Prochaines étapes

- [ ] Élargir à d'autres sites (LinkedIn, Glassdoor)
- [ ] Ajouter application automatique
- [ ] Dashboard pour suivre candidatures
- [ ] CV parsing pour meilleur matching
- [ ] Notifications par email/SMS

---

**Créé par** : Safaa  
**Stack** : MCP + IA + Automation  
**Status** : 🟢 Fonctionnel
