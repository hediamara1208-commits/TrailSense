# ContrailWatch

**McGill CodeJam 16 (20-22 nov. 2026) · piste visée : Agent Solution**

Un agent IA frugal qui aide les régulateurs de vol à éviter les traînées de condensation (contrails) qui réchauffent le climat. Il trouve en quelques millisecondes les rares vols concernés et propose de monter ou descendre de 2 000 ft, avec beaucoup moins de calcul qu'un agent classique (ratio mesuré par notre benchmark).

## Pourquoi
- Les contrails représentent environ 35 % de l'impact réchauffant de l'aviation (GIEC 2022), et une petite minorité de vols en est responsable.
- Les éviter marche sur les vols qui suivent le plan (−54 % lors d'essais Google / American Airlines), mais l'adoption reste faible en opérations réelles (−11,6 % en intention de traiter, essai 2026).
- Analyser chaque vol avec un gros LLM serait lent, cher et polluant.

## Comment : penser vite, puis lentement
1. **Physique (gratuit) :** critère de Schmidt-Appleman + sursaturation en glace, au niveau actuel et à ±2 000 ft.
2. **Jev (Système 1) :** décision typée et calibrée pour les vols signalés, avec un seuil d'autonomie.
3. **Rédaction en cascade (Système 2) :** gabarit gratuit, puis IBM Granite en local, puis Cloud LLM seulement pour les 1-2 avis clés.
4. **Reçu de calcul** et **benchmark** contre un agent tout-LLM.

Voir [`ARCHITECTURE.md`](ARCHITECTURE.md) et [`TASKS.md`](TASKS.md).

## Démarrer
```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn backend.api:app --reload
```

## Équipe
Hedi Amara · Dawud
