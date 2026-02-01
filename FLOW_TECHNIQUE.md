# 🔄 Comment marche le pipeline IA

## Flux complet

```
1. SCRAPE (search_jobs)
   └─→ Indeed → jobs_all.json (15 offres)

2. ANALYSE GLOBALE (get_jobs_summary) ⭐ POUR LA PRÉSENTATION
   └─→ "Voici les 15 offres analysées"
       - Top 5 entreprises
       - Compétences demandées
       - Types de contrats
       - Opportunités juniors
       ✅ Réponse générée par OpenRouter

3. MATCHING INDIVIDUEL (analyze_job_match)
   └─→ Offre #X vs Profil Safaa
       - Score /10
       - Points forts
       - Manques
       - Recommandations
       ✅ Réponse générée par OpenRouter

4. RANKING (get_best_matches)
   └─→ "Top 5 meilleures pour toi"
       - Index de l'offre
       - Raison
       - Score/10
       ✅ Réponse générée par OpenRouter

5. LETTRE (generate_cover_letter)
   └─→ Pour offre #X
       - 250-300 mots
       - Ton : professionnel/enthousiaste/créatif
       - En français
       ✅ Réponse générée par OpenRouter
```

---

## Détail technique

### 🟢 get_jobs_summary (CE QU'IL FAUT RETENIR)

**Input** :
```json
{
  // Vide - il charge jobs_all.json lui-même
}
```

**Process** :
1. Charge `jobs_all.json` (les 15 offres)
2. Formate les offres en JSON (titre, entreprise, contrat, lieu)
3. Crée un prompt : "Analyse ces 15 offres d'emploi"
4. Envoie à OpenRouter (Deepseek-R1)
5. Reçoit analyse structurée

**Output** :
```
✅ Nombre total d'offres
✅ Top 5 entreprises
✅ Types de contrats
✅ Compétences demandées
✅ Opportunités pour junior
```

---

### 🟢 analyze_job_match

**Input** :
```json
{
  "job_index": 0  // Quel job analyser (0 = premier)
}
```

**Process** :
1. Récupère l'offre #0 depuis jobs_all.json
2. Charge le profil Safaa (skills, expérience, etc.)
3. Crée prompt : "Compare le profil à cette offre"
4. Envoie à OpenRouter
5. Reçoit score et analyse

**Output** :
```
Score: 8/10
Points forts: Python, Docker, Automation
Manques: 5 ans expérience demandée
Recommandation: Postuler - profil prometteur
```

---

### 🟢 get_best_matches

**Input** :
```json
{
  "top_n": 5  // Combien de suggestions
}
```

**Process** :
1. Charge les 20 premières offres
2. Crée prompt : "Classe ces 20 offres par pertinence"
3. Envoie profil + offres à OpenRouter
4. L'IA les range par score de match
5. Retourne top 5

**Output** :
```
1. Job #7 (MBDA) - 9/10 - Cherche Senior Java
2. Job #3 (BluTech) - 8/10 - Python/Docker
3. Job #12 (Structure) - 8/10 - Junior friendly
...
```

---

### 🟢 generate_cover_letter

**Input** :
```json
{
  "job_index": 0,
  "tone": "professionnel"  // ou "enthousiaste" ou "créatif"
}
```

**Process** :
1. Récupère offre #0
2. Charge profil Safaa
3. Crée prompt : "Écris une lettre 250-300 mots"
4. Envoie à OpenRouter avec ton spécifié
5. Reçoit lettre complète

**Output** :
```
Madame, Monsieur,

Je suis vivement intéressé par le poste de...
[250-300 mots en français naturel]

Cordialement,
Safaa
```

---

## ✅ État actuel : FONCTIONNEL

✅ **Test réussi** : get_jobs_summary fonctionne parfaitement
- 15 offres analysées
- Analyse détaillée en français
- Réponse en ~5 secondes
- Format lisible

✅ **Autres outils** : Même architecture, doivent fonctionner

---

## 🎯 POUR LA PRÉSENTATION

**Utiliser get_jobs_summary** :
1. Scrape 15 offres avec search_jobs
2. Lance get_jobs_summary (analyse IA)
3. Affiche les résultats
4. Montre comment ça classe les opportunités

**Timeline** :
- Scrape: 1-2 minutes (premier appel)
- Analyse IA: 5-10 secondes
- Total: ~2 minutes pour présentation live

---

## 🔗 Dépendances

```
search_jobs
    ↓
    jobs_all.json (créé)
    ↓
    get_jobs_summary    ✅ Utilise jobs_all.json
    analyze_job_match   ✅ Utilise jobs_all.json
    get_best_matches    ✅ Utilise jobs_all.json
    generate_cover_letter ✅ Utilise jobs_all.json
```

**Important** : Pour que les autres tools marchent, `jobs_all.json` doit exister → d'abord lancer `search_jobs`

---

## 🚨 Pièges à éviter

❌ Appeler analyze_job_match sans lancer search_jobs avant (jobs_all.json n'existe pas)  
❌ Utiliser job_index hors limites (ex: index 20 s'il n'y a que 15 offres)  
✅ Toujours lancer search_jobs en premier  
✅ Vérifier jobs_all.json existe avant tests

