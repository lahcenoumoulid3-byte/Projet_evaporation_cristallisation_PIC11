# Projet Évaporation-Cristallisation du Saccharose

## Description

Simulation complète d'un procédé industriel de concentration et cristallisation du saccharose par évaporation multi-effets. Le projet combine :
- Modélisation thermodynamique rigoureuse (CoolProp + thermo)
- Simulation de cinétique de cristallisation
- Optimisation énergétique
- Analyse technico-économique
- Interface web interactive Streamlit

## Installation

### 1. Créer un environnement virtuel (recommandé)

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

**Note** : L'installation de CoolProp peut prendre quelques minutes.

## Structure du Projet

```
Projet_evaporation_cristallisation_PIC11/
├── modules/
│   ├── thermodynamique.py      # Propriétés thermodynamiques (CoolProp + thermo)
│   ├── evaporateurs.py         # Simulation évaporateurs multi-effets
│   ├── cristallisation.py      # Cinétique et bilan de population
│   ├── optimisation.py         # Analyses paramétriques et économiques
│   └── main.py                 # Script principal
├── tests/
│   ├── test_thermodynamique.py
│   ├── test_evaporateurs.py
│   └── test_cristallisation.py
├── resultats/
│   └── graphiques/             # Graphiques générés
├── app.py                      # Interface web Streamlit
├── requirements.txt
└── README.md
```

## Utilisation

### Mode Console (Script Principal)

Exécuter toutes les simulations et générer les résultats :

```bash
python modules/main.py
```

Les résultats seront sauvegardés dans `resultats/` :
- Graphiques au format PNG et PDF
- Données au format Excel
- Tableaux de synthèse

### Mode Interface Web (Streamlit)

Lancer l'application web interactive :

```bash
streamlit run app.py
```

L'application s'ouvrira automatiquement dans votre navigateur à l'adresse `http://localhost:8501`

**Fonctionnalités de l'interface web** :
- **Page Évaporateurs** : Simulation interactive avec ajustement des paramètres
- **Page Cristallisation** : Comparaison des profils de refroidissement
- **Page Optimisation** : Analyses de sensibilité dynamiques
- **Page Économique** : Calculs de coûts et ROI en temps réel

## Tests

Exécuter les tests unitaires :

```bash
pytest tests/ -v
```

Avec couverture de code :

```bash
pytest tests/ --cov=code --cov-report=html
```

## Modules Principaux

### thermodynamique.py
- Calcul des propriétés eau/vapeur avec CoolProp
- Corrélation de Dühring pour l'EPE du saccharose
- Solubilité du saccharose en fonction de la température

### evaporateurs.py
- Bilans matière et énergie pour évaporateurs multi-effets
- Calcul des coefficients de transfert thermique
- Optimisation du nombre d'effets (2-5)
- Économie de vapeur

### cristallisation.py
- Cinétique de nucléation et croissance
- Résolution du bilan de population
- Profils de refroidissement (linéaire, exponentiel, optimal)
- Distribution de taille des cristaux

### optimisation.py
- Analyses de sensibilité paramétriques
- Intégration énergétique (pinch analysis)
- Analyse technico-économique (TCI, OPEX, ROI)

## Données du Procédé

### Évaporateurs
- Alimentation : 10 000 kg/h de jus à 15% saccharose, 85°C
- Concentration finale : 65% saccharose
- Vapeur de chauffe : 3.5 bar (abs), surchauffe 10°C
- Pression condenseur : 0.15 bar (abs)
- Coefficients de transfert estimés : U₁=2500, U₂=2200, U₃=1800 W/m²·K

### Cristallisation
- Batch de 5000 kg de sirop à 70°C
- Refroidissement à 35°C sur 4 heures
- Cinétique : kb=1.5×10¹⁰, kg=2.8×10⁻⁷, Eg=45 kJ/mol

## Références

- Perry's Chemical Engineers' Handbook (8th ed.) - Chapitres 11 et 18
- Mullin, J.W. "Crystallization" (4th ed.)
- Documentation CoolProp : http://www.coolprop.org
- Documentation thermo : https://thermo.readthedocs.io

## Auteurs

Projet académique - PIC11

## Date de Rendu

15/12/2025
