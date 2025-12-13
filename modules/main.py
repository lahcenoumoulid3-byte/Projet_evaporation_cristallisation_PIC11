"""
Script principal main.py
========================

Script principal pour exécuter toutes les simulations du projet
d'évaporation-cristallisation du saccharose.

Auteur: Projet PIC11
Date: 2025
"""

import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Ajouter le dossier modules au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Imports des modules du projet
import thermodynamique as thermo
from evaporateurs import EvaporateurMultiEffets
from cristallisation import (
    CinetiqueCristallisation, BilanPopulation,
    dimensionner_cristalliseur
)
from optimisation import (
    AnalyseSensibilite, OptimisationNombreEffets,
    AnalyseEconomique, IntegrationEnergetique
)


def print_header(titre: str):
    """Affiche un en-tête formaté."""
    print("\n" + "="*80)
    print(f"  {titre}")
    print("="*80 + "\n")


def simulation_evaporateurs():
    """Simule les évaporateurs multi-effets."""
    print_header("PARTIE 1: SIMULATION ÉVAPORATEURS MULTI-EFFETS")
    
    # Paramètres du procédé
    params = {
        'debit_alimentation': 10000,  # kg/h
        'concentration_alimentation': 15,  # %
        'concentration_finale': 65,  # %
        'temperature_alimentation_celsius': 85,  # °C
        'pression_vapeur': 3.5e5,  # 3.5 bar
        'pression_condenseur': 0.15e5,  # 0.15 bar
    }
    
    resultats_configs = []
    
    # Simulation pour 2, 3, 4, 5 effets
    for n_effets in [2, 3, 4, 5]:
        print(f"\n--- Simulation avec {n_effets} effets ---")
        
        evap = EvaporateurMultiEffets(n_effets)
        res = evap.simuler(**params)
        evap.afficher_resultats()
        
        resultats_configs.append({
            'nombre_effets': n_effets,
            'economie_vapeur': res['economie_vapeur'],
            'surface_totale': res['surface_totale'],
            'consommation_vapeur': res['consommation_vapeur_kg_h'],
            'consommation_specifique': res['consommation_specifique']
        })
    
    # Tableau comparatif
    df_configs = pd.DataFrame(resultats_configs)
    print("\n--- COMPARAISON DES CONFIGURATIONS ---")
    print(df_configs.to_string(index=False))
    
    # Sauvegarder
    df_configs.to_excel('resultats/comparaison_effets.xlsx', index=False)
    print("\nRésultats sauvegardés dans: resultats/comparaison_effets.xlsx")
    
    return df_configs


def analyse_sensibilite_evaporateurs():
    """Effectue l'analyse de sensibilité pour les évaporateurs."""
    print_header("ANALYSE DE SENSIBILITÉ - ÉVAPORATEURS")
    
    # Fonction de simulation wrapper
    def simuler_evap(**kwargs):
        n_effets = kwargs.get('nombre_effets', 3)
        evap = EvaporateurMultiEffets(n_effets)
        return evap.simuler(**kwargs)
    
    # Paramètres de base
    params_base = {
        'nombre_effets': 3,
        'debit_alimentation': 10000,
        'concentration_alimentation': 15,
        'concentration_finale': 65,
        'temperature_alimentation_celsius': 85,
        'pression_vapeur': 3.5e5,
        'pression_condenseur': 0.15e5,
    }
    
    # Créer l'analyseur
    analyseur = AnalyseSensibilite(simuler_evap)
    
    # Effectuer les analyses
    analyses = analyseur.analyse_complete_evaporateurs(params_base)
    
    # Générer les graphiques
    analyseur.generer_graphiques_sensibilite(analyses)
    
    # Sauvegarder les données
    for param, df in analyses.items():
        nom_fichier = f'resultats/sensibilite_{param}.xlsx'
        df.to_excel(nom_fichier, index=False)
        print(f"Données sauvegardées: {nom_fichier}")
    
    return analyses


def simulation_cristallisation():
    """Simule la cristallisation batch."""
    print_header("PARTIE 2: SIMULATION CRISTALLISATION BATCH")
    
    # Paramètres
    T0 = 70  # °C
    Tf = 35  # °C
    concentration_initiale = 65  # g/100g
    volume_batch = 10  # m³
    duree = 4  # heures
    
    # Créer le simulateur
    cinetique = CinetiqueCristallisation()
    bilan_pop = BilanPopulation(cinetique)
    
    resultats_profils = []
    
    # Simuler les 3 profils
    for profil in ['lineaire', 'exponentiel', 'optimal']:
        print(f"\n--- Profil de refroidissement: {profil} ---")
        
        try:
            res = bilan_pop.resoudre_batch(
                T0, Tf, concentration_initiale, volume_batch,
                duree, profil=profil, n_classes=50
            )
            
            print(f"  Température finale: {res['temperature_finale']:.2f} °C")
            print(f"  Concentration finale: {res['concentration_finale']:.2f} g/100g")
            print(f"  L50 (médiane): {res['L50']:.2f} μm")
            print(f"  L moyen: {res['L_moyen']:.2f} μm")
            print(f"  CV: {res['CV']:.3f}")
            print(f"  Rendement: {res['rendement']:.2f} %")
            
            resultats_profils.append({
                'profil': profil,
                'L50': res['L50'],
                'L_moyen': res['L_moyen'],
                'CV': res['CV'],
                'rendement': res['rendement'],
                'masse_cristaux': res['masse_cristaux']
            })
            
        except Exception as e:
            print(f"  Erreur lors de la simulation: {e}")
    
    # Tableau comparatif
    df_profils = pd.DataFrame(resultats_profils)
    print("\n--- COMPARAISON DES PROFILS DE REFROIDISSEMENT ---")
    print(df_profils.to_string(index=False))
    
    # Sauvegarder
    df_profils.to_excel('resultats/comparaison_profils.xlsx', index=False)
    print("\nRésultats sauvegardés dans: resultats/comparaison_profils.xlsx")
    
    return df_profils


def dimensionnement():
    """Dimensionne le cristalliseur."""
    print_header("DIMENSIONNEMENT DU CRISTALLISEUR")
    
    dim = dimensionner_cristalliseur(
        masse_batch=5000,  # kg
        concentration=65,  # %
        temps_residence=4  # heures
    )
    
    print(f"Volume utile: {dim['volume_utile']:.2f} m³")
    print(f"Volume total (avec sécurité): {dim['volume_total']:.2f} m³")
    print(f"Diamètre: {dim['diametre']:.2f} m")
    print(f"Hauteur: {dim['hauteur']:.2f} m")
    print(f"Puissance d'agitation: {dim['puissance_agitation']/1000:.2f} kW")
    print(f"Surface serpentin: {dim['surface_serpentin']:.2f} m²")
    print(f"Flux de refroidissement: {dim['flux_refroidissement']/1000:.2f} kW")
    
    # Sauvegarder
    df_dim = pd.DataFrame([dim])
    df_dim.to_excel('resultats/dimensionnement_cristalliseur.xlsx', index=False)
    print("\nRésultats sauvegardés dans: resultats/dimensionnement_cristalliseur.xlsx")
    
    return dim


def analyse_economique():
    """Effectue l'analyse technico-économique."""
    print_header("PARTIE 3: ANALYSE TECHNICO-ÉCONOMIQUE")
    
    # Données pour 3 effets (configuration optimale)
    surfaces_evap = [100, 85, 70]  # m² (estimations)
    volume_crist = 10  # m³
    
    # Analyse économique
    eco = AnalyseEconomique()
    
    # Investissement
    inv = eco.calculer_investissement(surfaces_evap, volume_crist)
    
    print("--- COÛTS D'INVESTISSEMENT ---")
    print(f"Évaporateurs: {inv.evaporateurs/1000:.2f} k€")
    print(f"Cristalliseur: {inv.cristalliseur/1000:.2f} k€")
    print(f"Échangeurs: {inv.echangeurs/1000:.2f} k€")
    print(f"TOTAL (TCI): {inv.total/1000:.2f} k€")
    
    # Exploitation
    opex = eco.calculer_exploitation(
        consommation_vapeur_kg_h=2000,
        consommation_eau_m3_h=50,
        puissance_electrique_kW=150,
        nombre_operateurs=2,
        heures_operation_an=8000
    )
    
    print("\n--- COÛTS D'EXPLOITATION ANNUELS ---")
    print(f"Vapeur: {opex.vapeur/1000:.2f} k€/an")
    print(f"Eau de refroidissement: {opex.eau_refroidissement/1000:.2f} k€/an")
    print(f"Électricité: {opex.electricite/1000:.2f} k€/an")
    print(f"Main d'œuvre: {opex.main_oeuvre/1000:.2f} k€/an")
    print(f"TOTAL (OPEX): {opex.total/1000:.2f} k€/an")
    
    # ROI
    production_annuelle = 5000  # tonnes
    prix_vente = 800  # €/tonne
    
    roi = eco.calculer_roi(
        investissement=inv.total,
        opex_annuel=opex.total,
        production_annuelle_tonnes=production_annuelle,
        prix_vente_tonne=prix_vente
    )
    
    print("\n--- INDICATEURS ÉCONOMIQUES ---")
    print(f"Production annuelle: {production_annuelle} tonnes")
    print(f"Revenus annuels: {roi['revenus_annuels']/1000:.2f} k€/an")
    print(f"Bénéfice annuel: {roi['benefice_annuel']/1000:.2f} k€/an")
    print(f"Temps de retour: {roi['temps_retour_annees']:.2f} ans")
    print(f"Coût de production: {roi['cout_production_tonne']:.2f} €/tonne")
    print(f"Marge bénéficiaire: {roi['marge_beneficiaire_pct']:.2f} %")
    
    # Sauvegarder
    df_eco = pd.DataFrame([{
        'TCI_k€': inv.total/1000,
        'OPEX_k€_an': opex.total/1000,
        'Revenus_k€_an': roi['revenus_annuels']/1000,
        'Benefice_k€_an': roi['benefice_annuel']/1000,
        'ROI_ans': roi['temps_retour_annees'],
        'Cout_prod_€_tonne': roi['cout_production_tonne'],
        'Marge_%': roi['marge_beneficiaire_pct']
    }])
    df_eco.to_excel('resultats/analyse_economique.xlsx', index=False)
    print("\nRésultats sauvegardés dans: resultats/analyse_economique.xlsx")
    
    return roi


def generer_graphiques_comparatifs():
    """Génère des graphiques comparatifs supplémentaires."""
    print_header("GÉNÉRATION DES GRAPHIQUES COMPARATIFS")
    
    # Charger les données
    try:
        df_effets = pd.read_excel('resultats/comparaison_effets.xlsx')
        
        # Graphique: Économie de vapeur vs nombre d'effets
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 1. Économie de vapeur
        axes[0, 0].plot(df_effets['nombre_effets'], df_effets['economie_vapeur'], 
                       'o-', linewidth=2, markersize=8)
        axes[0, 0].set_xlabel('Nombre d\'effets')
        axes[0, 0].set_ylabel('Économie de vapeur')
        axes[0, 0].set_title('Économie de vapeur vs Nombre d\'effets')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Surface totale
        axes[0, 1].plot(df_effets['nombre_effets'], df_effets['surface_totale'],
                       's-', linewidth=2, markersize=8, color='orange')
        axes[0, 1].set_xlabel('Nombre d\'effets')
        axes[0, 1].set_ylabel('Surface totale (m²)')
        axes[0, 1].set_title('Surface d\'échange vs Nombre d\'effets')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Consommation de vapeur
        axes[1, 0].plot(df_effets['nombre_effets'], df_effets['consommation_vapeur'],
                       '^-', linewidth=2, markersize=8, color='green')
        axes[1, 0].set_xlabel('Nombre d\'effets')
        axes[1, 0].set_ylabel('Consommation vapeur (kg/h)')
        axes[1, 0].set_title('Consommation de vapeur vs Nombre d\'effets')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. Consommation spécifique
        axes[1, 1].plot(df_effets['nombre_effets'], df_effets['consommation_specifique'],
                       'd-', linewidth=2, markersize=8, color='red')
        axes[1, 1].set_xlabel('Nombre d\'effets')
        axes[1, 1].set_ylabel('Consommation spécifique (kg/kg)')
        axes[1, 1].set_title('Consommation spécifique vs Nombre d\'effets')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('resultats/graphiques/comparaison_configurations.png', 
                   dpi=300, bbox_inches='tight')
        print("Graphique sauvegardé: resultats/graphiques/comparaison_configurations.png")
        plt.close()
        
    except Exception as e:
        print(f"Erreur lors de la génération des graphiques: {e}")


def main():
    """Fonction principale."""
    print("\n" + "="*80)
    print("  PROJET ÉVAPORATION-CRISTALLISATION DU SACCHAROSE")
    print("  Simulation complète du procédé")
    print("="*80)
    
    # Créer le dossier de résultats
    os.makedirs('resultats', exist_ok=True)
    os.makedirs('resultats/graphiques', exist_ok=True)
    
    try:
        # 1. Simulation évaporateurs
        df_effets = simulation_evaporateurs()
        
        # 2. Analyse de sensibilité
        analyses = analyse_sensibilite_evaporateurs()
        
        # 3. Simulation cristallisation
        df_profils = simulation_cristallisation()
        
        # 4. Dimensionnement
        dim = dimensionnement()
        
        # 5. Analyse économique
        roi = analyse_economique()
        
        # 6. Graphiques comparatifs
        generer_graphiques_comparatifs()
        
        print_header("SIMULATION TERMINÉE AVEC SUCCÈS")
        print("Tous les résultats ont été sauvegardés dans le dossier 'resultats/'")
        print("\nFichiers générés:")
        print("  - comparaison_effets.xlsx")
        print("  - comparaison_profils.xlsx")
        print("  - dimensionnement_cristalliseur.xlsx")
        print("  - analyse_economique.xlsx")
        print("  - sensibilite_*.xlsx (4 fichiers)")
        print("  - graphiques/*.png (graphiques)")
        
    except Exception as e:
        print(f"\nERREUR lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
