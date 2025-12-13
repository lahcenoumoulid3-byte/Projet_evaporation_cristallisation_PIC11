
import sys
import os
import numpy as np

# Add modules to path
sys.path.insert(0, os.path.join(os.getcwd(), 'modules'))

from cristallisation import CinetiqueCristallisation, BilanPopulation
import thermodynamique as thermo

def test_scenario_apres():
    print("=== TEST SCENARIO APRES ===")
    
    # Parameters from app.py (Modified)
    C_init = 82.0
    Eg = 18000.0
    kg = 3.0e-4
    T0 = 70.0
    Tf = 25.0
    
    print(f"Params: C={C_init}, Eg={Eg}, kg={kg}, T0={T0}, Tf={Tf}")
    
    # Run manual thermodynamics verification
    C_sat_T0 = thermo.ProprietesSaccharose.solubilite(T0)
    C_sat_Tf = thermo.ProprietesSaccharose.solubilite(Tf)
    print(f"Solubility T0 ({T0}C): {C_sat_T0:.2f}")
    print(f"Solubility Tf ({Tf}C): {C_sat_Tf:.2f}")
    
    S_T0 = (C_init - C_sat_T0) / C_sat_T0
    S_Tf = (C_init - C_sat_Tf) / C_sat_Tf
    print(f"Supersaturation T0: {S_T0:.4f}")
    print(f"Supersaturation Tf: {S_Tf:.4f}")
    
    if S_Tf <= 0:
        print("ERROR: No supersaturation at final temperature!")
    
    # Run Simulation
    try:
        cinetique = CinetiqueCristallisation()
        cinetique.params.kg = kg
        cinetique.params.Eg = Eg
        
        bilan = BilanPopulation(cinetique)
        res = bilan.resoudre_batch(
            T0_celsius=T0, Tf_celsius=Tf,
            concentration_initiale=C_init,
            volume_batch=10, duree_heures=4,
            profil='lineaire', n_classes=100
        )
        
        print("\nRESULTS:")
        print(f"L50: {res['L50']}")
        print(f"Rendement: {res['rendement']}")
        print(f"Masse Cristaux: {res['masse_cristaux']}")
        
        print(f"Non-zero bins: {np.count_nonzero(res['distribution_finale'])}")
        print(f"Max density: {np.max(res['distribution_finale'])}")
        
    except Exception as e:
        print(f"SIMULATION ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scenario_apres()
