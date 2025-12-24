# Projet Évaporation-Cristallisation du Saccharose

[![CI/CD Pipeline](https://github.com/VOTRE-USERNAME/Projet_evaporation_cristallisation_PIC11/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/VOTRE-USERNAME/Projet_evaporation_cristallisation_PIC11/actions)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://hub.docker.com)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-green?logo=python)](https://www.python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red?logo=streamlit)](https://streamlit.io)

## 📋 Description

Simulation complète d'un procédé industriel de concentration et cristallisation du saccharose par évaporation multi-effets. Le projet combine :
- 🔥 Modélisation thermodynamique rigoureuse (CoolProp + thermo)
- ❄️ Simulation de cinétique de cristallisation
- ⚡ Optimisation énergétique
- 💰 Analyse technico-économique (contexte marocain)
- 🌐 Interface web interactive Streamlit avec design moderne
- 🐳 **Dockerisation complète**
- 🔄 **CI/CD automatisé avec GitHub Actions**


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

## 📂 Structure du Projet

```
Projet_evaporation_cristallisation_PIC11/
├── .github/
│   └── workflows/
│       └── ci-cd.yml              # Pipeline CI/CD GitHub Actions
├── assets/
│   └── custom_style.css           # CSS personnalisé (Design DistillSim)
├── modules/
│   ├── thermodynamique.py         # Propriétés thermodynamiques (CoolProp + thermo)
│   ├── evaporateurs.py            # Simulation évaporateurs multi-effets
│   ├── cristallisation.py         # Cinétique et bilan de population
│   ├── optimisation.py            # Analyses paramétriques et économiques
│   └── main.py                    # Script principal
├── tests/
│   ├── test_thermodynamique.py
│   ├── test_evaporateurs.py
│   └── test_cristallisation.py
├── resultats/
│   └── graphiques/                # Graphiques générés
├── app.py                         # Interface web Streamlit
├── Dockerfile                     # 🐳 Configuration Docker
├── docker-compose.yml             # 🐳 Orchestration Docker Compose
├── .dockerignore                  # Fichiers exclus du build Docker
├── requirements.txt
├── .gitignore
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
- **Page Accueil** : Présentation du projet et vue d'ensemble
- **Page Évaporateurs** : Simulation interactive avec ajustement des paramètres
- **Page Cristallisation** : Comparaison des profils de refroidissement
- **Page Économique** : Calculs de coûts et ROI en temps réel

### 🐳 Mode Docker (Recommandé pour Production)

#### Option 1: Docker seul

```bash
# Build de l'image
docker build -t evaporation-pic11 .

# Run du container
docker run -d -p 8501:8501 evaporation-pic11

# Accéder à l'application
# http://localhost:8501
```

#### Option 2: Docker Compose (Recommandé)

```bash
# Lancer l'application
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Arrêter l'application
docker-compose down
```

#### Pull depuis Docker Hub (si publié)

```bash
docker pull VOTRE-USERNAME/evaporation-cristallisation-pic11:latest
docker run -d -p 8501:8501 VOTRE-USERNAME/evaporation-cristallisation-pic11:latest
```

## 🔄 DevOps et CI/CD

Le projet utilise **GitHub Actions** pour l'intégration et le déploiement continus :

### Workflow Automatisé

À chaque push sur `main` ou `develop`, le pipeline CI/CD :

1. **Tests et Validation** ✅
   - Linting du code (flake8)
   - Validation des imports de modules
   - Tests unitaires (si présents)

2. **Build Docker** 🐳
   - Construction de l'image Docker
   - Push vers Docker Hub (avec tags: `latest`, `SHA`)
   - Cache optimisé pour builds rapides

3. **Tests Container** 🧪
   - Lancement d'un container de test
   - Healthcheck automatique
   - Validation du endpoint Streamlit

### Configuration des Secrets GitHub

Pour activer le push vers Docker Hub, ajoutez ces secrets dans GitHub:
- `DOCKER_USERNAME`: Votre nom d'utilisateur Docker Hub
- `DOCKER_TOKEN`: Token d'accès Docker Hub

**Créer un token Docker** :
1. Aller sur https://hub.docker.com/settings/security
2. "New Access Token"
3. Copier le token et l'ajouter dans GitHub Secrets


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

TEAM:
OUMOULID LAHCEN
BARRY OUMOUR


