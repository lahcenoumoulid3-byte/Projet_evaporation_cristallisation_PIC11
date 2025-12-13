"""
Module thermodynamique.py
=========================

Ce module gère tous les calculs thermodynamiques pour le projet d'évaporation-cristallisation.
Utilise CoolProp pour les propriétés de l'eau/vapeur et thermo pour les solutions de saccharose.

Auteur: Projet PIC11
Date: 2025
"""

import numpy as np
from CoolProp.CoolProp import PropsSI
from thermo import Chemical
from typing import Tuple, Dict


class ProprietesEauVapeur:
    """
    Classe pour calculer les propriétés thermodynamiques de l'eau et de la vapeur
    en utilisant la bibliothèque CoolProp.
    """
    
    @staticmethod
    def enthalpie_vapeur_saturee(pression: float) -> float:
        """
        Calcule l'enthalpie de la vapeur saturée à une pression donnée.
        
        Args:
            pression (float): Pression en Pa (absolue)
            
        Returns:
            float: Enthalpie en J/kg
        """
        return PropsSI('H', 'P', pression, 'Q', 1, 'Water')
    
    @staticmethod
    def enthalpie_liquide_sature(pression: float) -> float:
        """
        Calcule l'enthalpie du liquide saturé à une pression donnée.
        
        Args:
            pression (float): Pression en Pa (absolue)
            
        Returns:
            float: Enthalpie en J/kg
        """
        return PropsSI('H', 'P', pression, 'Q', 0, 'Water')
    
    @staticmethod
    def chaleur_latente(pression: float) -> float:
        """
        Calcule la chaleur latente de vaporisation à une pression donnée.
        
        Args:
            pression (float): Pression en Pa (absolue)
            
        Returns:
            float: Chaleur latente en J/kg
        """
        h_vap = ProprietesEauVapeur.enthalpie_vapeur_saturee(pression)
        h_liq = ProprietesEauVapeur.enthalpie_liquide_sature(pression)
        return h_vap - h_liq
    
    @staticmethod
    def temperature_saturation(pression: float) -> float:
        """
        Calcule la température de saturation à une pression donnée.
        
        Args:
            pression (float): Pression en Pa (absolue)
            
        Returns:
            float: Température en K
        """
        return PropsSI('T', 'P', pression, 'Q', 0, 'Water')
    
    @staticmethod
    def pression_saturation(temperature: float) -> float:
        """
        Calcule la pression de saturation à une température donnée.
        
        Args:
            temperature (float): Température en K
            
        Returns:
            float: Pression en Pa
        """
        return PropsSI('P', 'T', temperature, 'Q', 0, 'Water')
    
    @staticmethod
    def enthalpie_liquide(temperature: float, pression: float) -> float:
        """
        Calcule l'enthalpie du liquide à température et pression données.
        
        Args:
            temperature (float): Température en K
            pression (float): Pression en Pa
            
        Returns:
            float: Enthalpie en J/kg
        """
        return PropsSI('H', 'T', temperature, 'P', pression, 'Water')
    
    @staticmethod
    def capacite_calorifique_liquide(temperature: float, pression: float) -> float:
        """
        Calcule la capacité calorifique du liquide.
        
        Args:
            temperature (float): Température en K
            pression (float): Pression en Pa
            
        Returns:
            float: Cp en J/(kg·K)
        """
        return PropsSI('C', 'T', temperature, 'P', pression, 'Water')


class ProprietesSaccharose:
    """
    Classe pour calculer les propriétés des solutions de saccharose.
    """
    
    @staticmethod
    def solubilite(temperature_celsius: float) -> float:
        """
        Calcule la solubilité du saccharose en fonction de la température.
        Corrélation empirique : C* = 64.18 + 0.1337*T + 5.52e-3*T² - 9.73e-6*T³
        
        Args:
            temperature_celsius (float): Température en °C
            
        Returns:
            float: Solubilité en g saccharose / 100g solution
        """
        T = temperature_celsius
        C_star = 64.18 + 0.1337*T + 5.52e-3*T**2 - 9.73e-6*T**3
        return C_star
    
    @staticmethod
    def concentration_massique_to_fraction(concentration_pct: float) -> float:
        """
        Convertit la concentration massique (%) en fraction massique.
        
        Args:
            concentration_pct (float): Concentration en % massique
            
        Returns:
            float: Fraction massique (0-1)
        """
        return concentration_pct / 100.0
    
    @staticmethod
    def fraction_to_concentration_massique(fraction: float) -> float:
        """
        Convertit la fraction massique en concentration massique (%).
        
        Args:
            fraction (float): Fraction massique (0-1)
            
        Returns:
            float: Concentration en % massique
        """
        return fraction * 100.0
    
    @staticmethod
    def elevation_point_ebullition_duhring(concentration_pct: float, 
                                          temperature_eau_celsius: float) -> float:
        """
        Calcule l'élévation du point d'ébullition (EPE) du saccharose
        en utilisant la corrélation de Dühring.
        
        Corrélation simplifiée : EPE = a * X² + b * X
        où X est la concentration massique en fraction
        
        Args:
            concentration_pct (float): Concentration en % massique
            temperature_eau_celsius (float): Température d'ébullition de l'eau pure en °C
            
        Returns:
            float: Élévation du point d'ébullition en °C
        """
        X = concentration_pct / 100.0  # Fraction massique
        
        # Coefficients de la corrélation de Dühring (approximation)
        # Ces valeurs peuvent être ajustées selon les données expérimentales
        a = 25.0  # Coefficient quadratique
        b = 5.0   # Coefficient linéaire
        
        EPE = a * X**2 + b * X
        return EPE
    
    @staticmethod
    def temperature_ebullition_solution(concentration_pct: float, 
                                       pression: float) -> float:
        """
        Calcule la température d'ébullition d'une solution de saccharose.
        
        Args:
            concentration_pct (float): Concentration en % massique
            pression (float): Pression en Pa
            
        Returns:
            float: Température d'ébullition en K
        """
        # Température d'ébullition de l'eau pure à cette pression
        T_eau = ProprietesEauVapeur.temperature_saturation(pression)
        T_eau_celsius = T_eau - 273.15
        
        # Élévation du point d'ébullition
        EPE = ProprietesSaccharose.elevation_point_ebullition_duhring(
            concentration_pct, T_eau_celsius
        )
        
        # Température d'ébullition de la solution
        T_solution = T_eau + EPE
        return T_solution
    
    @staticmethod
    def masse_volumique_solution(concentration_pct: float, 
                                 temperature_celsius: float) -> float:
        """
        Calcule la masse volumique d'une solution de saccharose.
        Corrélation empirique basée sur les données de Perry's Handbook.
        
        Args:
            concentration_pct (float): Concentration en % massique
            temperature_celsius (float): Température en °C
            
        Returns:
            float: Masse volumique en kg/m³
        """
        X = concentration_pct / 100.0
        T = temperature_celsius
        
        # Masse volumique de l'eau
        rho_eau = 1000.0 - 0.0736 * T - 0.00355 * T**2
        
        # Correction pour le saccharose
        rho_solution = rho_eau * (1 + 0.4 * X)
        
        return rho_solution
    
    @staticmethod
    def viscosite_solution(concentration_pct: float, 
                          temperature_celsius: float) -> float:
        """
        Calcule la viscosité dynamique d'une solution de saccharose.
        
        Args:
            concentration_pct (float): Concentration en % massique
            temperature_celsius (float): Température en °C
            
        Returns:
            float: Viscosité dynamique en Pa·s
        """
        X = concentration_pct / 100.0
        T = temperature_celsius + 273.15  # Conversion en K
        
        # Viscosité de l'eau (corrélation d'Andrade)
        mu_eau = 2.414e-5 * 10**(247.8 / (T - 140))
        
        # Correction pour le saccharose (corrélation empirique)
        mu_solution = mu_eau * np.exp(4.5 * X)
        
        return mu_solution


class BilanThermique:
    """
    Classe pour effectuer les bilans thermiques.
    """
    
    @staticmethod
    def chaleur_sensible(masse: float, cp: float, delta_T: float) -> float:
        """
        Calcule la chaleur sensible.
        
        Args:
            masse (float): Masse en kg
            cp (float): Capacité calorifique en J/(kg·K)
            delta_T (float): Variation de température en K
            
        Returns:
            float: Chaleur sensible en J
        """
        return masse * cp * delta_T
    
    @staticmethod
    def chaleur_latente_totale(masse: float, chaleur_latente: float) -> float:
        """
        Calcule la chaleur latente totale.
        
        Args:
            masse (float): Masse en kg
            chaleur_latente (float): Chaleur latente en J/kg
            
        Returns:
            float: Chaleur latente totale en J
        """
        return masse * chaleur_latente
    
    @staticmethod
    def coefficient_transfert_global(U_propre: float, 
                                    resistance_encrassement: float = 0.0002) -> float:
        """
        Calcule le coefficient de transfert thermique global
        en tenant compte de l'encrassement.
        
        Args:
            U_propre (float): Coefficient de transfert propre en W/(m²·K)
            resistance_encrassement (float): Résistance d'encrassement en m²·K/W
            
        Returns:
            float: Coefficient de transfert global en W/(m²·K)
        """
        # 1/U_global = 1/U_propre + R_encrassement
        U_global = 1 / (1/U_propre + resistance_encrassement)
        return U_global
    
    @staticmethod
    def surface_echange(flux_thermique: float, U: float, delta_T_ml: float) -> float:
        """
        Calcule la surface d'échange nécessaire.
        Q = U * A * ΔT_ml
        
        Args:
            flux_thermique (float): Flux thermique en W
            U (float): Coefficient de transfert global en W/(m²·K)
            delta_T_ml (float): Différence de température moyenne logarithmique en K
            
        Returns:
            float: Surface d'échange en m²
        """
        if delta_T_ml <= 0:
            raise ValueError("La différence de température doit être positive")
        
        A = flux_thermique / (U * delta_T_ml)
        return A
    
    @staticmethod
    def delta_T_ml(T_chaud_entree: float, T_chaud_sortie: float,
                   T_froid_entree: float, T_froid_sortie: float) -> float:
        """
        Calcule la différence de température moyenne logarithmique (LMTD).
        
        Args:
            T_chaud_entree (float): Température entrée fluide chaud en K
            T_chaud_sortie (float): Température sortie fluide chaud en K
            T_froid_entree (float): Température entrée fluide froid en K
            T_froid_sortie (float): Température sortie fluide froid en K
            
        Returns:
            float: LMTD en K
        """
        delta_T1 = T_chaud_entree - T_froid_sortie
        delta_T2 = T_chaud_sortie - T_froid_entree
        
        if delta_T1 <= 0 or delta_T2 <= 0:
            raise ValueError("Configuration thermique invalide")
        
        if abs(delta_T1 - delta_T2) < 1e-6:
            return delta_T1
        
        LMTD = (delta_T1 - delta_T2) / np.log(delta_T1 / delta_T2)
        return LMTD


def test_module():
    """
    Fonction de test pour vérifier le bon fonctionnement du module.
    """
    print("=== Test du module thermodynamique ===\n")
    
    # Test 1: Propriétés eau/vapeur
    print("Test 1: Propriétés eau/vapeur à 3.5 bar")
    P = 3.5e5  # 3.5 bar en Pa
    T_sat = ProprietesEauVapeur.temperature_saturation(P)
    h_vap = ProprietesEauVapeur.enthalpie_vapeur_saturee(P)
    h_liq = ProprietesEauVapeur.enthalpie_liquide_sature(P)
    L_vap = ProprietesEauVapeur.chaleur_latente(P)
    
    print(f"  Température de saturation: {T_sat - 273.15:.2f} °C")
    print(f"  Enthalpie vapeur saturée: {h_vap/1000:.2f} kJ/kg")
    print(f"  Enthalpie liquide saturé: {h_liq/1000:.2f} kJ/kg")
    print(f"  Chaleur latente: {L_vap/1000:.2f} kJ/kg\n")
    
    # Test 2: Solubilité du saccharose
    print("Test 2: Solubilité du saccharose")
    for T in [30, 50, 70]:
        C_star = ProprietesSaccharose.solubilite(T)
        print(f"  À {T}°C: {C_star:.2f} g/100g solution")
    print()
    
    # Test 3: Élévation du point d'ébullition
    print("Test 3: Élévation du point d'ébullition")
    for conc in [15, 40, 65]:
        EPE = ProprietesSaccharose.elevation_point_ebullition_duhring(conc, 100)
        print(f"  À {conc}% saccharose: EPE = {EPE:.2f} °C")
    print()
    
    # Test 4: Température d'ébullition solution
    print("Test 4: Température d'ébullition à 0.15 bar")
    P_cond = 0.15e5  # 0.15 bar en Pa
    for conc in [15, 40, 65]:
        T_eb = ProprietesSaccharose.temperature_ebullition_solution(conc, P_cond)
        print(f"  À {conc}% saccharose: {T_eb - 273.15:.2f} °C")
    print()
    
    print("=== Tests terminés avec succès ===")


if __name__ == "__main__":
    test_module()
