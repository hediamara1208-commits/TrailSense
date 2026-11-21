"""[HEDI] Tests de la physique : ce qu'on doit pouvoir défendre devant le jury.

Cas à écrire (valeurs de référence à vérifier dans la littérature) :
- rh_ice > rh_water quand T < 0 °C (la glace sature avant l'eau).
- À -60 °C et 250 hPa avec air humide : SAC rempli.
- À -30 °C : SAC non rempli (trop chaud à cette pression).
- assess() : un avion dans une couche RHi 120 % est flagged ; RHi 60 % ne l'est pas.
"""
