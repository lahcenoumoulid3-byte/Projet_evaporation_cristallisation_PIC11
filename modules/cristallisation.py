"""
Module cristallisation.py
=========================

Ce module gère la simulation de la cristallisation batch du saccharose.
Inclut la cinétique de nucléation et croissance, le bilan de population,
et les différents profils de refroidissement.

Auteur: Projet PIC11
Date: 2025
"""

import numpy as np
from scipy.integrate import odeint, solve_ivp
from scipy.interpolate import interp1d
from typing import Callable, Tuple, Dict, List
from dataclasses import dataclass
import thermodynamique as thermo


@dataclass
class ParametresCinetique:
    """Paramètres cinétiques pour la cristallisation."""
    kb: float = 1.5e10  # Constante de nucléation (noyaux/(m³·s))
    b: float = 2.5  # Exposant de nucléation
    j: float = 0.5  # Exposant de masse de cristaux
    kg: float = 3.0e-4  # Constante de croissance (m/s) - Optimisée pour 20-50 μm/h
    g: float = 1.5  # Exposant de croissance
    Eg: float = 18000  # Énergie d'activation (J/mol) - Typique pour saccharose
    R: float = 8.314  # Constante des gaz parfaits (J/(mol·K))


class CinetiqueCristallisation:
    """
    Classe pour calculer les cinétiques de nucléation et croissance.
    """
    
    def __init__(self, params: ParametresCinetique = None):
        """
        Initialise les paramètres cinétiques.
        
        Args:
            params (ParametresCinetique): Paramètres cinétiques
        """
        self.params = params if params else ParametresCinetique()
    
    def sursaturation_relative(self, concentration: float, 
                              temperature_celsius: float) -> float:
        """
        Calcule la sursaturation relative.
        S = (C - C*) / C*
        
        Args:
            concentration (float): Concentration actuelle (g/100g solution)
            temperature_celsius (float): Température en °C
            
        Returns:
            float: Sursaturation relative (sans dimension)
        """
        C_star = thermo.ProprietesSaccharose.solubilite(temperature_celsius)
        
        if C_star <= 0:
            return 0.0
        
        S = (concentration - C_star) / C_star
        return max(0.0, S)  # Sursaturation ne peut pas être négative
    
    def taux_nucleation(self, sursaturation: float, 
                       masse_cristaux: float) -> float:
        """
        Calcule le taux de nucléation.
        B = kb * S^b * mj^j
        
        Args:
            sursaturation (float): Sursaturation relative
            masse_cristaux (float): Masse de cristaux en suspension (kg/m³)
            
        Returns:
            float: Taux de nucléation (noyaux/(m³·s))
        """
        if sursaturation <= 0:
            return 0.0
        
        # Protection contre masse nulle
        mj = max(masse_cristaux, 1e-6)
        
        B = self.params.kb * (sursaturation ** self.params.b) * (mj ** self.params.j)
        return B
    
    def vitesse_croissance(self, sursaturation: float, 
                          temperature: float) -> float:
        """
        Calcule la vitesse de croissance linéaire.
        G = kg * S^g * exp(-Eg / (R*T))
        
        Args:
            sursaturation (float): Sursaturation relative
            temperature (float): Température en K
            
        Returns:
            float: Vitesse de croissance (m/s)
        """
        if sursaturation <= 0:
            return 0.0
        
        G = self.params.kg * (sursaturation ** self.params.g) * \
            np.exp(-self.params.Eg / (self.params.R * temperature))
        
        return G


class ProfilRefroidissement:
    """
    Classe pour définir différents profils de refroidissement.
    """
    
    @staticmethod
    def lineaire(t: float, T0: float, Tf: float, duree: float) -> float:
        """
        Profil de refroidissement linéaire.
        T(t) = T0 - α*t
        
        Args:
            t (float): Temps en secondes
            T0 (float): Température initiale en °C
            Tf (float): Température finale en °C
            duree (float): Durée totale en secondes
            
        Returns:
            float: Température en °C
        """
        if t >= duree:
            return Tf
        
        alpha = (T0 - Tf) / duree
        return T0 - alpha * t
    
    @staticmethod
    def exponentiel(t: float, T0: float, Tf: float, duree: float) -> float:
        """
        Profil de refroidissement exponentiel.
        T(t) = Tf + (T0 - Tf) * exp(-β*t)
        
        Args:
            t (float): Temps en secondes
            T0 (float): Température initiale en °C
            Tf (float): Température finale en °C
            duree (float): Durée totale en secondes
            
        Returns:
            float: Température en °C
        """
        # Choisir β tel que T(duree) ≈ Tf + 0.05*(T0-Tf)
        beta = -np.log(0.05) / duree
        
        T = Tf + (T0 - Tf) * np.exp(-beta * t)
        return T
    
    @staticmethod
    def sursaturation_constante(concentration_actuelle: float,
                                sursaturation_cible: float = 0.05) -> float:
        """
        Calcule la température pour maintenir une sursaturation constante.
        
        Args:
            concentration_actuelle (float): Concentration actuelle (g/100g)
            sursaturation_cible (float): Sursaturation cible
            
        Returns:
            float: Température en °C
        """
        # Résolution numérique: trouver T tel que S = S_cible
        # C* = C / (1 + S_cible)
        C_star_cible = concentration_actuelle / (1 + sursaturation_cible)
        
        # Recherche de la température correspondante
        # Par dichotomie entre 20 et 80°C
        T_min, T_max = 20.0, 80.0
        
        for _ in range(50):  # Itérations de dichotomie
            T_mid = (T_min + T_max) / 2
            C_star_mid = thermo.ProprietesSaccharose.solubilite(T_mid)
            
            if abs(C_star_mid - C_star_cible) < 0.01:
                return T_mid
            
            if C_star_mid < C_star_cible:
                T_min = T_mid
            else:
                T_max = T_mid
        
        return (T_min + T_max) / 2


class BilanPopulation:
    """
    Classe pour résoudre le bilan de population des cristaux.
    """
    
    def __init__(self, cinetique: CinetiqueCristallisation):
        """
        Initialise le bilan de population.
        
        Args:
            cinetique (CinetiqueCristallisation): Objet cinétique
        """
        self.cinetique = cinetique
        self.resultats = None
    
    def resoudre_batch(self, T0_celsius: float, Tf_celsius: float,
                      concentration_initiale: float,
                      volume_batch: float,
                      duree_heures: float,
                      profil: str = 'lineaire',
                      n_classes: int = 50) -> Dict:
        """
        Résout le bilan de population pour un cristalliseur batch.
        
        Args:
            T0_celsius (float): Température initiale en °C
            Tf_celsius (float): Température finale en °C
            concentration_initiale (float): Concentration initiale (g/100g)
            volume_batch (float): Volume du batch en m³
            duree_heures (float): Durée du batch en heures
            profil (str): Type de profil ('lineaire', 'exponentiel', 'optimal')
            n_classes (int): Nombre de classes de taille
            
        Returns:
            Dict: Résultats de la simulation
        """
        duree_secondes = duree_heures * 3600
        
        # Discrétisation de la taille
        L_max = 1e-3  # Taille maximale 1 mm
        L_classes = np.linspace(0, L_max, n_classes)
        dL = L_classes[1] - L_classes[0]
        
        # Conditions initiales (pas de cristaux au début)
        n0 = np.zeros(n_classes)
        C0 = concentration_initiale
        
        # État initial: [n1, n2, ..., n_n, C]
        y0 = np.concatenate([n0, [C0]])
        
        # Temps de simulation
        t_span = (0, duree_secondes)
        t_eval = np.linspace(0, duree_secondes, 200)
        
        # Fonction profil de température
        if profil == 'lineaire':
            T_func = lambda t: ProfilRefroidissement.lineaire(
                t, T0_celsius, Tf_celsius, duree_secondes
            )
        elif profil == 'exponentiel':
            T_func = lambda t: ProfilRefroidissement.exponentiel(
                t, T0_celsius, Tf_celsius, duree_secondes
            )
        else:  # optimal
            T_func = None  # Sera calculé dynamiquement
        
        # Système d'EDO
        def systeme_edo(t, y):
            n = y[:-1]  # Distribution de taille
            C = y[-1]   # Concentration
            
            # Température
            if T_func:
                T_celsius = T_func(t)
            else:
                T_celsius = ProfilRefroidissement.sursaturation_constante(C, 0.05)
            
            T_kelvin = T_celsius + 273.15
            
            # Sursaturation
            S = self.cinetique.sursaturation_relative(C, T_celsius)
            
            # Masse de cristaux (approximation)
            rho_cristal = 1580  # kg/m³ (saccharose)
            kv = np.pi / 6  # Facteur de forme (sphère)
            masse_cristaux = rho_cristal * kv * np.sum(n * L_classes**3 * dL)
            
            # Vitesse de croissance
            G = self.cinetique.vitesse_croissance(S, T_kelvin)
            
            # Taux de nucléation
            B = self.cinetique.taux_nucleation(S, masse_cristaux)
            
            # Dérivées de la distribution
            dn_dt = np.zeros(n_classes)
            
            # Méthode upwind pour ∂n/∂L
            for i in range(1, n_classes):
                dn_dt[i] = -G * (n[i] - n[i-1]) / dL
            
            # Condition limite: n(0,t) = B/G
            if G > 1e-12:
                dn_dt[0] = B / dL - G * n[0] / dL
            
            # Bilan de masse sur la concentration
            # dC/dt = -3 * rho_cristal * kv * G * sum(n * L²)
            dC_dt = -3 * rho_cristal * kv * G * np.sum(n * L_classes**2 * dL) / 10.0
            
            dydt = np.concatenate([dn_dt, [dC_dt]])
            return dydt
        
        # Résolution
        solution = solve_ivp(
            systeme_edo, t_span, y0, t_eval=t_eval,
            method='BDF', rtol=1e-6, atol=1e-8
        )
        
        # Extraction des résultats
        n_final = solution.y[:-1, -1]
        C_final = solution.y[-1, -1]
        
        # Calcul des moments de la distribution
        moments = self.calculer_moments(n_final, L_classes, dL)
        
        # Température finale
        if T_func:
            T_final = T_func(duree_secondes)
        else:
            T_final = ProfilRefroidissement.sursaturation_constante(C_final, 0.05)
        
        resultats = {
            'profil': profil,
            'temps': solution.t / 3600,  # Conversion en heures
            'L_classes': L_classes * 1e6,  # Conversion en μm
            'distribution_finale': n_final,
            'concentration_finale': C_final,
            'temperature_finale': T_final,
            'L50': moments['L50'] * 1e6,  # μm
            'L_moyen': moments['L_moyen'] * 1e6,  # μm
            'CV': moments['CV'],
            'masse_cristaux': moments['masse_totale'],
            'rendement': (concentration_initiale - C_final) / concentration_initiale * 100,
            'solution': solution
        }
        
        self.resultats = resultats
        return resultats
    
    def calculer_moments(self, n: np.ndarray, L: np.ndarray, 
                        dL: float) -> Dict:
        """
        Calcule les moments de la distribution de taille.
        
        Args:
            n (np.ndarray): Distribution de population
            L (np.ndarray): Classes de taille
            dL (float): Pas de discrétisation
            
        Returns:
            Dict: Moments de la distribution
        """
        # Moments
        mu0 = np.sum(n * dL)  # Nombre total
        mu1 = np.sum(n * L * dL)  # Moment d'ordre 1
        mu2 = np.sum(n * L**2 * dL)  # Moment d'ordre 2
        mu3 = np.sum(n * L**3 * dL)  # Moment d'ordre 3
        
        # Taille moyenne
        if mu0 > 0:
            L_moyen = mu1 / mu0
        else:
            L_moyen = 0
        
        # Écart-type
        if mu0 > 0:
            variance = mu2 / mu0 - L_moyen**2
            sigma = np.sqrt(max(0, variance))
        else:
            sigma = 0
        
        # Coefficient de variation
        if L_moyen > 0:
            CV = sigma / L_moyen
        else:
            CV = 0
        
        # L50 (médiane)
        cumul = np.cumsum(n * dL)
        if cumul[-1] > 0:
            cumul_norm = cumul / cumul[-1]
            idx_50 = np.argmin(np.abs(cumul_norm - 0.5))
            L50 = L[idx_50]
        else:
            L50 = 0
        
        # Masse totale de cristaux
        rho_cristal = 1580  # kg/m³
        kv = np.pi / 6
        masse_totale = rho_cristal * kv * mu3
        
        return {
            'mu0': mu0,
            'mu1': mu1,
            'mu2': mu2,
            'mu3': mu3,
            'L_moyen': L_moyen,
            'sigma': sigma,
            'CV': CV,
            'L50': L50,
            'masse_totale': masse_totale
        }


def dimensionner_cristalliseur(masse_batch: float,
                              concentration: float,
                              temps_residence: float,
                              puissance_agitation: float = 50) -> Dict:
    """
    Dimensionne le cristalliseur batch.
    
    Args:
        masse_batch (float): Masse du batch en kg
        concentration (float): Concentration en % massique
        temps_residence (float): Temps de résidence en heures
        puissance_agitation (float): Puissance spécifique d'agitation en W/m³
        
    Returns:
        Dict: Dimensions du cristalliseur
    """
    # Masse volumique de la solution
    rho_solution = thermo.ProprietesSaccharose.masse_volumique_solution(
        concentration, 50  # Température moyenne
    )
    
    # Volume requis
    volume = masse_batch / rho_solution
    
    # Facteur de sécurité (20%)
    volume_total = volume * 1.2
    
    # Géométrie cylindrique (H/D = 1.5)
    # V = π/4 * D² * H = π/4 * D² * 1.5*D = 1.178 * D³
    D = (volume_total / 1.178) ** (1/3)
    H = 1.5 * D
    
    # Puissance d'agitation
    P_agitation = puissance_agitation * volume_total
    
    # Surface du serpentin de refroidissement
    # Flux thermique de refroidissement (approximation)
    cp_solution = 3500  # J/(kg·K)
    delta_T = 35  # Refroidissement de 70 à 35°C
    duree = temps_residence * 3600  # secondes
    
    Q_refroidissement = masse_batch * cp_solution * delta_T / duree  # W
    
    # Coefficient de transfert serpentin
    U_serpentin = 500  # W/(m²·K)
    delta_T_ml = 15  # Différence de température moyenne
    
    A_serpentin = Q_refroidissement / (U_serpentin * delta_T_ml)
    
    return {
        'volume_utile': volume,
        'volume_total': volume_total,
        'diametre': D,
        'hauteur': H,
        'puissance_agitation': P_agitation,
        'surface_serpentin': A_serpentin,
        'flux_refroidissement': Q_refroidissement
    }


def test_module():
    """Fonction de test du module."""
    print("=== Test du module cristallisation ===\n")
    
    # Test 1: Cinétique
    print("Test 1: Cinétique de cristallisation")
    cinetique = CinetiqueCristallisation()
    
    S = 0.05
    T = 50 + 273.15
    m_cristaux = 10  # kg/m³
    
    B = cinetique.taux_nucleation(S, m_cristaux)
    G = cinetique.vitesse_croissance(S, T)
    
    print(f"  Sursaturation: {S}")
    print(f"  Taux de nucléation: {B:.2e} noyaux/(m³·s)")
    print(f"  Vitesse de croissance: {G:.2e} m/s")
    print(f"  Vitesse de croissance: {G*1e6*3600:.2f} μm/h\n")
    
    # Test 2: Profils de refroidissement
    print("Test 2: Profils de refroidissement")
    t_test = np.linspace(0, 4*3600, 100)
    T_lin = [ProfilRefroidissement.lineaire(t, 70, 35, 4*3600) for t in t_test]
    T_exp = [ProfilRefroidissement.exponentiel(t, 70, 35, 4*3600) for t in t_test]
    
    print(f"  Profil linéaire - T(0h): {T_lin[0]:.1f}°C, T(4h): {T_lin[-1]:.1f}°C")
    print(f"  Profil exponentiel - T(0h): {T_exp[0]:.1f}°C, T(4h): {T_exp[-1]:.1f}°C\n")
    
    # Test 3: Dimensionnement
    print("Test 3: Dimensionnement cristalliseur")
    dim = dimensionner_cristalliseur(5000, 65, 4)
    
    print(f"  Volume utile: {dim['volume_utile']:.2f} m³")
    print(f"  Volume total: {dim['volume_total']:.2f} m³")
    print(f"  Diamètre: {dim['diametre']:.2f} m")
    print(f"  Hauteur: {dim['hauteur']:.2f} m")
    print(f"  Puissance agitation: {dim['puissance_agitation']/1000:.2f} kW")
    print(f"  Surface serpentin: {dim['surface_serpentin']:.2f} m²\n")
    
    print("=== Tests terminés ===")


if __name__ == "__main__":
    test_module()
