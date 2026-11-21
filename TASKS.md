# Répartition des tâches : Hedi et Dawud

**Principe :** chacun possède ses modules, mais **chacun doit pouvoir expliquer ceux de l'autre** au jury (le Q&A juge toute l'équipe). À chaque point de synchro, on se présente mutuellement ce qu'on a fait en 5 minutes.

## Hedi : « la science et les données »
**Objectif :** des avions réels, une météo réelle, un risque de contrail correct et défendable, et la preuve chiffrée de frugalité.

- [ ] **H1 · Ven soir (urgent)** `sources/opensky.py` : avions en croisière au-dessus du Québec.
- [ ] **H2 · Ven soir (urgent)** `sources/recorder.py` : lancer l'enregistrement du ciel de nuit (toute la nuit si possible).
- [ ] **H3 · Ven soir / sam matin** `sources/weather.py` : profil Open-Meteo + cache. Vérifier la convention de l'humidité.
- [ ] **H4 · Sam matin** `physics/contrails.py` : RHi, SAC, interpolation, jour/nuit, `assess()` + `tests/test_physics.py`.
- [ ] **H5 · Sam midi** `physics/fuel.py` + `docs/hypotheses.md`.
- [ ] **H6 · Sam après-midi** `benchmark/all_llm.py` : notre cascade contre le tout-LLM sur le même cycle.
- [ ] **H7 · Sam soir** Pitch : texte de 2 min 30, les 3 chiffres (35 %, 11,6 %, ratio du benchmark), sources.

## Dawud : « l'agent et le produit »
**Objectif :** un agent qui décide vite et bien avec Jev, n'appelle le LLM que quand ça vaut le coût, et une interface claire pour la démo.

- [ ] **D1 · Ven soir** Créer la clé Jev, tester les 4 questions dans le playground (console.typesafe.ai/playground) avec le vol exemple du fichier fixture.
- [ ] **D2 · Ven soir** `api.py` qui renvoie le fichier fixture + `frontend/` : carte Leaflet avec les 3 avions de l'exemple.
- [ ] **D3 · Sam matin** `agent/jev.py` : `build_state()` + `decide()` avec le seuil. Tester l'appel groupé (plusieurs vols par requête).
- [ ] **D4 · Sam midi** `agent/writer.py` : gabarit + LLM pour les 2-3 vols clés + EcoLogits.
- [ ] **D5 · Sam après-midi** `agent/pipeline.py` : brancher les modules de Hedi, remplir le `Receipt`.
- [ ] **D6 · Sam soir** Interface finale : fiche vol, curseur de seuil, bascule Replay/Live, reçu, bouton benchmark.
- [ ] **D7 · Dim matin** Vidéo de secours de la démo.

## Points de synchro (15 min chacun)
| Quand | Ce qui doit marcher |
|---|---|
| **Ven 23 h 30** | `models.py` validé à deux. Hedi : vrais avions affichés en console + enregistrement lancé. Dawud : la carte affiche le fichier exemple. |
| **Sam 12 h** | Hedi : `assess()` marche sur des données réelles. Dawud : Jev décide sur le fichier exemple. |
| **Sam 18 h** | **Intégration de bout en bout** en mode Replay. |
| **Sam 23 h** | Benchmark + reçu dans l'interface. Première répétition du pitch. |
| **Dim 9 h** | **Gel des fonctionnalités.** Seulement des corrections et la répétition. |
| **Dim 10-11 h** | Check-in d'équipe obligatoire (CodeJam). |
| **Dim 11 h 30** | Repo public, README avec GIF, dernier commit. |
| **Dim 12 h** | Fin des modifications (règle CodeJam). |

## Règles de travail
- Une branche par personne (`hedi/...`, `dawud/...`), on fusionne dans `main` aux points de synchro.
- Petits commits fréquents (ils prouvent qu'on a codé pendant le hackathon).
- Jamais de clé API dans le code : tout dans `.env`.
