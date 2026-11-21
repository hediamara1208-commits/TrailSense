// [HEDI] Logique de l'interface.
// 1. Démarrer avec fetch('../data/fixtures/sample_snapshot.json') tant que l'API n'est pas prête,
//    puis passer à fetch('/api/snapshot?mode=...&threshold=...').
// 2. Dessiner chaque avion (L.circleMarker) avec une couleur selon assessment.flagged et decision.route.
// 3. Au clic : remplir #panel.
// 4. Rafraîchir toutes les 30 s en mode live ; avancer d'un cycle en mode replay.
// 5. Le curseur de seuil relance /api/snapshot avec le nouveau threshold.
