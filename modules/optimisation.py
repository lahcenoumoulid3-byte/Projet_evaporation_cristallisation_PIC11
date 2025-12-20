"""
Module optimisation.py
======================

Ce module gère les analyses paramétriques, l'optimisation énergétique,
et l'analyse technico-économique du procédé.

Auteur: Projet PIC11
Date: 2025
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Callable
from dataclasses import dataclass
import matplotlib.pyplot as plt
import seaborn as sns


@dataclass
class CoutsInvestissement:
    """Coûts d'investissement du procédé."""
    evaporateurs: float = 0.0  # €
    cristalliseur: float = 0.0  # €
    echangeurs: float = 0.0  # €
    total: float = 0.0  # €


@dataclass
class CoutsExploitation:
    """Coûts d'exploitation annuels."""
    vapeur: float = 0.0  # €/an
    eau_refroidissement: float = 0.0  # €/an
    electricite: float = 0.0  # €/an
    main_oeuvre: float = 0.0  # €/an
    total: float = 0.0  # €/an


class AnalyseSensibilite:
    """
    Classe pour effectuer les analyses de sensibilité paramétriques.
    """
    
    def __init__(self, fonction_simulation: Callable):
        """
        Initialise l'analyse de sensibilité.
        
        Args:
            fonction_simulation (Callable): Fonction de simulation à analyser
        """
        self.fonction_simulation = fonction_simulation
        self.resultats = {}
    
    def varier_parametre(self, nom_parametre: str,
                        valeurs: np.ndarray,
                        params_fixes: Dict,
                        variables_sortie: List[str]) -> pd.DataFrame:
        """
        Varie un paramètre et observe l'impact sur les sorties.
        
        Args:
            nom_parametre (str): Nom du paramètre à varier
            valeurs (np.ndarray): Valeurs du paramètre à tester
            params_fixes (Dict): Paramètres fixes
            variables_sortie (List[str]): Variables de sortie à observer
            
        Returns:
            pd.DataFrame: Résultats de l'analyse
        """
        resultats = []
        
        for val in valeurs:
            # Mettre à jour le paramètre
            params = params_fixes.copy()
            params[nom_parametre] = val
            
            # Simuler
            try:
                res = self.fonction_simulation(**params)
                
                # Extraire les variables de sortie
                ligne = {nom_parametre: val}
                for var in variables_sortie:
                    if var in res:
                        ligne[var] = res[var]
                    else:
                        # Chercher dans les sous-dictionnaires
                        for key, value in res.items():
                            if isinstance(value, dict) and var in value:
                                ligne[var] = value[var]
                                break
                
                resultats.append(ligne)
            except Exception as e:
                print(f"Erreur pour {nom_parametre}={val}: {e}")
        
        df = pd.DataFrame(resultats)
        self.resultats[nom_parametre] = df
        return df
    
    def analyse_complete_evaporateurs(self, params_base: Dict) -> Dict[str, pd.DataFrame]:
        """
        Effectue l'analyse de sensibilité complète pour les évaporateurs.
        
        Args:
            params_base (Dict): Paramètres de base
            
        Returns:
            Dict[str, pd.DataFrame]: Résultats pour chaque paramètre
        """
        variables_sortie = [
            'consommation_vapeur_kg_h',
            'surface_totale',
            'economie_vapeur',
            'consommation_specifique'
        ]
        
        analyses = {}
        
        # 1. Variation de la pression de vapeur (2.5 à 4.5 bar)
        print("Analyse: Pression de vapeur...")
        P_vapeur_vals = np.linspace(2.5e5, 4.5e5, 15)
        df_P = self.varier_parametre(
            'pression_vapeur', P_vapeur_vals, params_base, variables_sortie
        )
        analyses['pression_vapeur'] = df_P
        
        # 2. Variation de la concentration finale (60 à 70%)
        print("Analyse: Concentration finale...")
        conc_vals = np.linspace(60, 70, 15)
        df_conc = self.varier_parametre(
            'concentration_finale', conc_vals, params_base, variables_sortie
        )
        analyses['concentration_finale'] = df_conc
        
        # 3. Variation du débit (±20%)
        print("Analyse: Débit d'alimentation...")
        debit_base = params_base['debit_alimentation']
        debit_vals = np.linspace(debit_base * 0.8, debit_base * 1.2, 15)
        df_debit = self.varier_parametre(
            'debit_alimentation', debit_vals, params_base, variables_sortie
        )
        analyses['debit_alimentation'] = df_debit
        
        # 4. Variation de la température d'alimentation (75 à 95°C)
        print("Analyse: Température d'alimentation...")
        T_vals = np.linspace(75, 95, 15)
        df_T = self.varier_parametre(
            'temperature_alimentation_celsius', T_vals, params_base, variables_sortie
        )
        analyses['temperature_alimentation'] = df_T
        
        return analyses
    
    def analyse_sensibilite_cristallisation(self) -> Dict[str, pd.DataFrame]:
        """
        Effectue l'analyse de sensibilité pour la cristallisation.
        
        Returns:
            Dict[str, pd.DataFrame]: Résultats pour chaque paramètre
        """
        # Imports locaux pour éviter les cycles
        from .cristallisation import CinetiqueCristallisation, BilanPopulation
        
        analyses = {}
        
        # 1. Variation de la concentration initiale (60 à 85 g/100g)
        C_vals = np.linspace(60, 85, 20)
        res_conc = []
        
        for C in C_vals:
            try:
                cinetique = CinetiqueCristallisation()
                cinetique.params.kg = 3.0e-4 # Valeur par défaut
                cinetique.params.Eg = 18000  # Valeur par défaut
                
                bilan = BilanPopulation(cinetique)
                res = bilan.resoudre_batch(
                    T0_celsius=70, Tf_celsius=30,
                    concentration_initiale=C,
                    volume_batch=10, duree_heures=4,
                    profil='lineaire', n_classes=50
                )
                
                res_conc.append({
                    'concentration_initiale': C,
                    'L50': res['L50'],
                    'rendement': res['rendement'],
                    'masse_cristaux': res['masse_cristaux']
                })
            except Exception:
                pass
                
        analyses['concentration'] = pd.DataFrame(res_conc)
        
        # 2. Variation de l'énergie d'activation (15000 à 50000 J/mol)
        Eg_vals = np.linspace(15000, 50000, 20)
        res_Eg = []
        
        for Eg in Eg_vals:
            try:
                cinetique = CinetiqueCristallisation()
                cinetique.params.kg = 3.0e-4
                cinetique.params.Eg = Eg
                
                bilan = BilanPopulation(cinetique)
                res = bilan.resoudre_batch(
                    T0_celsius=70, Tf_celsius=30,
                    concentration_initiale=78.0, # Valeur fixe
                    volume_batch=10, duree_heures=4,
                    profil='lineaire', n_classes=50
                )
                
                res_Eg.append({
                    'energie_activation': Eg,
                    'L50': res['L50'],
                    'rendement': res['rendement'],
                    'masse_cristaux': res['masse_cristaux']
                })
            except Exception:
                pass
                
        analyses['energie_activation'] = pd.DataFrame(res_Eg)
        
        return analyses
    
    def generer_graphiques_sensibilite(self, analyses: Dict[str, pd.DataFrame],
                                      dossier_sortie: str = 'resultats/graphiques'):
        """
        Génère les graphiques d'analyse de sensibilité.
        
        Args:
            analyses (Dict[str, pd.DataFrame]): Résultats des analyses
            dossier_sortie (str): Dossier de sortie pour les graphiques
        """
        import os
        os.makedirs(dossier_sortie, exist_ok=True)
        
        # Style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 8)
        
        # Pour chaque paramètre varié
        for param_name, df in analyses.items():
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            fig.suptitle(f'Analyse de Sensibilité: {param_name}', fontsize=16, fontweight='bold')
            
            # Graphique 1: Consommation de vapeur
            if 'consommation_vapeur_kg_h' in df.columns:
                axes[0, 0].plot(df[param_name], df['consommation_vapeur_kg_h'], 'o-', linewidth=2)
                axes[0, 0].set_xlabel(param_name)
                axes[0, 0].set_ylabel('Consommation vapeur (kg/h)')
                axes[0, 0].grid(True, alpha=0.3)
            
            # Graphique 2: Surface totale
            if 'surface_totale' in df.columns:
                axes[0, 1].plot(df[param_name], df['surface_totale'], 's-', linewidth=2, color='orange')
                axes[0, 1].set_xlabel(param_name)
                axes[0, 1].set_ylabel('Surface totale (m²)')
                axes[0, 1].grid(True, alpha=0.3)
            
            # Graphique 3: Économie de vapeur
            if 'economie_vapeur' in df.columns:
                axes[1, 0].plot(df[param_name], df['economie_vapeur'], '^-', linewidth=2, color='green')
                axes[1, 0].set_xlabel(param_name)
                axes[1, 0].set_ylabel('Économie de vapeur')
                axes[1, 0].grid(True, alpha=0.3)
            
            # Graphique 4: Consommation spécifique
            if 'consommation_specifique' in df.columns:
                axes[1, 1].plot(df[param_name], df['consommation_specifique'], 'd-', linewidth=2, color='red')
                axes[1, 1].set_xlabel(param_name)
                axes[1, 1].set_ylabel('Consommation spécifique (kg/kg)')
                axes[1, 1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Sauvegarder
            nom_fichier = f'sensibilite_{param_name}.png'
            chemin = os.path.join(dossier_sortie, nom_fichier)
            plt.savefig(chemin, dpi=300, bbox_inches='tight')
            print(f"Graphique sauvegardé: {chemin}")
            plt.close()


class OptimisationNombreEffets:
    """
    Classe pour optimiser le nombre d'effets.
    """
    
    def __init__(self, fonction_simulation: Callable):
        """
        Initialise l'optimisation.
        
        Args:
            fonction_simulation (Callable): Fonction de simulation
        """
        self.fonction_simulation = fonction_simulation
    
    def comparer_configurations(self, params_base: Dict,
                               nombres_effets: List[int] = [2, 3, 4, 5]) -> pd.DataFrame:
        """
        Compare différentes configurations (nombre d'effets).
        
        Args:
            params_base (Dict): Paramètres de base
            nombres_effets (List[int]): Nombres d'effets à comparer
            
        Returns:
            pd.DataFrame: Comparaison des configurations
        """
        resultats = []
        
        for n_effets in nombres_effets:
            print(f"Simulation avec {n_effets} effets...")
            
            params = params_base.copy()
            params['nombre_effets'] = n_effets
            
            try:
                res = self.fonction_simulation(**params)
                
                ligne = {
                    'nombre_effets': n_effets,
                    'consommation_vapeur': res.get('consommation_vapeur_kg_h', 0),
                    'surface_totale': res.get('surface_totale', 0),
                    'economie_vapeur': res.get('economie_vapeur', 0),
                    'consommation_specifique': res.get('consommation_specifique', 0)
                }
                
                resultats.append(ligne)
            except Exception as e:
                print(f"Erreur pour {n_effets} effets: {e}")
        
        return pd.DataFrame(resultats)


class AnalyseEconomique:
    """
    Classe pour l'analyse technico-économique.
    """
    
    # Prix unitaires (Adaptés pour le Maroc en MAD)
    # Conversion approx: 1 EUR ≈ 11 MAD
    PRIX_VAPEUR = 275.0      # MAD/tonne (ex: 25€ * 11)
    PRIX_EAU = 1.65          # MAD/m³ (ex: 0.15€ * 11)
    PRIX_ELECTRICITE = 1.32  # MAD/kWh (ex: 0.12€ * 11)
    PRIX_MAIN_OEUVRE = 40.0  # MAD/h·opérateur (SMIG/Qualifié)
    
    def __init__(self):
        """Initialise l'analyse économique."""
        self.couts_investissement = None
        self.couts_exploitation = None
    
    def calculer_investissement(self, surfaces_evaporateurs: List[float],
                               volume_cristalliseur: float,
                               surfaces_echangeurs: List[float] = None) -> CoutsInvestissement:
        """
        Calcule les coûts d'investissement.
        
        Formules du projet:
        - Évaporateurs: C = 15000 * A^0.65 (€)
        - Cristalliseur: C = 25000 * V^0.6 (€)
        - Échangeurs: C = 8000 * A^0.7 (€)
        
        Args:
            surfaces_evaporateurs (List[float]): Surfaces des évaporateurs en m²
            volume_cristalliseur (float): Volume du cristalliseur en m³
            surfaces_echangeurs (List[float]): Surfaces des échangeurs en m²
            
        Returns:
            CoutsInvestissement: Coûts d'investissement
        """
        # Évaporateurs
        cout_evap = sum(15000 * A**0.65 for A in surfaces_evaporateurs)
        
        # Cristalliseur
        cout_crist = 25000 * volume_cristalliseur**0.6
        
        # Échangeurs
        if surfaces_echangeurs:
            cout_ech = sum(8000 * A**0.7 for A in surfaces_echangeurs)
        else:
            cout_ech = 0
        
        total = cout_evap + cout_crist + cout_ech
        
        self.couts_investissement = CoutsInvestissement(
            evaporateurs=cout_evap,
            cristalliseur=cout_crist,
            echangeurs=cout_ech,
            total=total
        )
        
        return self.couts_investissement
    
    def calculer_exploitation(self, consommation_vapeur_kg_h: float,
                             consommation_eau_m3_h: float,
                             puissance_electrique_kW: float,
                             nombre_operateurs: int = 2,
                             heures_operation_an: float = 8000) -> CoutsExploitation:
        """
        Calcule les coûts d'exploitation annuels.
        
        Args:
            consommation_vapeur_kg_h (float): Consommation de vapeur en kg/h
            consommation_eau_m3_h (float): Consommation d'eau en m³/h
            puissance_electrique_kW (float): Puissance électrique en kW
            nombre_operateurs (int): Nombre d'opérateurs
            heures_operation_an (float): Heures d'opération par an
            
        Returns:
            CoutsExploitation: Coûts d'exploitation annuels
        """
        # Vapeur
        cout_vapeur = (consommation_vapeur_kg_h / 1000) * self.PRIX_VAPEUR * heures_operation_an
        
        # Eau de refroidissement
        cout_eau = consommation_eau_m3_h * self.PRIX_EAU * heures_operation_an
        
        # Électricité
        cout_elec = puissance_electrique_kW * self.PRIX_ELECTRICITE * heures_operation_an
        
        # Main d'œuvre
        cout_mo = nombre_operateurs * self.PRIX_MAIN_OEUVRE * heures_operation_an
        
        total = cout_vapeur + cout_eau + cout_elec + cout_mo
        
        self.couts_exploitation = CoutsExploitation(
            vapeur=cout_vapeur,
            eau_refroidissement=cout_eau,
            electricite=cout_elec,
            main_oeuvre=cout_mo,
            total=total
        )
        
        return self.couts_exploitation
    
    def calculer_roi(self, investissement: float,
                    opex_annuel: float,
                    production_annuelle_tonnes: float,
                    prix_vente_tonne: float) -> Dict:
        """
        Calcule le retour sur investissement (ROI).
        
        Args:
            investissement (float): Investissement total en €
            opex_annuel (float): OPEX annuel en €
            production_annuelle_tonnes (float): Production annuelle en tonnes
            prix_vente_tonne (float): Prix de vente par tonne en €
            
        Returns:
            Dict: Indicateurs économiques
        """
        # Revenus annuels
        revenus_annuels = production_annuelle_tonnes * prix_vente_tonne
        
        # Bénéfice annuel
        benefice_annuel = revenus_annuels - opex_annuel
        
        # Temps de retour simple
        if benefice_annuel > 0:
            temps_retour = investissement / benefice_annuel
        else:
            temps_retour = float('inf')
        
        # Coût de production par tonne
        cout_production_tonne = opex_annuel / production_annuelle_tonnes
        
        # Marge bénéficiaire
        if revenus_annuels > 0:
            marge = (benefice_annuel / revenus_annuels) * 100
        else:
            marge = 0
        
        return {
            'investissement': investissement,
            'opex_annuel': opex_annuel,
            'revenus_annuels': revenus_annuels,
            'benefice_annuel': benefice_annuel,
            'temps_retour_annees': temps_retour,
            'cout_production_tonne': cout_production_tonne,
            'marge_beneficiaire_pct': marge
        }
    
    def cout_total_annualise(self, investissement: float,
                            opex_annuel: float,
                            duree_vie_ans: int = 15,
                            taux_actualisation: float = 0.08) -> float:
        """
        Calcule le coût total annualisé (TCA).
        
        Args:
            investissement (float): Investissement en €
            opex_annuel (float): OPEX annuel en €
            duree_vie_ans (int): Durée de vie en années
            taux_actualisation (float): Taux d'actualisation
            
        Returns:
            float: Coût total annualisé en €/an
        """
        # Facteur de récupération du capital
        if taux_actualisation > 0:
            CRF = (taux_actualisation * (1 + taux_actualisation)**duree_vie_ans) / \
                  ((1 + taux_actualisation)**duree_vie_ans - 1)
        else:
            CRF = 1 / duree_vie_ans
        
        # Coût annualisé de l'investissement
        capex_annualise = investissement * CRF
        
        # Coût total annualisé
        TCA = capex_annualise + opex_annuel
        
        return TCA


class IntegrationEnergetique:
    """
    Classe pour l'intégration énergétique et la pinch analysis.
    """
    
    def __init__(self):
        """Initialise l'intégration énergétique."""
        self.flux_chauds = []
        self.flux_froids = []
    
    def ajouter_flux_chaud(self, T_entree: float, T_sortie: float,
                          flux_thermique: float, nom: str = ""):
        """
        Ajoute un flux chaud.
        
        Args:
            T_entree (float): Température d'entrée en °C
            T_sortie (float): Température de sortie en °C
            flux_thermique (float): Flux thermique en kW
            nom (str): Nom du flux
        """
        self.flux_chauds.append({
            'nom': nom,
            'T_entree': T_entree,
            'T_sortie': T_sortie,
            'flux': flux_thermique,
            'cp': flux_thermique / (T_entree - T_sortie) if T_entree != T_sortie else 0
        })
    
    def ajouter_flux_froid(self, T_entree: float, T_sortie: float,
                          flux_thermique: float, nom: str = ""):
        """
        Ajoute un flux froid.
        
        Args:
            T_entree (float): Température d'entrée en °C
            T_sortie (float): Température de sortie en °C
            flux_thermique (float): Flux thermique en kW
            nom (str): Nom du flux
        """
        self.flux_froids.append({
            'nom': nom,
            'T_entree': T_entree,
            'T_sortie': T_sortie,
            'flux': flux_thermique,
            'cp': flux_thermique / (T_sortie - T_entree) if T_sortie != T_entree else 0
        })
    
    def calculer_pinch(self, delta_T_min: float = 10) -> Dict:
        """
        Calcule le point de pincement.
        
        Args:
            delta_T_min (float): Différence de température minimale en °C
            
        Returns:
            Dict: Résultats de la pinch analysis
        """
        # Simplification: calcul des besoins minimaux
        # Flux chaud total disponible
        Q_chaud_total = sum(f['flux'] for f in self.flux_chauds)
        
        # Flux froid total requis
        Q_froid_total = sum(f['flux'] for f in self.flux_froids)
        
        # Besoins minimaux
        if Q_chaud_total > Q_froid_total:
            Q_chaud_min = 0
            Q_froid_min = Q_chaud_total - Q_froid_total
        else:
            Q_chaud_min = Q_froid_total - Q_chaud_total
            Q_froid_min = 0
        
        # Potentiel de récupération
        Q_recuperation = min(Q_chaud_total, Q_froid_total)
        
        return {
            'Q_chaud_total': Q_chaud_total,
            'Q_froid_total': Q_froid_total,
            'Q_chaud_min': Q_chaud_min,
            'Q_froid_min': Q_froid_min,
            'Q_recuperation': Q_recuperation,
            'economie_pct': (Q_recuperation / Q_chaud_total * 100) if Q_chaud_total > 0 else 0
        }


def test_module():
    """Fonction de test du module."""
    print("=== Test du module optimisation ===\n")
    
    # Test 1: Analyse économique
    print("Test 1: Analyse économique")
    analyse_eco = AnalyseEconomique()
    
    # Investissement
    surfaces_evap = [100, 80, 60]  # m²
    volume_crist = 10  # m³
    
    inv = analyse_eco.calculer_investissement(surfaces_evap, volume_crist)
    print(f"  Coût évaporateurs: {inv.evaporateurs/1000:.2f} k€")
    print(f"  Coût cristalliseur: {inv.cristalliseur/1000:.2f} k€")
    print(f"  Investissement total: {inv.total/1000:.2f} k€\n")
    
    # Exploitation
    opex = analyse_eco.calculer_exploitation(
        consommation_vapeur_kg_h=2000,
        consommation_eau_m3_h=50,
        puissance_electrique_kW=100,
        nombre_operateurs=2
    )
    print(f"  Coût vapeur: {opex.vapeur/1000:.2f} k€/an")
    print(f"  Coût électricité: {opex.electricite/1000:.2f} k€/an")
    print(f"  OPEX total: {opex.total/1000:.2f} k€/an\n")
    
    # ROI
    roi = analyse_eco.calculer_roi(
        investissement=inv.total,
        opex_annuel=opex.total,
        production_annuelle_tonnes=5000,
        prix_vente_tonne=800
    )
    print(f"  Temps de retour: {roi['temps_retour_annees']:.2f} ans")
    print(f"  Coût production: {roi['cout_production_tonne']:.2f} €/tonne")
    print(f"  Marge bénéficiaire: {roi['marge_beneficiaire_pct']:.2f} %\n")
    
    print("=== Tests terminés ===")


if __name__ == "__main__":
    test_module()
