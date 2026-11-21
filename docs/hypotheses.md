# Hypothèses physiques de ContrailWatch

Toutes les valeurs sont réglables dans `backend/config.py`. Ce qui est **à vérifier** est marqué ⚠️.

## Données
| Sujet | Choix | Pourquoi |
|---|---|---|
| Avions | OpenSky, FL290-410, \|vitesse verticale\| ≤ 2,5 m/s | On ne conseille que des avions en palier de croisière. |
| Météo | Open-Meteo GFS, niveaux 350 → 150 hPa | Encadre FL265 à FL450. Interpolation linéaire en ln(p). |
| Niveau de vol → pression | Atmosphère standard ISA | Un FL est une altitude-pression (calage 1013,25 hPa). FL350 = 238,4 hPa. |
| Convention d'humidité | `RH_CONVENTION = "ice"` ⚠️ | Premier enregistrement : RH = 100 % pile à −49,5 °C. Si c'était /eau, cela ferait ~155 % /glace, au-delà du seuil de congélation homogène (~145-150 %) : irréaliste. À confirmer sur la distribution de la nuit (valeurs qui s'empilent sous 100 % sans jamais le dépasser = /glace plafonnée). |

## Formation : critère de Schmidt-Appleman (Schumann, 1996)
- Pente de mélange G = EI_H2O · cp · p / (ε · Q · (1 − η)), avec EI_H2O = 1,23, cp = 1004 J/kg/K, ε = 0,622, Q = 43,2 MJ/kg, **η = 0,35** (moteurs modernes : 0,3 à 0,4).
- Seuil sec T_LM = −46,46 + 9,43 ln(G − 0,053) + 0,720 ln²(G − 0,053) (°C, G en Pa/K) → environ −41 °C à 250 hPa.
- Le contrail se forme si T < T_LM et e_amb ≥ e_sat,eau(T_LM) − G (T_LM − T).
- Pressions de saturation : Sonntag (1994).

## Persistance
- RHi ≥ **95 %** (`RHI_THRESHOLD`) ⚠️ C'est un **choix de réglage** : GFS plafonne l'humidité à 100 % et sous-estime la sursaturation, connue pour être mal représentée dans les modèles (pycontrails applique aussi une correction d'humidité). Le seuil change le nombre de vols signalés : à dire au jury.
- Longueur traversée : **150 km** (`ISSR_TYPICAL_KM`), longueur moyenne d'une zone sursaturée le long des routes (Gierens & Spichtinger, 2000). On n'a qu'un profil par avion, donc pas l'étendue réelle.

## Carburant
- Type d'avion inconnu → consommation générique **3 000 kg/h**.
- Surconsommation pendant la déviation : **+1,5 % en montée, +2 % en descente** (ordre de grandeur de l'essai Google / American Airlines 2023 : ~2 % sur les vols déviés).
- **3,16 kg de CO₂ par kg** de kérosène.

## Réchauffement évité ⚠️ (l'estimation la plus incertaine)
- Réchauffement d'un contrail persistant : **100 kg CO2e/km la nuit, 40 kg CO2e/km le jour** (horizon 100 ans), avec une fourchette ×/÷ 3 affichée.
- Nuit = soleil sous l'horizon : le contrail ne fait que piéger la chaleur infrarouge. Le jour, il réfléchit aussi du soleil, ce qui compense en partie.
- Ces facteurs sont des ordres de grandeur, pas une mesure. **À sourcer ou calibrer** (par ex. sur des sorties CoCiP de pycontrails) avant d'être cités comme chiffres.
- Robustesse : pour un avion à 500 kt, 150 km de zone sursaturée = 18 min, soit ~13 kg de carburant en plus (~42 kg CO₂) contre ~15 t CO2e évitées la nuit. Le bilan reste largement positif même avec un facteur divisé par 100, ce qui est cohérent avec Teoh et al. (2020) : ~59 % de forçage des contrails évité pour ~0,014 % de carburant en plus.

## Ce qu'on ne modélise pas
Le trafic réel et l'accord du contrôle aérien (l'outil est une aide à la décision pour le régulateur), le vent, le type d'avion, l'étendue réelle de la zone sursaturée, et l'effet radiatif détaillé (CoCiP).
