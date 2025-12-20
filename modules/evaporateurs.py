"""
Module evaporateurs.py
======================

Ce module gère la simulation des évaporateurs multi-effets pour la concentration
du saccharose. Il inclut les bilans matière et énergie, le calcul des surfaces
d'échange et l'optimisation du nombre d'effets.

Auteur: Projet PIC11
Date: 2025
"""

import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
from . import thermodynamique as thermo


@dataclass
class ParametresEffet:
    """Paramètres d'un effet d'évaporation."""
    numero: int
    pression: float  # Pa
    U: float  # Coefficient de transfert W/(m²·K)
    pertes_thermiques: float = 0.03  # 3% de pertes


@dataclass
class ResultatsEffet:
    """Résultats de simulation pour un effet."""
    numero: int
    debit_alimentation: float  # kg/h
    debit_vapeur: float  # kg/h
    debit_concentrat: float  # kg/h
    concentration: float  # % massique
    temperature: float  # K
    pression: float  # Pa
    flux_thermique: float  # W
    surface_echange: float  # m²
    enthalpie_alimentation: float  # J/kg
    enthalpie_vapeur: float  # J/kg


class Effet:
    """
    Représente un effet d'évaporation dans un système multi-effets.
    """
    
    def __init__(self, params: ParametresEffet):
        """
        Initialise un effet d'évaporation.
        
        Args:
            params (ParametresEffet): Paramètres de l'effet
        """
        self.params = params
        self.resultats = None
    
    def calculer_temperature_ebullition(self, concentration: float) -> float:
        """
        Calcule la température d'ébullition de la solution.
        
        Args:
            concentration (float): Concentration en % massique
            
        Returns:
            float: Température d'ébullition en K
        """
        return thermo.ProprietesSaccharose.temperature_ebullition_solution(
            concentration, self.params.pression
        )
    
    def calculer_enthalpie_alimentation(self, temperature: float, 
                                       concentration: float) -> float:
        """
        Calcule l'enthalpie de l'alimentation.
        
        Args:
            temperature (float): Température en K
            concentration (float): Concentration en % massique
            
        Returns:
            float: Enthalpie en J/kg
        """
        # Approximation: enthalpie basée sur l'eau avec correction
        cp_eau = thermo.ProprietesEauVapeur.capacite_calorifique_liquide(
            temperature, self.params.pression
        )
        
        # Correction pour le saccharose (cp diminue avec la concentration)
        X = concentration / 100.0
        cp_solution = cp_eau * (1 - 0.3 * X)
        
        # Enthalpie par rapport à 0°C
        h = cp_solution * (temperature - 273.15)
        return h


class EvaporateurMultiEffets:
    """
    Système d'évaporation multi-effets pour la concentration du saccharose.
    """
    
    def __init__(self, nombre_effets: int):
        """
        Initialise le système d'évaporation.
        
        Args:
            nombre_effets (int): Nombre d'effets (2-5)
        """
        if nombre_effets < 2 or nombre_effets > 5:
            raise ValueError("Le nombre d'effets doit être entre 2 et 5")
        
        self.nombre_effets = nombre_effets
        self.effets: List[Effet] = []
        self.resultats_globaux = {}
    
    def initialiser_effets(self, pression_vapeur: float, 
                          pression_condenseur: float,
                          coefficients_U: List[float] = None):
        """
        Initialise les effets avec répartition des pressions.
        
        Args:
            pression_vapeur (float): Pression de la vapeur de chauffe en Pa
            pression_condenseur (float): Pression au condenseur final en Pa
            coefficients_U (List[float]): Coefficients de transfert pour chaque effet
        """
        # Coefficients U par défaut si non fournis
        if coefficients_U is None:
            # Décroissance typique des coefficients U
            coefficients_U = [2500, 2200, 1800, 1500, 1200][:self.nombre_effets]
        
        # Répartition logarithmique des pressions
        pressions = np.logspace(
            np.log10(pression_condenseur),
            np.log10(pression_vapeur * 0.9),  # Légèrement en dessous de la vapeur
            self.nombre_effets
        )[::-1]  # Inverser pour avoir décroissance
        
        # Créer les effets
        self.effets = []
        for i in range(self.nombre_effets):
            params = ParametresEffet(
                numero=i + 1,
                pression=pressions[i],
                U=coefficients_U[i]
            )
            self.effets.append(Effet(params))
    
    def bilan_matiere(self, debit_alimentation: float,
                     concentration_alimentation: float,
                     concentration_finale: float) -> List[Dict]:
        """
        Effectue le bilan matière sur tous les effets.
        
        Args:
            debit_alimentation (float): Débit d'alimentation total en kg/h
            concentration_alimentation (float): Concentration initiale en %
            concentration_finale (float): Concentration finale visée en %
        
        Returns:
            List[Dict]: Bilans matière pour chaque effet
        """
        bilans = []
        
        # Débit de saccharose (constant)
        debit_saccharose = debit_alimentation * concentration_alimentation / 100.0
        
        # Débit final de concentrat
        debit_final = debit_saccharose / (concentration_finale / 100.0)
        
        # Évaporation totale
        evaporation_totale = debit_alimentation - debit_final
        
        # Répartition de l'évaporation (approximation: égale par effet)
        evaporation_par_effet = evaporation_totale / self.nombre_effets
        
        # Calcul pour chaque effet
        debit_entree = debit_alimentation
        conc_entree = concentration_alimentation
        
        for i in range(self.nombre_effets):
            debit_vapeur = evaporation_par_effet
            debit_sortie = debit_entree - debit_vapeur
            conc_sortie = (debit_entree * conc_entree) / debit_sortie
            
            bilan = {
                'effet': i + 1,
                'debit_entree': debit_entree,
                'concentration_entree': conc_entree,
                'debit_vapeur': debit_vapeur,
                'debit_sortie': debit_sortie,
                'concentration_sortie': conc_sortie
            }
            bilans.append(bilan)
            
            # Préparer pour l'effet suivant
            debit_entree = debit_sortie
            conc_entree = conc_sortie
        
        return bilans
    
    def bilan_energie(self, bilans_matiere: List[Dict],
                     temperature_alimentation: float,
                     pression_vapeur: float) -> List[ResultatsEffet]:
        """
        Effectue le bilan énergétique sur tous les effets.
        
        Args:
            bilans_matiere (List[Dict]): Bilans matière de chaque effet
            temperature_alimentation (float): Température d'alimentation en K
            pression_vapeur (float): Pression de la vapeur de chauffe en Pa
            
        Returns:
            List[ResultatsEffet]: Résultats complets pour chaque effet
        """
        resultats = []
        
        # Propriétés de la vapeur de chauffe
        h_vapeur_chauffe = thermo.ProprietesEauVapeur.enthalpie_vapeur_saturee(pression_vapeur)
        h_condensat_chauffe = thermo.ProprietesEauVapeur.enthalpie_liquide_sature(pression_vapeur)
        L_vapeur_chauffe = h_vapeur_chauffe - h_condensat_chauffe
        
        T_entree = temperature_alimentation
        
        for i, bilan in enumerate(bilans_matiere):
            effet = self.effets[i]
            
            # Température d'ébullition dans cet effet
            T_ebullition = effet.calculer_temperature_ebullition(
                bilan['concentration_sortie']
            )
            
            # Enthalpies
            h_entree = effet.calculer_enthalpie_alimentation(
                T_entree, bilan['concentration_entree']
            )
            h_sortie = effet.calculer_enthalpie_alimentation(
                T_ebullition, bilan['concentration_sortie']
            )
            
            # Chaleur latente de la vapeur produite
            L_vapeur_produite = thermo.ProprietesEauVapeur.chaleur_latente(
                effet.params.pression
            )
            h_vapeur_produite = thermo.ProprietesEauVapeur.enthalpie_vapeur_saturee(
                effet.params.pression
            )
            
            # Bilan énergétique (en W, conversion de kg/h en kg/s)
            debit_entree_kg_s = bilan['debit_entree'] / 3600.0
            debit_sortie_kg_s = bilan['debit_sortie'] / 3600.0
            debit_vapeur_kg_s = bilan['debit_vapeur'] / 3600.0
            
            # Chaleur nécessaire
            Q_sensible = debit_entree_kg_s * (h_sortie - h_entree)
            Q_latente = debit_vapeur_kg_s * L_vapeur_produite
            Q_total = Q_sensible + Q_latente
            
            # Pertes thermiques
            Q_pertes = Q_total * effet.params.pertes_thermiques
            Q_requis = Q_total + Q_pertes
            
            # Calcul de la surface d'échange
            if i == 0:
                # Premier effet: chauffé par vapeur externe
                T_vapeur = thermo.ProprietesEauVapeur.temperature_saturation(pression_vapeur)
                delta_T = T_vapeur - T_ebullition
            else:
                # Effets suivants: chauffés par vapeur de l'effet précédent
                T_vapeur_prec = resultats[i-1].temperature
                delta_T = T_vapeur_prec - T_ebullition
            
            # Coefficient U avec encrassement
            U_global = thermo.BilanThermique.coefficient_transfert_global(
                effet.params.U, resistance_encrassement=0.0002
            )
            
            # Surface d'échange
            if delta_T > 0:
                A = Q_requis / (U_global * delta_T)
            else:
                A = 0.0
                print(f"Attention: ΔT négatif pour effet {i+1}")
            
            # Créer les résultats
            resultat = ResultatsEffet(
                numero=i + 1,
                debit_alimentation=bilan['debit_entree'],
                debit_vapeur=bilan['debit_vapeur'],
                debit_concentrat=bilan['debit_sortie'],
                concentration=bilan['concentration_sortie'],
                temperature=T_ebullition,
                pression=effet.params.pression,
                flux_thermique=Q_requis,
                surface_echange=A,
                enthalpie_alimentation=h_entree,
                enthalpie_vapeur=h_vapeur_produite
            )
            resultats.append(resultat)
            
            # Température d'entrée pour l'effet suivant = température de sortie actuelle
            T_entree = T_ebullition
        
        return resultats
    
    def simuler(self, debit_alimentation: float,
               concentration_alimentation: float,
               concentration_finale: float,
               temperature_alimentation_celsius: float,
               pression_vapeur: float,
               pression_condenseur: float,
               coefficients_U: List[float] = None) -> Dict:
        """
        Simule le système d'évaporation multi-effets complet.
        
        Args:
            debit_alimentation (float): Débit d'alimentation en kg/h
            concentration_alimentation (float): Concentration initiale en %
            concentration_finale (float): Concentration finale en %
            temperature_alimentation_celsius (float): Température alimentation en °C
            pression_vapeur (float): Pression vapeur de chauffe en Pa
            pression_condenseur (float): Pression au condenseur en Pa
            coefficients_U (List[float]): Coefficients de transfert
            
        Returns:
            Dict: Résultats complets de la simulation
        """
        # Initialiser les effets
        self.initialiser_effets(pression_vapeur, pression_condenseur, coefficients_U)
        
        # Bilans matière
        bilans_matiere = self.bilan_matiere(
            debit_alimentation,
            concentration_alimentation,
            concentration_finale
        )
        
        # Bilans énergie
        T_alim = temperature_alimentation_celsius + 273.15
        resultats_effets = self.bilan_energie(
            bilans_matiere,
            T_alim,
            pression_vapeur
        )
        
        # Calculs globaux
        evaporation_totale = sum(r.debit_vapeur for r in resultats_effets)
        surface_totale = sum(r.surface_echange for r in resultats_effets)
        
        # Économie de vapeur
        economie_vapeur = evaporation_totale / resultats_effets[0].debit_vapeur
        
        # Consommation de vapeur (premier effet)
        consommation_vapeur = resultats_effets[0].flux_thermique / \
                             thermo.ProprietesEauVapeur.chaleur_latente(pression_vapeur)
        
        self.resultats_globaux = {
            'nombre_effets': self.nombre_effets,
            'resultats_effets': resultats_effets,
            'evaporation_totale': evaporation_totale,
            'surface_totale': surface_totale,
            'economie_vapeur': economie_vapeur,
            'consommation_vapeur_kg_s': consommation_vapeur,
            'consommation_vapeur_kg_h': consommation_vapeur * 3600,
            'consommation_specifique': consommation_vapeur * 3600 / evaporation_totale
        }
        
        return self.resultats_globaux
    
    def afficher_resultats(self):
        """Affiche les résultats de la simulation."""
        if not self.resultats_globaux:
            print("Aucune simulation effectuée.")
            return
        
        print(f"\n{'='*70}")
        print(f"RÉSULTATS ÉVAPORATEUR {self.nombre_effets} EFFETS")
        print(f"{'='*70}\n")
        
        for r in self.resultats_globaux['resultats_effets']:
            print(f"Effet {r.numero}:")
            print(f"  Pression: {r.pression/1e5:.3f} bar")
            print(f"  Température: {r.temperature - 273.15:.2f} °C")
            print(f"  Concentration: {r.concentration:.2f} %")
            print(f"  Débit vapeur: {r.debit_vapeur:.2f} kg/h")
            print(f"  Surface échange: {r.surface_echange:.2f} m²")
            print(f"  Flux thermique: {r.flux_thermique/1000:.2f} kW")
            print()
        
        print(f"RÉSULTATS GLOBAUX:")
        print(f"  Évaporation totale: {self.resultats_globaux['evaporation_totale']:.2f} kg/h")
        print(f"  Surface totale: {self.resultats_globaux['surface_totale']:.2f} m²")
        print(f"  Économie de vapeur: {self.resultats_globaux['economie_vapeur']:.3f}")
        print(f"  Consommation vapeur: {self.resultats_globaux['consommation_vapeur_kg_h']:.2f} kg/h")
        print(f"  Consommation spécifique: {self.resultats_globaux['consommation_specifique']:.3f} kg vapeur/kg évaporé")
        print(f"{'='*70}\n")


def test_module():
    """Fonction de test du module."""
    print("=== Test du module évaporateurs ===\n")
    
    # Paramètres du procédé
    debit_alim = 10000  # kg/h
    conc_alim = 15  # %
    conc_finale = 65  # %
    T_alim = 85  # °C
    P_vapeur = 3.5e5  # 3.5 bar
    P_cond = 0.15e5  # 0.15 bar
    
    # Test avec 3 effets
    evap = EvaporateurMultiEffets(3)
    resultats = evap.simuler(
        debit_alim, conc_alim, conc_finale, T_alim,
        P_vapeur, P_cond
    )
    evap.afficher_resultats()


if __name__ == "__main__":
    test_module()
