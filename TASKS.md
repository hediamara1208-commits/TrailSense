# Répartition des tâches : Dawud et Hedi

**Principe :** chacun possède ses modules, mais **chacun doit pouvoir expliquer ceux de l'autre** au jury (le Q&A juge toute l'équipe). À chaque point de synchro, on se présente mutuellement ce qu'on a fait en 5 minutes.

*Version 3 (ven 23 h 05) : ajout de l'étage Granite local et des outils du hackathon (Cloud LLM Builder Club, 1Password). Version 2 (ven 22 h 45) : rôles inversés, le benchmark rejoint la partie LLM, ajout d'un plan B sans Jev, limites d'appels pour l'enregistrement, pitch partagé, repo public à 11 h.*

## Dawud : « la science et les données » (chemin critique)
**Objectif :** des avions réels, une météo réelle, un risque de contrail correct et défendable. C'est la partie la plus risquée : Dawud s'y concentre, sans autre tâche.

- [ ] **D1 · Ven soir (urgent)** `sources/opensky.py` : avions en croisière au-dessus du Québec.
- [ ] **D2 · Ven soir (urgent)** `sources/recorder.py` : lancer l'enregistrement de nuit. **Avions toutes les 2-5 min (`RECORD_S`), avec un compte OpenSky gratuit, météo toutes les heures** : ne pas épuiser les crédits OpenSky.
- [ ] **D3 · Ven soir / sam matin** `sources/weather.py` : profil Open-Meteo + cache. Vérifier la convention de l'humidité.
- [ ] **D4 · Sam matin** `physics/contrails.py` : RHi, critère de Schmidt-Appleman, interpolation, jour/nuit, `assess()` + `tests/test_physics.py`.
- [ ] **D5 · Sam après-midi (après 12 h)** `physics/fuel.py` + `docs/hypotheses.md`.
- [ ] **D6 · Sam soir** Pitch, partie scientifique : la diapositive physique et les réponses du Q&A sur la physique.

**Règle de repli à 12 h samedi :** si la physique n'est pas prête sur de vraies données, on garde **critère de Schmidt-Appleman + RHi seuls, sans carburant**, et on ajoute le carburant à 18 h.

## Hedi : « l'agent, les LLM et le produit »
**Objectif :** un agent qui décide vite et bien avec Jev, n'appelle le LLM que quand ça vaut le coût, prouve sa frugalité, et une interface claire.

- [ ] **H0 · Ven soir** Demander les crédits API Cloud LLM au Cloud LLM Builder Club McGill. Créer un coffre 1Password partagé avec Dawud pour les clés (Jev, provider, OpenSky).
- [ ] **H1 · Ven soir** Créer la clé Jev, tester les 4 questions dans le playground (console.typesafe.ai/playground) avec le vol exemple de la fixture.
- [ ] **H2 · Ven soir** `api.py` qui renvoie la fixture + `frontend/` : carte Leaflet avec les 3 avions de l'exemple.
- [ ] **H3 · Sam matin** `agent/jev.py` : `build_state()` + `decide()` avec le seuil. Tester l'appel groupé.
- [ ] **H4 · Sam matin** `agent/fallback.py` : **plan B sans Jev** (règle codée en dur, même sortie que `decide()`).
- [ ] **H5 · Sam midi** `agent/writer.py` : gabarit + Cloud LLM pour les 1-2 vols clés + EcoLogits.
- [ ] **H5b · Sam après-midi (optionnel)** Étage **Granite local** : installer Ollama, `ollama pull` du modèle Granite, `granite_advisory()`, mesure Wh locale. **Coupure : si ça ne marche pas à 15 h samedi, `USE_GRANITE = False` et on n'y touche plus.**
- [ ] **H6 · Sam après-midi** `agent/pipeline.py` : brancher les modules de Dawud, remplir le `Receipt`.
- [ ] **H7 · Sam après-midi** `benchmark/all_llm.py` : cascade contre tout-LLM, **limité à ~20 vols** de l'enregistrement.
- [ ] **H8 · Sam soir** Interface finale : fiche vol, curseur de seuil, bascule Replay/Live, reçu, bouton benchmark.
- [ ] **H9 · Dim matin** Vidéo de secours + README de remise (GIF, instructions, sources).

## Pitch : partagé
- **Hedi :** l'histoire (accroche, Sophie, Système 1 / Système 2), la démo, le reçu et le benchmark.
- **Dawud :** la physique en 30 secondes, et les questions du jury sur la science.
- Les deux répètent ensemble samedi 23 h et dimanche 9 h.

## Points de synchro (15 min chacun)
| Quand | Ce qui doit marcher |
|---|---|
| **Ven 23 h 30** | `models.py` validé à deux. Dawud : vrais avions en console + enregistrement lancé. Hedi : la carte affiche la fixture. |
| **Sam 12 h** | Dawud : `assess()` sur données réelles (sinon : règle de repli ci-dessus). Hedi : Jev **et** le plan B décident sur la fixture. |
| **Sam 18 h** | **Intégration de bout en bout** en mode Replay. Carburant ajouté si repli à midi. |
| **Sam 23 h** | Benchmark + reçu dans l'interface. Première répétition du pitch. |
| **Dim 9 h** | **Gel des fonctionnalités.** Seulement des corrections et la répétition. |
| **Dim 10-11 h** | Check-in d'équipe obligatoire (CodeJam). |
| **Dim 11 h** | Repo à jour (public), README avec GIF, dernier commit. Marge si GitHub ou la remise posent problème. |
| **Dim 12 h** | Fin des modifications (règle CodeJam). |

## Règles de travail
- Une branche par personne (`dawud/...`, `hedi/...`), on fusionne dans `main` aux points de synchro.
- Petits commits fréquents (ils prouvent qu'on a codé pendant le hackathon).
- Jamais de clé API dans le code : tout dans `.env` ou dans 1Password (`op run --env-file=.env -- uvicorn backend.api:app`). **Le repo est public** : vérifier avant chaque push.
