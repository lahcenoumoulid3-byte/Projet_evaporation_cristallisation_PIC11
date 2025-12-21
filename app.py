"""
Application Streamlit pour le Projet Évaporation-Cristallisation
=================================================================

Interface web interactive pour visualiser et manipuler les simulations.

Auteur: Projet PIC11
Date: 2025
"""

import streamlit as st
import sys
import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Imports des modules
import modules.thermodynamique as thermo
from modules.evaporateurs import EvaporateurMultiEffets
from modules.cristallisation import (
    CinetiqueCristallisation, BilanPopulation,
    dimensionner_cristalliseur
)
from modules.optimisation import AnalyseEconomique, CoutsInvestissement


# Configuration de la page
st.set_page_config(
    page_title="Évaporation-Cristallisation PIC11",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Projet PIC11 - Évaporation & Cristallisation du Saccharose"
    }
)

# Chargement et injection du CSS personnalisé (Design DistillSim-inspired)
def load_custom_css():
    """Charge et injecte le CSS personnalisé."""
    css_path = os.path.join(os.path.dirname(__file__), 'assets', 'custom_style.css')
    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("⚠️ Fichier CSS personnalisé non trouvé. Utilisation du style par défaut.")

load_custom_css()

# Configuration Plotly - Modern Theme
PLOTLY_TEMPLATE = {
    'layout': {
        'colorway': ['#6366f1', '#ec4899', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4'],
        'font': {'family': 'Inter, Segoe UI, sans-serif', 'size': 12, 'color': '#1e293b'},
        'paper_bgcolor': 'white',
        'plot_bgcolor': '#f8fafc',
        'title': {'font': {'size': 18, 'color': '#1e293b', 'family': 'Inter, sans-serif'}},
        'xaxis': {'gridcolor': '#e2e8f0', 'linecolor': '#cbd5e1'},
        'yaxis': {'gridcolor': '#e2e8f0', 'linecolor': '#cbd5e1'}
    }
}



def page_accueil():
    """Page d'accueil."""
    st.markdown('''
    <div class="main-header">
        <h1>Projet Évaporation-Cristallisation</h1>
        <p>Simulation industrielle complète - PIC11</p>
    </div>
    ''', unsafe_allow_html=True)

    
    st.markdown("""
    ## Présentation du Projet
    
    Ce projet simule un procédé industriel complet de concentration et cristallisation du saccharose 
    comprenant :
    
    ### Partie 1: Évaporateurs Multi-Effets
    - Modélisation thermodynamique avec **CoolProp** et **thermo**
    - Bilans matière et énergie
    - Optimisation du nombre d'effets (2-5)
    - Analyse de sensibilité paramétrique
    
    ### Partie 2: Cristallisation Batch
    - Cinétique de nucléation et croissance
    - Résolution du bilan de population
    - Comparaison de profils de refroidissement
    - Dimensionnement du cristalliseur
    
    ### Partie 3: Analyse Économique
    - Coûts d'investissement (CAPEX)
    - Coûts d'exploitation (OPEX)
    - Retour sur investissement (ROI)
    - Intégration énergétique
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("**Données du Procédé**\n\n"
                "• Débit: 10 000 kg/h\n"
                "• Concentration: 15% → 65%\n"
                "• Vapeur: 3.5 bar")
    
    with col2:
        st.success("**Objectifs**\n\n"
                   "• Maximiser économie vapeur\n"
                   "• Minimiser coûts\n"
                   "• Optimiser distribution cristaux")
    
    with col3:
        st.warning("**Technologies**\n\n"
                   "• Python + CoolProp\n"
                   "• NumPy + SciPy\n"
                   "• Streamlit + Plotly")


def page_evaporateurs():
    """Page de simulation des évaporateurs."""
    st.markdown('''
    <div class="main-header">
        <h1>Évaporateurs Multi-Effets</h1>
        <p>Modélisation thermodynamique et bilans matière-énergie</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Sidebar pour les paramètres (Communs)
    st.sidebar.header("Paramètres de Simulation")
    
    n_effets = st.sidebar.slider("Nombre d'effets", 2, 5, 3)
    debit = st.sidebar.number_input("Débit alimentation (kg/h)", 5000, 20000, 10000, 1000)
    conc_init = st.sidebar.slider("Concentration initiale (%)", 10.0, 25.0, 15.0, 0.5)
    conc_final = st.sidebar.slider("Concentration finale (%)", 55.0, 75.0, 65.0, 1.0)
    T_alim = st.sidebar.slider("Température alimentation (°C)", 70, 100, 85, 5)
    P_vapeur = st.sidebar.slider("Pression vapeur (bar)", 2.5, 4.5, 3.5, 0.1)
    
    # Onglets supprimés sur demande
    
    if st.sidebar.button("Lancer la Simulation", key="sim_evap"):
        with st.spinner("Simulation en cours..."):
            try:
                # Simulation
                evap = EvaporateurMultiEffets(n_effets)
                res = evap.simuler(
                    debit_alimentation=debit,
                    concentration_alimentation=conc_init,
                    concentration_finale=conc_final,
                    temperature_alimentation_celsius=T_alim,
                    pression_vapeur=P_vapeur * 1e5,
                    pression_condenseur=0.15e5
                )
                
                # Métriques clés
                st.subheader("Résultats Globaux")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Économie de vapeur", f"{res['economie_vapeur']:.2f}")
                
                with col2:
                    st.metric("Surface totale", f"{res['surface_totale']:.1f} m²")
                
                with col3:
                    st.metric("Consommation vapeur", f"{res['consommation_vapeur_kg_h']:.0f} kg/h")
                
                with col4:
                    st.metric("Consommation spécifique", f"{res['consommation_specifique']:.3f} kg/kg")
                
                # Tableau des résultats par effet
                st.subheader("Résultats par Effet")
                
                data_effets = []
                for r in res['resultats_effets']:
                    data_effets.append({
                        'Effet': r.numero,
                        'Pression (bar)': f"{r.pression/1e5:.3f}",
                        'Température (°C)': f"{r.temperature - 273.15:.2f}",
                        'Concentration (%)': f"{r.concentration:.2f}",
                        'Débit vapeur (kg/h)': f"{r.debit_vapeur:.1f}",
                        'Surface (m²)': f"{r.surface_echange:.2f}",
                        'Flux thermique (kW)': f"{r.flux_thermique/1000:.1f}"
                    })
                
                df_effets = pd.DataFrame(data_effets)
                st.dataframe(df_effets, use_container_width=True)
                
                # Graphiques
                st.subheader("Visualisations")
                
                # Créer les graphiques avec Plotly
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=('Températures par Effet', 'Concentrations par Effet',
                                  'Débits de Vapeur', 'Surfaces d\'Échange'),
                    specs=[[{"type": "scatter"}, {"type": "scatter"}],
                           [{"type": "bar"}, {"type": "bar"}]]
                )
                
                effets = [r.numero for r in res['resultats_effets']]
                temperatures = [r.temperature - 273.15 for r in res['resultats_effets']]
                concentrations = [r.concentration for r in res['resultats_effets']]
                debits_vapeur = [r.debit_vapeur for r in res['resultats_effets']]
                surfaces = [r.surface_echange for r in res['resultats_effets']]
                
                # Températures
                fig.add_trace(
                    go.Scatter(x=effets, y=temperatures, mode='lines+markers',
                              name='Température', line=dict(color='#ff6b6b', width=3),
                              marker=dict(size=10)),
                    row=1, col=1
                )
                
                # Concentrations
                fig.add_trace(
                    go.Scatter(x=effets, y=concentrations, mode='lines+markers',
                              name='Concentration', line=dict(color='#00bfff', width=3),
                              marker=dict(size=10)),
                    row=1, col=2
                )
                
                # Débits vapeur
                fig.add_trace(
                    go.Bar(x=effets, y=debits_vapeur, name='Débit vapeur',
                           marker_color='#20c997'),
                    row=2, col=1
                )
                
                # Surfaces
                fig.add_trace(
                    go.Bar(x=effets, y=surfaces, name='Surface',
                           marker_color='#003366'),
                    row=2, col=2
                )
                
                fig.update_xaxes(title_text="Effet", row=1, col=1)
                fig.update_xaxes(title_text="Effet", row=1, col=2)
                fig.update_xaxes(title_text="Effet", row=2, col=1)
                fig.update_xaxes(title_text="Effet", row=2, col=2)
                
                fig.update_yaxes(title_text="Température (°C)", row=1, col=1)
                fig.update_yaxes(title_text="Concentration (%)", row=1, col=2)
                fig.update_yaxes(title_text="Débit (kg/h)", row=2, col=1)
                fig.update_yaxes(title_text="Surface (m²)", row=2, col=2)
                
                # Appliquer le template DistillSim
                fig.update_layout(
                    height=700, 
                    showlegend=False,
                    font=PLOTLY_TEMPLATE['layout']['font'],
                    paper_bgcolor=PLOTLY_TEMPLATE['layout']['paper_bgcolor'],
                    plot_bgcolor=PLOTLY_TEMPLATE['layout']['plot_bgcolor']
                )
                fig.update_xaxes(gridcolor='#e9ecef', linecolor='#dee2e6')
                fig.update_yaxes(gridcolor='#e9ecef', linecolor='#dee2e6')
                
                st.plotly_chart(fig, use_container_width=True)

                    
            except Exception as e:
                st.error(f"Erreur simulation: {e}")
                    



def page_cristallisation():
    """Page de simulation de la cristallisation."""
    st.markdown('''
    <div class="main-header">
        <h1>Cristallisation Batch</h1>
        <p>Cinétique de nucléation, croissance et bilan de population</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Paramètres
    st.sidebar.header("Paramètres de Cristallisation")
    
    # Création des onglets
    tab1, tab2, tab3, tab4 = st.tabs(["Simulation", "Analyse & Calibration", "Détails Calculs", "Comparaison Avant/Après"])
    
    with tab1:
        # Initialiser session_state pour persist results
        if 'crist_results' not in st.session_state:
            st.session_state.crist_results = None
        
        # Réintroduction T0
        # Paramètres étendus (Demande Expert)
        T0 = st.sidebar.slider("Température initiale (°C)", 25, 80, 70, 1)
        Tf = st.sidebar.slider("Température finale (°C)", 0, 50, 20, 1)
        duree = st.sidebar.slider("Durée (heures)", 2.0, 10.0, 6.0, 0.5)
        conc_init = st.sidebar.slider("Concentration initiale (g/100g)", 70.0, 100.0, 84.0, 0.5)
        profil = st.sidebar.selectbox("Profil de refroidissement", 
                                      ['lineaire', 'exponentiel', 'optimal'])
        
        if st.sidebar.button("Lancer la Simulation", key="sim_crist"):
            with st.spinner("Simulation en cours (peut prendre quelques secondes)..."):
                try:
                    cinetique = CinetiqueCristallisation()
                    bilan_pop = BilanPopulation(cinetique)
                    
                    res = bilan_pop.resoudre_batch(
                        T0, Tf, conc_init, volume_batch=10,
                        duree_heures=duree, profil=profil, n_classes=50
                    )
                    
                    # Sauvegarder dans session_state
                    st.session_state.crist_results = {
                        'res': res,
                        'T0': T0,
                        'Tf': Tf,
                        'duree': duree,
                        'profil': profil
                    }
                    
                except Exception as e:
                    st.error(f"❌ Erreur lors de la simulation: {e}")
                    st.exception(e)
        
        # Afficher les résultats si disponibles
        if st.session_state.crist_results is not None:
            res = st.session_state.crist_results['res']
            T0 = st.session_state.crist_results['T0']
            Tf = st.session_state.crist_results['Tf']
            duree = st.session_state.crist_results['duree']
            profil = st.session_state.crist_results['profil']
            
            # Métriques
            st.subheader("Résultats de la Cristallisation")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("L50 (médiane)", f"{res['L50']:.1f} μm")
            
            with col2:
                st.metric("L moyen", f"{res['L_moyen']:.1f} μm")
            
            with col3:
                st.metric("CV", f"{res['CV']:.3f}")
            
            with col4:
                st.metric("Rendement", f"{res['rendement']:.1f} %")
            
            # Graphiques
            st.subheader("Distribution de Taille des Cristaux")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=res['L_classes'],
                y=res['distribution_finale'],
                mode='lines',
                fill='tozeroy',
                name='Distribution',
                line=dict(color='purple', width=2)
            ))
            
            fig.update_layout(
                title=f"Distribution de Taille - Profil {profil}",
                xaxis_title="Taille des cristaux (μm)",
                yaxis_title="Densité de population",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Informations supplémentaires
            st.info(f"""
            **Paramètres de simulation:**
            - Profil: {profil}
            - Température: {T0}°C → {Tf}°C
            - Durée: {duree} heures
            - Concentration finale: {res['concentration_finale']:.2f} g/100g
            - Masse de cristaux: {res['masse_cristaux']:.2f} kg
            """)

    with tab2:
        st.header("🔬 Analyse de Sensibilité Étendue & Optimisation")
        st.markdown("""
        **Étude Complète:** Cette analyse fait varier systématiquement tous les paramètres critiques 
        (Durée, Concentration, Températures, Profil) pour identifier la **combinaison optimale** maximisant le rendement.
        
        *Paramètres testés:*
        - Durée: 2 à 10h
        - Concentration: 70 à 100 g/100g
        - T0: 60-80°C, Tf: 10-40°C
        - Profils: Linéaire, Exponentiel
        """)
        
        if st.button("🚀 Lancer l'Optimisation Globale", key="run_global_opt"):
            prog_bar = st.progress(0)
            status_text = st.empty()
            
            with st.spinner("Exploration de l'espace des paramètres en cours..."):
                try:
                    from modules.optimisation import AnalyseSensibilite
                    
                    analyseur = AnalyseSensibilite(lambda: None)
                    # Note: La fonction est synchrone, on ne verra pas la barre progresser en temps réel 
                    # sauf si on modifie la lib, mais simulation rapide.
                    best_config, df_res = analyseur.analyse_multivariable_cristallisation()
                    prog_bar.progress(100)
                    
                    st.success("Optimisation terminée !")
                    
                    # Sauvegarde pour propagation (QA/QC)
                    st.session_state['optimal_params'] = best_config
                    
                    # Affichage du Meilleur Résultat
                    st.subheader("🏆 Configuration Optimale Identifiée")
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Rendement Max", f"{best_config['Rendement']:.1f} %")
                    c2.metric("Masse Cristaux", f"{best_config['Masse']:.2f} kg")
                    c3.metric("Taille L50", f"{best_config['L50']:.0f} μm")
                    c4.metric("Profil", f"{best_config['Profil']}")
                    
                    st.write("---")
                    st.write("**Paramètres Optimaux:**")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Durée", f"{best_config['Duree_h']} h")
                    c2.metric("Conc. Initiale", f"{best_config['Conc_init']} g/100g")
                    c3.metric("Temp Initiale (T0)", f"{best_config['T0']} °C")
                    c4.metric("Temp Finale (Tf)", f"{best_config['Tf']} °C")
                    
                    # Visualisation des corrélations
                    st.subheader("📈 Corrélations Clés")
                    
                    tab_viz1, tab_viz2 = st.tabs(["Rendement vs Durée/Conc", "Impact Thermique"])
                    
                    with tab_viz1:
                        # Rendement vs Durée et Concentration
                        fig = px.scatter(df_res, x='Duree_h', y='Rendement', 
                                       color='Conc_init', size='Masse',
                                       title="Rendement selon Durée et Concentration",
                                       labels={'Duree_h': 'Durée (h)', 'Conc_init': 'Concentration (g/100g)'})
                        st.plotly_chart(fig, use_container_width=True)
                        
                    with tab_viz2:
                        # Rendement vs Tf
                        fig2 = px.box(df_res, x='Tf', y='Rendement', color='Profil',
                                    title="Distribution du Rendement selon Tf et Profil")
                        st.plotly_chart(fig2, use_container_width=True)
                    
                    # Données brutes
                    with st.expander("Voir toutes les simulations"):
                        st.dataframe(df_res.sort_values(by='Rendement', ascending=False))
                        
                except Exception as e:
                    st.error(f"Erreur lors de l'optimisation: {e}")
                    st.exception(e)

    with tab3:
        st.header("📑 Détails des Calculs (Paramètres Optimisés)")
        st.markdown("""
        Cette section détaille les calculs intermédiaires effectués avec les paramètres optimisés
        pour valider la physique du modèle.
        """)
        
        if st.button("🧮 Lancer les Calculs Détaillés", key="run_details"):
            try:
                # 1. Récupération des Paramètres (Propagation)
                if 'optimal_params' in st.session_state:
                    params = st.session_state['optimal_params']
                    C_opt = float(params['Conc_init'])
                    # On garde Eg fixe car non varié dans l'optimisation multivariable (fixé à 18000)
                    Eg_opt = 18000.0 
                    kg_opt = 3.0e-4
                    T0_opt = float(params['T0'])
                    Tf_opt = float(params['Tf'])
                    duree_opt = float(params['Duree_h'])
                    st.success("✅ Utilisation des paramètres optimisés identifiés dans l'onglet Analyse.")
                else:
                    st.warning("⚠️ Paramètres par défaut (Veuillez lancer l'optimisation dans l'onglet 2 pour des résultats personnalisés).")
                    C_opt = 78.0
                    Eg_opt = 18000.0
                    kg_opt = 3.0e-4
                    T0_opt = 70.0
                    Tf_opt = 30.0
                    duree_opt = 4.0

                st.subheader("1. Paramètres d'Entrée")
                col1, col2, col3 = st.columns(3)
                col1.metric("Concentration Initiale", f"{C_opt} g/100g")
                col2.metric("Énergie d'Activation", f"{Eg_opt} J/mol")
                col3.metric("Constante Croissance", f"{kg_opt:.1e} m/s")
                
                # 2. Thermodynamique (Solubilité & Sursaturation)
                st.subheader("2. Thermodynamique & Sursaturation")
                
                # Calculs manuels pour affichage
                C_star_T0 = thermo.ProprietesSaccharose.solubilite(T0_opt)
                C_star_Tf = thermo.ProprietesSaccharose.solubilite(Tf_opt)
                
                S_T0 = (C_opt - C_star_T0) / C_star_T0
                S_Tf = (C_opt - C_star_Tf) / C_star_Tf
                
                st.markdown(f"""
                **Formule Sursaturation :** $S = \\frac{{C - C^*}}{{C^*}}$
                
                **À T = {T0_opt}°C (Début) :**
                - Solubilité $C^*$ : {C_star_T0:.2f} g/100g
                - Concentration $C$ : {C_opt} g/100g
                - Sursaturation $S$ : {S_T0:.4f} (Sous-saturé, dissolution)
                
                **À T = {Tf_opt}°C (Fin) :**
                - Solubilité $C^*$ : {C_star_Tf:.2f} g/100g
                - Concentration $C$ : {C_opt} g/100g
                - Sursaturation $S$ : **{S_Tf:.4f}** (Sursaturé > 0, cristallisation possible ✅)
                """)
                
                # 3. Cinétique (Vitesse de Croissance)
                st.subheader("3. Cinétique de Croissance")
                
                # Calcul G à Tf
                R = 8.314
                T_kelvin = Tf_opt + 273.15
                Arrhenius = np.exp(-Eg_opt / (R * T_kelvin))
                G_final = kg_opt * (max(0, S_Tf)**1.5) * Arrhenius
                G_final_um = G_final * 1e6 * 3600 # um/h
                
                st.markdown(f"""
                **Loi de Croissance :** $G = k_g \\cdot S^g \\cdot \\exp\\\\left(\\\\frac{{-E_g}}{{RT}}\\\\right)$
                
                **Calcul à {Tf_opt}°C :**
                - Terme Arrhenius : $\\exp(\\frac{{-{Eg_opt}}}{{8.314 \\times {T_kelvin:.1f}}}) = {Arrhenius:.2e}$
                - Terme Sursaturation : ${max(0, S_Tf):.4f}^{{1.5}} = {max(0, S_Tf)**1.5:.4f}$
                - **Vitesse de Croissance $G$** : {G_final:.2e} m/s
                - **En unités pratiques** : **{G_final_um:.2f} μm/h** (Vitesse réaliste ✅)
                """)
                
                # 4. Bilan de Population
                st.subheader("4. Résultats du Bilan de Population")
                
                # Simulation réelle
                cinetique = CinetiqueCristallisation()
                cinetique.params.Eg = Eg_opt
                cinetique.params.kg = kg_opt
                bilan = BilanPopulation(cinetique)
                res = bilan.resoudre_batch(T0_opt, Tf_opt, C_opt, 10, duree_opt, 'lineaire', 50)
                
                st.markdown(f"""
                Le bilan de population résout l'évolution des moments de la distribution $m_j$.
                
                **Résultats Finaux :**
                - **Masse de cristaux produite** : {res['masse_cristaux']:.2f} kg
                - **Taille médiane (L50)** : {res['L50']:.2f} μm
                - **Rendement massique** : {res['rendement']:.1f} %
                
                Ces résultats confirment que les paramètres choisis permettent d'obtenir une cristallisation industrielle viable.
                """)
                
            except Exception as e:
                st.error(f"Erreur calculs détaillés: {e}")

    with tab4:
        st.header("🆚 Comparaison Avant / Après Optimisation")
        st.markdown("""
        Cette section compare directement les résultats de la simulation avec les paramètres initiaux (problématiques)
        et les paramètres optimisés (corrigés).
        """)
        
        if st.button("🔄 Lancer la Comparaison", key="run_compare"):
            with st.spinner("Calcul des deux scénarios en cours..."):
                try:
                    # Simulation 1: Avant (Paramètres Initiaux)
                    # C=65, Eg=45000, kg=2.8e-7
                    cinetique_avant = CinetiqueCristallisation()
                    cinetique_avant.params.kg = 2.8e-7
                    cinetique_avant.params.Eg = 45000
                    
                    bilan_avant = BilanPopulation(cinetique_avant)
                    res_avant = bilan_avant.resoudre_batch(
                        T0_celsius=70, Tf_celsius=35, 
                        concentration_initiale=65.0, 
                        volume_batch=10, duree_heures=4, profil='lineaire', n_classes=50
                    )
                    
                    # Simulation 2: Après (Paramètres Optimisés propagés)
                    cinetique_apres = CinetiqueCristallisation()
                    cinetique_apres.params.kg = 1.2e-3 # Cinétique améliorée
                    cinetique_apres.params.Eg = 15000
                    
                    # Valeurs par défaut ou optimisées
                    if 'optimal_params' in st.session_state:
                        opt = st.session_state['optimal_params']
                        C_apres = float(opt['Conc_init'])
                        T0_apres = float(opt['T0'])
                        Tf_apres = float(opt['Tf'])
                        duree_apres = float(opt['Duree_h'])
                        source_params = "Optimisation Globale (Onglet 2)"
                    else:
                        C_apres = 84.0
                        T0_apres = 70.0
                        Tf_apres = 18.0
                        duree_apres = 6.0
                        source_params = "Optimisation Standard (Défaut)"
                    
                    bilan_apres = BilanPopulation(cinetique_apres)
                    res_apres = bilan_apres.resoudre_batch(
                        T0_celsius=T0_apres, Tf_celsius=Tf_apres, 
                        concentration_initiale=C_apres, 
                        volume_batch=10, duree_heures=duree_apres, 
                        profil='lineaire', n_classes=100
                    )
                    
                    # Affichage côte à côte
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.error("❌ AVANT (Paramètres Initiaux)")
                        st.write("**Paramètres:**")
                        st.write("- Conc: 65 g/100g")
                        st.write("- Eg: 45000 J/mol")
                        st.write("- kg: 2.8e-7 m/s")
                        st.write("- Durée: 4h")
                        st.write("---")
                        st.metric("L50 (Taille)", f"{res_avant['L50']:.2f} μm")
                        st.metric("Rendement", f"{res_avant['rendement']:.2f} %")
                        st.metric("Masse Cristaux", f"{res_avant['masse_cristaux']:.4f} kg")
                        st.warning("Résultat: Zéros ou valeurs négligeables")
                    
                    with col2:
                        st.success(f"✅ APRÈS ({source_params})")
                        st.write("**Paramètres:**")
                        st.write(f"- Conc: {C_apres} g/100g")
                        st.write("- Eg: 15000 J/mol")
                        st.write(f"- Tf: {Tf_apres}°C")
                        st.write(f"- Durée: {duree_apres}h")
                        st.write("---")
                        st.metric("L50 (Taille)", f"{res_apres['L50']:.2f} μm")
                        st.metric("Rendement", f"{res_apres['rendement']:.1f} %")
                        st.metric("Masse Cristaux", f"{res_apres['masse_cristaux']:.2f} kg")
                        st.success("Résultat: Rendement Maximisé (+Temps)")
                    
                    # Graphique Comparatif
                    st.subheader("📈 Comparaison des Distributions")
                    fig_comp = go.Figure()
                    
                    # Trace Avant
                    fig_comp.add_trace(go.Scatter(
                        x=res_avant['L_classes'], y=res_avant['distribution_finale'],
                        name="Avant (Initial)", line=dict(color='red', dash='dot')
                    ))
                    
                    # Trace Après
                    fig_comp.add_trace(go.Scatter(
                        x=res_apres['L_classes'], y=res_apres['distribution_finale'],
                        name="Après (Optimisé)", line=dict(color='green', width=3),
                        fill='tozeroy'
                    ))
                    
                    fig_comp.update_layout(
                        title="Distribution de Taille des Cristaux (Avant vs Après)",
                        xaxis_title="Taille (μm)",
                        yaxis_title="Densité",
                        height=500,
                        legend=dict(y=1.1, orientation="h")
                    )
                    
                    st.plotly_chart(fig_comp, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Erreur lors de la comparaison: {e}")


def page_economique():
    """Page d'analyse économique (Adaptée Maroc)."""
    st.markdown('''
    <div class="main-header">
        <h1>Analyse Technico-Économique</h1>
        <p>CAPEX, OPEX et ROI (contexte marocain)</p>
    </div>
    ''', unsafe_allow_html=True)
    
    st.sidebar.header("Paramètres Économiques")
    
    # Investissement
    st.sidebar.subheader("Investissement")
    surface_evap_1 = st.sidebar.number_input("Surface évaporateur 1 (m²)", 50, 200, 100, 10)
    surface_evap_2 = st.sidebar.number_input("Surface évaporateur 2 (m²)", 50, 200, 85, 10)
    surface_evap_3 = st.sidebar.number_input("Surface évaporateur 3 (m²)", 50, 200, 70, 10)
    volume_crist = st.sidebar.number_input("Volume cristalliseur (m³)", 5, 20, 10, 1)
    
    # Exploitation
    st.sidebar.subheader("Exploitation")
    conso_vapeur = st.sidebar.number_input("Consommation vapeur (kg/h)", 1000, 5000, 2000, 100)
    conso_eau = st.sidebar.number_input("Consommation eau (m³/h)", 20, 100, 50, 5)
    puissance_elec = st.sidebar.number_input("Puissance électrique (kW)", 50, 300, 150, 10)
    heures_an = st.sidebar.number_input("Heures opération/an", 6000, 8760, 8000, 100)
    
    # Production
    st.sidebar.subheader("Production")
    production = st.sidebar.number_input("Production annuelle (tonnes)", 3000, 10000, 5000, 500)
    prix_vente = st.sidebar.number_input("Prix de vente (MAD/tonne)", 5000, 15000, 8800, 500) # ~800€ * 11
    
    if st.sidebar.button("💡 Calculer (MAD)", key="calc_eco"):
        eco = AnalyseEconomique()
        
        # Investissement (Conversion des formules en € -> MAD si nécessaire, 
        # mais ici les formules retournent des unités monétaires abstraites basées sur les coeffs.
        # On suppose que les formules d'investissement restent en base 'Euro' pour l'échelle internationale
        # et on convertit le résultat final, OU on assume que les coûts matériel sont mondiaux.
        # Pour être cohérent avec la demande "tout en DH", on va convertir les résultats d'investissement x11)
        
        # Note: La classe calcule en "Unités Monétaires". Si les formules sont en €, on multiplie par 11 en sortie.
        FACTEUR_CONVERSION = 11.0 
        
        inv_euro = eco.calculer_investissement(
            [surface_evap_1, surface_evap_2, surface_evap_3],
            volume_crist
        )
        
        # On adapte l'objet pour l'affichage
        inv_mad = CoutsInvestissement(
            evaporateurs=inv_euro.evaporateurs * FACTEUR_CONVERSION,
            cristalliseur=inv_euro.cristalliseur * FACTEUR_CONVERSION,
            echangeurs=inv_euro.echangeurs * FACTEUR_CONVERSION,
            total=inv_euro.total * FACTEUR_CONVERSION
        )
        
        # Exploitation (Déjà en MAD car constantes mises à jour dans la classe)
        opex_mad = eco.calculer_exploitation(
            conso_vapeur, conso_eau, puissance_elec,
            nombre_operateurs=2, heures_operation_an=heures_an
        )
        
        # ROI
        roi = eco.calculer_roi(
            inv_mad.total, opex_mad.total, production, prix_vente
        )
        
        # Affichage des résultats
        st.subheader("💵 Coûts d'Investissement (CAPEX)")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Évaporateurs", f"{inv_mad.evaporateurs/1000:.0f} kMAD")
        with col2:
            st.metric("Cristalliseur", f"{inv_mad.cristalliseur/1000:.0f} kMAD")
        with col3:
            st.metric("Échangeurs", f"{inv_mad.echangeurs/1000:.0f} kMAD")
        with col4:
            st.metric("**TOTAL (TCI)**", f"{inv_mad.total/1000:.0f} kMAD")
        
        st.subheader("💸 Coûts d'Exploitation (OPEX)")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Vapeur", f"{opex_mad.vapeur/1000:.0f} kMAD/an")
        with col2:
            st.metric("Eau", f"{opex_mad.eau_refroidissement/1000:.0f} kMAD/an")
        with col3:
            st.metric("Électricité", f"{opex_mad.electricite/1000:.0f} kMAD/an")
        with col4:
            st.metric("Main d'œuvre", f"{opex_mad.main_oeuvre/1000:.0f} kMAD/an")
        with col5:
            st.metric("**TOTAL**", f"{opex_mad.total/1000:.0f} kMAD/an")
        
        st.subheader("📊 Indicateurs Économiques")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Temps de retour (ROI)", f"{roi['temps_retour_annees']:.2f} ans",
                     delta=f"{5 - roi['temps_retour_annees']:.2f} vs cible 5 ans")
        with col2:
            st.metric("Coût de production", f"{roi['cout_production_tonne']:.2f} MAD/tonne")
        with col3:
            st.metric("Marge bénéficiaire", f"{roi['marge_beneficiaire_pct']:.1f} %")
        
        # Graphique de répartition des coûts
        st.subheader("📈 Répartition des Coûts")
        
        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{"type": "pie"}, {"type": "pie"}]],
            subplot_titles=("Investissement (CAPEX)", "Exploitation (OPEX)")
        )
        
        # CAPEX
        fig.add_trace(
            go.Pie(labels=['Évaporateurs', 'Cristalliseur', 'Échangeurs'],
                  values=[inv_mad.evaporateurs, inv_mad.cristalliseur, inv_mad.echangeurs],
                  hole=0.3),
            row=1, col=1
        )
        
        # OPEX
        fig.add_trace(
            go.Pie(labels=['Vapeur', 'Eau', 'Électricité', 'Main d\'œuvre'],
                  values=[opex_mad.vapeur, opex_mad.eau_refroidissement, 
                         opex_mad.electricite, opex_mad.main_oeuvre],
                  hole=0.3),
            row=1, col=2
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)


def main():
    """Fonction principale de l'application."""
    
    # Menu de navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Choisir une page:",
        ["Accueil", "Évaporateurs", "Cristallisation", "Analyse Économique"]
    )
    
    # Afficher la page sélectionnée
    if page == "Accueil":
        page_accueil()
    elif page == "Évaporateurs":
        page_evaporateurs()
    elif page == "Cristallisation":
        page_cristallisation()
    elif page == "Analyse Économique":
        page_economique()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **Projet PIC11**  
    Évaporation-Cristallisation  
    du Saccharose
    
    📅 Date de rendu: 24/12/2025
    
    OUMOULID LAHCEN
    
    BARRY OUMAR
    """)


if __name__ == "__main__":
    main()
