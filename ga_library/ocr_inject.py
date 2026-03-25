#!/usr/bin/env python3
"""
OCR injection script — adds ocr_text, ocr_words, and ocr_word_count
to each GA JSON sidecar based on visual text extraction from chart images.

Since these are programmatically generated charts, the OCR text was extracted
via multimodal vision reading of each PNG file.
"""
import json
import os
import re

GA_DIR = os.path.dirname(os.path.abspath(__file__))

# OCR data extracted from visual reading of each image
OCR_DATA = {
    "attention_transformer_2017": {
        "ocr_text": "Machine Translation — WMT 2014 EN→DE\nVaswani et al., \"Attention Is All You Need\" (2017)\nBLEU Score (EN→DE)\n30\n29\n28.4\n28\n27.3\n27\n26\n25.2\n25\n24.6\n24\n23\n22\nGNMT+RL (Google)\nConvS2S (Gehring)\nTransformer (Base)\nTransformer (Big)\nSource: Vaswani et al., NeurIPS 2017"
    },
    "attention_transformer_2017_pie_control": {
        "ocr_text": "Machine Translation — BLEU Score Distribution (WMT 2014 EN-DE)\nPie chart encoding — area-based, perceptually misleading for close values\n26.9%\n23.3%\n25.9%\n23.9%\nTransformer (Big): 28.4 BLEU\nTransformer (Base): 27.3 BLEU\nConvS2S: 25.2 BLEU\nGNMT+RL: 24.6 BLEU\nSource: Vaswani et al., NeurIPS 2017"
    },
    "battery_energy_density_2023": {
        "ocr_text": "Battery Technologies — Energy Density Comparison (2023)\nSolid-state 400\nLithium-ion 250\nSodium-ion 160\nLead-acid 40\n0 50 100 150 200 250 300 350 400\nWh/kg\nCompiled from DOE & industry benchmarks (2023)."
    },
    "battery_energy_density_2023_control": {
        "ocr_text": "Battery Technologies — Pie chart (control)\nSolid-state (400)\nLithium-ion (250)\nSodium-ion (160)\nLead-acid (40)\nCompiled from DOE & industry benchmarks (2023)."
    },
    "cbt_depression_cuijpers_2020": {
        "ocr_text": "CBT vs Medications for Depression — Meta-analysis (Cuijpers et al., 2020)\nCombined therapy 0.82\nCBT 0.71\nSSRIs 0.53\nPlacebo 0.16\n0.0 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8\nHedges' g\nCuijpers, P. et al. (2020). Meta-analysis of CBT for depression."
    },
    "cbt_depression_cuijpers_2020_control": {
        "ocr_text": "CBT vs Medications for Depression — Pie chart (control)\nCombined therapy (0.82)\nCBT (0.71)\nSSRIs (0.53)\nPlacebo (0.16)\nCuijpers, P. et al. (2020). Meta-analysis of CBT for depression."
    },
    "concrete_co2_alternatives_2023": {
        "ocr_text": "Concrete Alternatives — CO₂ Reduction vs Portland Cement (2023)\nGeopolymer 80\nLC3 40\nFly ash blend 25\nStandard Portland 0\n0 10 20 30 40 50 60 70 80\n% CO₂ reduction\nCompiled from IEA Cement Technology Roadmap & materials science literature."
    },
    "concrete_co2_alternatives_2023_control": {
        "ocr_text": "Concrete Alternatives — Pie chart (control)\nGeopolymer (80)\nLC3 (40)\nFly ash blend (25)\nStandard Portland (0)\nCompiled from IEA Cement Technology Roadmap & materials science literature."
    },
    "coral_recovery_interventions_2020": {
        "ocr_text": "Coral Reef Recovery Interventions — Cover Increase (%)\nCoral gardening 25\nMarine protected areas 15\nPollution control 8\nNo intervention -5\n-5 0 5 10 15 20 25\n% cover change\nCompiled from Boström-Einarsson et al. (2020) & UNEP Coral Reef Reports."
    },
    "coral_recovery_interventions_2020_control": {
        "ocr_text": "Coral Reef Recovery Interventions — Pie chart (control)\nCoral gardening (+25)\nMarine protected areas (+15)\nPollution control (+8)\nNo intervention (-5)\nCompiled from Boström-Einarsson et al. (2020) & UNEP Coral Reef Reports."
    },
    "covid_vaccine_polack_2020": {
        "ocr_text": "COVID-19 Vaccine Efficacy by Subgroup (Polack et al., 2020)\n16-55 years 95.6\n>55 years 93.7\nSevere disease 88.9\nAsymptomatic 75\n0 20 40 60 80\n% efficacy\nPolack, F. P. et al. (2020). Safety and Efficacy of BNT162b2. NEJM."
    },
    "covid_vaccine_polack_2020_control": {
        "ocr_text": "COVID-19 Vaccine Efficacy by Subgroup — Pie chart (control)\n16-55 years (95.6)\n>55 years (93.7)\nSevere disease (88.9)\nAsymptomatic (75)\nPolack, F. P. et al. (2020). Safety and Efficacy of BNT162b2. NEJM."
    },
    "crop_yield_ponisio_2015": {
        "ocr_text": "Crop Yield by Farming Method — Meta-analysis (Ponisio et al., 2015)\nPrecision farming 3\nConservation -5\nIntegrated -8\nOrganic -19\n-20 -15 -10 -5 0\n% yield gap vs conventional\nPonisio, L. C. et al. (2015). Diversification practices reduce the yield gap. Proc. R. Soc. B."
    },
    "crop_yield_ponisio_2015_control": {
        "ocr_text": "Crop Yield by Farming Method — Pie chart (control)\nPrecision farming (+3)\nConservation (-5)\nIntegrated (-8)\nOrganic (-19)\nPonisio, L. C. et al. (2015). Diversification practices reduce the yield gap. Proc. R. Soc. B."
    },
    "drawdown_climate_2017": {
        "ocr_text": "Project Drawdown (Hawken, 2017)\nTop Climate Solutions by CO₂ Reduction Potential\nReduced food waste 70.5 GT\nPlant-rich diets 65.0 GT\nSolar farms 36.9 GT\nElectric vehicles 10.8 GT\n0 10 20 30 40 50 60 70 80 90\nCO₂ reduction (gigatons, 2020–2050)"
    },
    "drawdown_climate_2017_pie_control": {
        "ocr_text": "Project Drawdown — Pie chart (control)\nElectric vehicles (10.8 GT) 6%\nSolar farms (36.9 GT) 20%\nPlant-rich diets (65.0 GT) 35%\nReduced food waste (70.5 GT) 38%"
    },
    "exercise_neuroplasticity_erickson_2011": {
        "ocr_text": "Exercise and Hippocampal Volume Change (Erickson et al., 2011)\nAerobic exercise 2.0\nWalking 0.5\nStretching -1.4\nControl -1.5\n-1.5 -1.0 -0.5 0.0 0.5 1.0 1.5 2.0\n% volume change\nErickson, K. I. et al. (2011). Exercise training increases hippocampal volume. PNAS."
    },
    "exercise_neuroplasticity_erickson_2011_control": {
        "ocr_text": "Exercise and Hippocampal Volume Change — Pie chart (control)\nAerobic exercise (+2)\nWalking (+0.5)\nStretching (-1.4)\nControl (-1.5)\nErickson, K. I. et al. (2011). Exercise training increases hippocampal volume. PNAS."
    },
    "handwashing_aiello_2008": {
        "ocr_text": "Handwashing and Respiratory Infections — Meta-analysis (Aiello et al., 2008)\nSoap and water 24\nHand sanitizer 21\nEducation only 10\nControl 0\n0 5 10 15 20 25\n% risk reduction\nAiello, A. E. et al. (2008). Effect of hand hygiene on infectious disease. AJPH."
    },
    "handwashing_aiello_2008_control": {
        "ocr_text": "Handwashing and Respiratory Infections — Pie chart (control)\nSoap and water (24)\nHand sanitizer (21)\nEducation only (10)\nControl (0)\nAiello, A. E. et al. (2008). Effect of hand hygiene on infectious disease. AJPH."
    },
    "hattie_visible_learning_2009": {
        "ocr_text": "Visible Learning Meta-Analysis (Hattie, 2009)\nEducational Interventions by Effect Size\nFeedback d = 0.73\nDirect instruction d = 0.59\nPeer tutoring d = 0.55\nHomework d = 0.29\n0.0 0.2 0.4 0.6 0.8 1.0\nEffect size (Cohen's d)"
    },
    "hattie_visible_learning_2009_bubble_control": {
        "ocr_text": "Visible Learning — Bubble chart (control)\n1.0\n0.8\nFeedback d=0.73\nDirect instruction d=0.59\nPeer tutoring d=0.55\n0.6\n0.4\nHomework d=0.29\n0.2\n0.0\nEffect size (Cohen's d)"
    },
    "immunomod_v10_wireframe": {
        "ocr_text": "Inflammation Th2\nFracture du Cycle Pathologique\nOM-85\nPMBL\nMV130\nConvergence vers la Protection (IgA)\nAggression virale\nRe-susceptibilité\nLe Cercle Vicieux de l'Asthme\nRemodelage des voies respiratoires\nCRL1505\nHiérarchie de l'Évidence Scientifique\nOM-85 (18 RCTs)\nPMBL (5 RCTs)\nMV130 (1 RCT)\nCRL1505 (Préclinique)\nRéduction majeure des infections de 40% en fréquence\nRéduction des exacerbations d'asthme allergique\nDiminution de 40% des épisodes de sifflements\nVia muqueuse intestinale pouvant moduler l'immunité"
    },
    "immunomod_v10_area_control": {
        "ocr_text": "Immunomodulateurs — Niveau de preuve clinique\nEncodage par aire (cercles proportionnels)\nOM-85 18 RCTs\nPMBL 5 RCTs\nMV130 1 RCT\nCRL1505 Preclinical\nArea encoding: Stevens β=0.7 — perceptual compression\nSource: Inchauspe, MDPI Children 2026"
    },
    "immunomod_v2a4_infographic": {
        "ocr_text": "Briser le Cercle Vicieux des Infections Respiratoires Pédiatriques\nOM-85\nPMBL\nMV130\nConvergence vers la Protection (IgA)\nAggression virale\nRe-susceptibilité\nLe Cercle Vicieux de l'Asthme\nRemodelage des voies respiratoires\nCRL1505\nInflammation Th2\nFracture du Cycle Pathologique\nHiérarchie de l'Évidence Scientifique\nOM-85 (18 RCTs) Réduction majeure des infections de 40% en fréquence\nPMBL (5 RCTs) Réduction des exacerbations d'asthme allergique\nMV130 (1 RCT) Diminution de 40% des épisodes de sifflements\nCRL1505 (Préclinique) Via muqueuse intestinale pouvant moduler l'immunité\nNotebookLM"
    },
    "marshmallow_watts_2018": {
        "ocr_text": "Marshmallow Test Replication — Effect Sizes (Watts et al., 2018)\nAcademic achievement 0.32\nBehavioral problems 0.12\nSAT scores 0.08\nBMI 0.05\n0.00 0.05 0.10 0.15 0.20 0.25 0.30\nCohen's d\nWatts, T. W. et al. (2018). Revisiting the Marshmallow Test. Psych Science."
    },
    "marshmallow_watts_2018_control": {
        "ocr_text": "Marshmallow Test Replication — Pie chart (control)\nAcademic achievement (0.32)\nBehavioral problems (0.12)\nSAT scores (0.08)\nBMI (0.05)\nWatts, T. W. et al. (2018). Revisiting the Marshmallow Test. Psych Science."
    },
    "microfinance_banerjee_2015": {
        "ocr_text": "Microfinance Impact on Business Profits — 6-Country RCT (Banerjee et al., 2015)\nIndia 27\nMexico 20\nMongolia 11\nEthiopia 5\n0 5 10 15 20 25\n% profit increase\nBanerjee, A. et al. (2015). Six Randomized Evaluations of Microcredit. AEJ:Applied."
    },
    "microfinance_banerjee_2015_control": {
        "ocr_text": "Microfinance Impact on Business Profits — Pie chart (control)\nIndia (27)\nMexico (20)\nMongolia (11)\nEthiopia (5)\nBanerjee, A. et al. (2015). Six Randomized Evaluations of Microcredit. AEJ:Applied."
    },
    "minimum_wage_card_krueger_1994": {
        "ocr_text": "Minimum Wage and Employment — Card & Krueger (1994)\nNJ fast food 13\nNJ full-service 3\nPA full-service -1\nPA fast food -2.2\n-2 0 2 4 6 8 10 12\n% employment change\nCard, D. & Krueger, A. (1994). Minimum Wages and Employment. AER."
    },
    "minimum_wage_card_krueger_1994_control": {
        "ocr_text": "Minimum Wage and Employment — Pie chart (control)\nNJ fast food (+13)\nNJ full-service (+3)\nPA full-service (-1)\nPA fast food (-2.2)\nCard, D. & Krueger, A. (1994). Minimum Wages and Employment. AER."
    },
    "modal_emissions_itf_2021": {
        "ocr_text": "CO₂ Emissions per Passenger-km by Transport Mode (ITF, 2021)\nCar 170\nBus 65\nTrain 14\nBicycle 0\n0 20 40 60 80 100 120 140 160\ng CO₂/pkm\nInternational Transport Forum (2021). Transport CO₂ and the Paris Agreement."
    },
    "modal_emissions_itf_2021_control": {
        "ocr_text": "CO₂ Emissions per Passenger-km by Transport Mode — Pie chart (control)\nCar (170)\nBus (65)\nTrain (14)\nBicycle (0)\nInternational Transport Forum (2021). Transport CO₂ and the Paris Agreement."
    },
    "obedience_milgram_1963": {
        "ocr_text": "Obedience to Authority — Milgram Experiment (1963)\nBaseline 65\nRemote feedback 40\nTouch proximity 30\nExperimenter absent 20\n0 10 20 30 40 50 60\n% obedience\nMilgram, S. (1963). Behavioral Study of Obedience. JASP."
    },
    "obedience_milgram_1963_control": {
        "ocr_text": "Obedience to Authority — Pie chart (control)\nBaseline (65)\nRemote feedback (40)\nTouch proximity (30)\nExperimenter absent (20)\nMilgram, S. (1963). Behavioral Study of Obedience. JASP."
    },
    "oregon_health_experiment_2012": {
        "ocr_text": "Oregon Health Insurance Experiment\nMedicaid Coverage vs No Coverage — 4 Health Outcomes\nPhysical health 0%\nFinancial strain -25%\nDepression screening +30%\nEmergency visits +40%\n-40 -20 0 20 40\nEffect size (% change)"
    },
    "oregon_health_experiment_2012_pie_control": {
        "ocr_text": "Oregon Health Insurance Experiment — Pie (control)\nPhysical health (0%) 5%\nFinancial strain (-25%) 25%\nDepression screening (+30%) 30%\nEmergency visits (+40%) 40%"
    },
    "pollinator_decline_potts_2010": {
        "ocr_text": "Pollinator Decline Drivers — Relative Impact (Potts et al., 2010)\nHabitat loss 45\nPesticides 25\nClimate change 15\nInvasive species 10\n0 10 20 30 40\n% relative impact\nPotts, S. G. et al. (2010). Global pollinator declines. Trends in Ecology & Evolution."
    },
    "pollinator_decline_potts_2010_control": {
        "ocr_text": "Pollinator Decline Drivers — Pie chart (control)\nHabitat loss (45)\nPesticides (25)\nClimate change (15)\nInvasive species (10)\nPotts, S. G. et al. (2010). Global pollinator declines. Trends in Ecology & Evolution."
    },
    "predimed_estruch_2018": {
        "ocr_text": "Mediterranean Diet and Cardiovascular Risk — PREDIMED (Estruch et al., 2018)\nMed + EVOO 31\nMed + Nuts 28\nLow-fat diet 6\nControl diet 0\n0 5 10 15 20 25 30\n% CV risk reduction\nEstruch, R. et al. (2018). Primary Prevention of CVD with Mediterranean Diet. NEJM."
    },
    "predimed_estruch_2018_control": {
        "ocr_text": "Mediterranean Diet and Cardiovascular Risk — Pie chart (control)\nMed + EVOO (31)\nMed + Nuts (28)\nLow-fat diet (6)\nControl diet (0)\nEstruch, R. et al. (2018). Primary Prevention of CVD with Mediterranean Diet. NEJM."
    },
    "renewable_lcoe_lazard_2023": {
        "ocr_text": "Renewable Energy LCOE Comparison (Lazard, 2023)\nNuclear 141\nGas combined 45\nWind onshore 29\nSolar utility 24\n0 20 40 60 80 100 120 140\n$/MWh\nLazard's Levelized Cost of Energy Analysis, v16.0 (2023)."
    },
    "renewable_lcoe_lazard_2023_control": {
        "ocr_text": "Renewable Energy LCOE Comparison — Pie chart (control)\nSolar utility (24)\nWind onshore (29)\nGas combined (45)\nNuclear (141)\nLazard's Levelized Cost of Energy Analysis, v16.0 (2023)."
    },
    "sleep_memory_walker_2009": {
        "ocr_text": "Sleep Stages and Memory Consolidation (Walker, 2009)\nFull night sleep 94\nNap 85\nFragmented sleep 72\nSleep deprived 60\n0 20 40 60 80\n% retention\nWalker, M. P. (2009). The Role of Sleep in Cognition and Emotion. ANYAS."
    },
    "sleep_memory_walker_2009_control": {
        "ocr_text": "Sleep Stages and Memory Consolidation — Pie chart (control)\nFull night sleep (94)\nNap (85)\nFragmented sleep (72)\nSleep deprived (60)\nWalker, M. P. (2009). The Role of Sleep in Cognition and Emotion. ANYAS."
    },
    "sugar_tax_teng_2019": {
        "ocr_text": "Sugar Tax Effects on Consumption — Meta-analysis (Teng et al., 2019)\nPhiladelphia 38\nBerkeley 21\nUK 10\nMexico 7.6\n0 5 10 15 20 25 30 35\n% consumption reduction\nTeng, A. M. et al. (2019). Impact of sugar-sweetened beverage taxes. BMJ."
    },
    "sugar_tax_teng_2019_control": {
        "ocr_text": "Sugar Tax Effects on Consumption — Pie chart (control)\nPhiladelphia (38)\nBerkeley (21)\nUK (10)\nMexico (7.6)\nTeng, A. M. et al. (2019). Impact of sugar-sweetened beverage taxes. BMJ."
    },
}


def extract_words(text: str) -> list[str]:
    """Extract individual words from OCR text, filtering out pure numbers and symbols."""
    # Split on whitespace and newlines
    raw_tokens = re.split(r'[\s\n]+', text)
    words = []
    for token in raw_tokens:
        # Strip common punctuation from edges
        cleaned = token.strip('.,;:()[]{}""\'—–-')
        if cleaned and len(cleaned) > 0:
            words.append(cleaned)
    return words


def update_json_file(json_path: str, ocr_text: str):
    """Read existing JSON, add OCR fields, write back."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    words = extract_words(ocr_text)

    data['ocr_text'] = ocr_text
    data['ocr_words'] = words
    data['ocr_word_count'] = len(words)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return len(words)


def main():
    updated = 0
    skipped = 0

    for base_name, ocr_info in OCR_DATA.items():
        json_path = os.path.join(GA_DIR, f"{base_name}.json")

        if not os.path.exists(json_path):
            print(f"  SKIP (no JSON): {base_name}")
            skipped += 1
            continue

        ocr_text = ocr_info['ocr_text']
        word_count = update_json_file(json_path, ocr_text)
        print(f"  OK: {base_name}.json — {word_count} words")
        updated += 1

    print(f"\nDone: {updated} updated, {skipped} skipped")


if __name__ == '__main__':
    main()
