#!/usr/bin/env python3
"""
GLANCE GA Library Generator — 18 papers × 2 versions = 36 images + 36 JSONs.
Produces VEC bar charts (β≈1.0) and control pie charts (β≈0.7).
"""

import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Color palette (distinct, colorblind-friendly) ──────────────────────
COLORS = [
    "#60a5fa",  # blue
    "#f97316",  # orange
    "#34d399",  # green
    "#f472b6",  # pink
    "#a78bfa",  # purple
    "#fbbf24",  # amber
    "#38bdf8",  # sky
    "#fb7185",  # rose
]

BG_COLOR = "#0f172a"
TEXT_COLOR = "#e2e8f0"
GRID_COLOR = "#1e293b"

# ── Paper definitions ──────────────────────────────────────────────────

PAPERS = [
    # --- Psychology (3) ---
    {
        "slug": "obedience_milgram_1963",
        "domain": "psychology",
        "version": "Milgram1963",
        "title": "Obedience to Authority — Milgram Experiment (1963)",
        "description": "Percentage of participants delivering maximum shock by experimental condition. Milgram's classic study showed 65% full obedience in the baseline condition, dropping sharply with increased proximity to the victim.",
        "source": "Milgram, S. (1963). Behavioral Study of Obedience. JASP.",
        "labels": ["Baseline", "Remote feedback", "Touch proximity", "Experimenter absent"],
        "values": [65, 40, 30, 20],
        "unit": "% obedience",
        "correct": "Baseline",
        "semantic_references": {
            "L1_broad": [
                "social psychology", "obedience", "authority",
                "psychologie sociale", "obéissance"
            ],
            "L2_specific": [
                "Milgram obedience experiment conditions comparison",
                "obéissance à l'autorité selon la proximité avec la victime",
                "social influence and compliance in laboratory settings",
                "effet de la proximité sur le comportement d'obéissance"
            ],
            "L3_detailed": [
                "the baseline Milgram condition shows the highest obedience rate at 65%",
                "la condition de base de Milgram montre le taux d'obéissance le plus élevé à 65%",
                "proximity to the victim reduces obedience from 65% to 30% in touch condition"
            ]
        }
    },
    {
        "slug": "marshmallow_watts_2018",
        "domain": "psychology",
        "version": "Watts2018",
        "title": "Marshmallow Test Replication — Effect Sizes (Watts et al., 2018)",
        "description": "Effect sizes (Cohen's d) of delayed gratification on later-life outcomes. The replication found a small effect on academic achievement (d=0.32) but negligible effects on BMI and behavioral outcomes.",
        "source": "Watts, T. W. et al. (2018). Revisiting the Marshmallow Test. Psych Science.",
        "labels": ["Academic achievement", "Behavioral problems", "SAT scores", "BMI"],
        "values": [0.32, 0.12, 0.08, 0.05],
        "unit": "Cohen's d",
        "correct": "Academic achievement",
        "semantic_references": {
            "L1_broad": [
                "developmental psychology", "self-control", "delayed gratification",
                "psychologie du développement", "contrôle de soi"
            ],
            "L2_specific": [
                "marshmallow test replication effect sizes on life outcomes",
                "réplication du test du marshmallow et tailles d'effet",
                "delayed gratification predicts academic achievement more than health",
                "le contrôle de soi prédit les résultats scolaires mais pas la santé"
            ],
            "L3_detailed": [
                "academic achievement shows the largest effect size (d=0.32) in marshmallow replication",
                "la réussite scolaire montre le plus grand effet (d=0.32) dans la réplication",
                "BMI and behavioral problems show negligible effects of delayed gratification"
            ]
        }
    },
    {
        "slug": "cbt_depression_cuijpers_2020",
        "domain": "psychology",
        "version": "Cuijpers2020",
        "title": "CBT vs Medications for Depression — Meta-analysis (Cuijpers et al., 2020)",
        "description": "Effect sizes (Hedges' g) of different treatments for depression. Combined therapy (CBT + SSRIs) yields the largest effect (g=0.82), followed by CBT alone (g=0.71).",
        "source": "Cuijpers, P. et al. (2020). Meta-analysis of CBT for depression.",
        "labels": ["Combined therapy", "CBT", "SSRIs", "Placebo"],
        "values": [0.82, 0.71, 0.53, 0.16],
        "unit": "Hedges' g",
        "correct": "Combined therapy",
        "semantic_references": {
            "L1_broad": [
                "clinical psychology", "depression treatment", "psychotherapy",
                "psychologie clinique", "traitement de la dépression"
            ],
            "L2_specific": [
                "CBT versus medication effect sizes for depression treatment",
                "comparaison thérapie cognitive-comportementale et antidépresseurs",
                "combined therapy superiority over monotherapy for depression",
                "la thérapie combinée surpasse la monothérapie contre la dépression"
            ],
            "L3_detailed": [
                "combined CBT + SSRI therapy shows the largest effect size (g=0.82)",
                "la thérapie combinée TCC + ISRS montre le plus grand effet (g=0.82)",
                "CBT alone outperforms SSRIs alone for depression in meta-analysis"
            ]
        }
    },
    # --- Economics (2) ---
    {
        "slug": "minimum_wage_card_krueger_1994",
        "domain": "economics",
        "version": "CardKrueger1994",
        "title": "Minimum Wage and Employment — Card & Krueger (1994)",
        "description": "Employment change (%) after NJ minimum wage increase. NJ fast food employment rose +13%, contradicting the classical prediction of job loss, while PA (control) declined slightly.",
        "source": "Card, D. & Krueger, A. (1994). Minimum Wages and Employment. AER.",
        "labels": ["NJ fast food", "NJ full-service", "PA full-service", "PA fast food"],
        "values": [13, 3, -1, -2.2],
        "unit": "% employment change",
        "correct": "NJ fast food",
        "semantic_references": {
            "L1_broad": [
                "labor economics", "minimum wage", "employment",
                "économie du travail", "salaire minimum"
            ],
            "L2_specific": [
                "minimum wage increase effect on fast food employment",
                "effet de l'augmentation du salaire minimum sur l'emploi restauration",
                "Card and Krueger natural experiment New Jersey Pennsylvania",
                "expérience naturelle salaire minimum New Jersey Pennsylvanie"
            ],
            "L3_detailed": [
                "NJ fast food employment increased 13% after minimum wage rise",
                "l'emploi fast food au New Jersey a augmenté de 13% après la hausse du SMIC",
                "contradicts classical prediction that minimum wage increases reduce employment"
            ]
        }
    },
    {
        "slug": "microfinance_banerjee_2015",
        "domain": "economics",
        "version": "Banerjee2015",
        "title": "Microfinance Impact on Business Profits — 6-Country RCT (Banerjee et al., 2015)",
        "description": "Business profit increase (%) from microfinance across 6-country RCT. India shows the largest impact (+27%), while Ethiopia shows minimal effects (+5%).",
        "source": "Banerjee, A. et al. (2015). Six Randomized Evaluations of Microcredit. AEJ:Applied.",
        "labels": ["India", "Mexico", "Mongolia", "Ethiopia"],
        "values": [27, 20, 11, 5],
        "unit": "% profit increase",
        "correct": "India",
        "semantic_references": {
            "L1_broad": [
                "development economics", "microfinance", "poverty",
                "économie du développement", "microfinance"
            ],
            "L2_specific": [
                "microfinance RCT business profits by country",
                "impact du microcrédit sur les profits des entreprises par pays",
                "randomized evaluation of microfinance in developing countries",
                "évaluation randomisée du microcrédit dans les pays en développement"
            ],
            "L3_detailed": [
                "India shows the largest microfinance business profit increase at 27%",
                "l'Inde montre la plus grande augmentation de profits par microcrédit à 27%",
                "six-country RCT shows heterogeneous microfinance effects across contexts"
            ]
        }
    },
    # --- Neuroscience (2) ---
    {
        "slug": "sleep_memory_walker_2009",
        "domain": "neuroscience",
        "version": "Walker2009",
        "title": "Sleep Stages and Memory Consolidation (Walker, 2009)",
        "description": "Memory retention (%) by sleep condition. Full night sleep achieves 94% retention, while sleep deprivation drops to 60%, demonstrating sleep's critical role in memory consolidation.",
        "source": "Walker, M. P. (2009). The Role of Sleep in Cognition and Emotion. ANYAS.",
        "labels": ["Full night sleep", "Nap", "Fragmented sleep", "Sleep deprived"],
        "values": [94, 85, 72, 60],
        "unit": "% retention",
        "correct": "Full night sleep",
        "semantic_references": {
            "L1_broad": [
                "neuroscience", "sleep", "memory",
                "neurosciences", "sommeil", "mémoire"
            ],
            "L2_specific": [
                "sleep stages and memory consolidation comparison",
                "consolidation mnésique selon les conditions de sommeil",
                "full night sleep vs deprivation effect on retention",
                "effet de la privation de sommeil sur la rétention mnésique"
            ],
            "L3_detailed": [
                "full night sleep achieves 94% memory retention vs 60% when sleep deprived",
                "une nuit complète permet 94% de rétention vs 60% en privation de sommeil",
                "even napping (85%) significantly outperforms sleep deprivation for memory"
            ]
        }
    },
    {
        "slug": "exercise_neuroplasticity_erickson_2011",
        "domain": "neuroscience",
        "version": "Erickson2011",
        "title": "Exercise and Hippocampal Volume Change (Erickson et al., 2011)",
        "description": "Hippocampal volume change (%) by exercise type. Aerobic exercise uniquely increases hippocampal volume (+2%), while stretching and control groups show volume decline.",
        "source": "Erickson, K. I. et al. (2011). Exercise training increases hippocampal volume. PNAS.",
        "labels": ["Aerobic exercise", "Walking", "Stretching", "Control"],
        "values": [2.0, 0.5, -1.4, -1.5],
        "unit": "% volume change",
        "correct": "Aerobic exercise",
        "semantic_references": {
            "L1_broad": [
                "neuroscience", "exercise", "neuroplasticity",
                "neurosciences", "exercice physique", "neuroplasticité"
            ],
            "L2_specific": [
                "exercise effect on hippocampal volume in older adults",
                "effet de l'exercice sur le volume hippocampique chez les seniors",
                "aerobic exercise increases brain volume neuroplasticity",
                "l'exercice aérobique augmente le volume cérébral"
            ],
            "L3_detailed": [
                "aerobic exercise increases hippocampal volume by 2% in older adults",
                "l'exercice aérobique augmente le volume hippocampique de 2% chez les seniors",
                "control group shows 1.5% hippocampal decline highlighting age-related atrophy"
            ]
        }
    },
    # --- Nutrition / Public Health (2) ---
    {
        "slug": "predimed_estruch_2018",
        "domain": "nutrition",
        "version": "Estruch2018",
        "title": "Mediterranean Diet and Cardiovascular Risk — PREDIMED (Estruch et al., 2018)",
        "description": "Reduction in major cardiovascular events (%) by dietary intervention. Mediterranean diet supplemented with extra-virgin olive oil achieves the largest risk reduction (-31%).",
        "source": "Estruch, R. et al. (2018). Primary Prevention of CVD with Mediterranean Diet. NEJM.",
        "labels": ["Med + EVOO", "Med + Nuts", "Low-fat diet", "Control diet"],
        "values": [31, 28, 6, 0],
        "unit": "% CV risk reduction",
        "correct": "Med + EVOO",
        "semantic_references": {
            "L1_broad": [
                "nutrition", "cardiovascular disease", "diet",
                "nutrition", "maladie cardiovasculaire", "régime alimentaire"
            ],
            "L2_specific": [
                "Mediterranean diet cardiovascular risk reduction PREDIMED trial",
                "réduction du risque cardiovasculaire par le régime méditerranéen",
                "olive oil and nuts supplementation prevents cardiovascular events",
                "supplémentation huile d'olive et noix en prévention cardiovasculaire"
            ],
            "L3_detailed": [
                "Mediterranean diet with EVOO reduces major cardiovascular events by 31%",
                "le régime méditerranéen à l'huile d'olive réduit les événements CV de 31%",
                "PREDIMED shows Mediterranean diet superiority over low-fat diet for CVD prevention"
            ]
        }
    },
    {
        "slug": "sugar_tax_teng_2019",
        "domain": "nutrition",
        "version": "Teng2019",
        "title": "Sugar Tax Effects on Consumption — Meta-analysis (Teng et al., 2019)",
        "description": "Reduction in sugary drink consumption (%) following sugar tax implementation. Philadelphia shows the largest effect (-38%), while Mexico shows a more modest -7.6%.",
        "source": "Teng, A. M. et al. (2019). Impact of sugar-sweetened beverage taxes. BMJ.",
        "labels": ["Philadelphia", "Berkeley", "UK", "Mexico"],
        "values": [38, 21, 10, 7.6],
        "unit": "% consumption reduction",
        "correct": "Philadelphia",
        "semantic_references": {
            "L1_broad": [
                "public health", "sugar tax", "nutrition policy",
                "santé publique", "taxe sur le sucre", "politique nutritionnelle"
            ],
            "L2_specific": [
                "sugar-sweetened beverage tax effect on consumption by city",
                "effet de la taxe sur les boissons sucrées par ville",
                "fiscal policy intervention reducing sugar intake worldwide",
                "intervention fiscale réduisant la consommation de sucre"
            ],
            "L3_detailed": [
                "Philadelphia's sugar tax achieved the largest consumption reduction at 38%",
                "la taxe de Philadelphie a obtenu la plus forte réduction de consommation à 38%",
                "sugar taxes reduce consumption but magnitude varies widely by jurisdiction"
            ]
        }
    },
    # --- Energy / Engineering (2) ---
    {
        "slug": "battery_energy_density_2023",
        "domain": "energy",
        "version": "Battery2023",
        "title": "Battery Technologies — Energy Density Comparison (2023)",
        "description": "Energy density (Wh/kg) of battery technologies. Solid-state batteries lead at 400 Wh/kg, 60% higher than conventional lithium-ion, representing the next generation of energy storage.",
        "source": "Compiled from DOE & industry benchmarks (2023).",
        "labels": ["Solid-state", "Lithium-ion", "Sodium-ion", "Lead-acid"],
        "values": [400, 250, 160, 40],
        "unit": "Wh/kg",
        "correct": "Solid-state",
        "semantic_references": {
            "L1_broad": [
                "energy storage", "batteries", "engineering",
                "stockage d'énergie", "batteries", "ingénierie"
            ],
            "L2_specific": [
                "battery technology energy density comparison by chemistry",
                "comparaison de densité énergétique des technologies de batteries",
                "solid-state vs lithium-ion energy storage performance",
                "performances du stockage solide vs lithium-ion"
            ],
            "L3_detailed": [
                "solid-state batteries achieve 400 Wh/kg, 60% more than lithium-ion",
                "les batteries solides atteignent 400 Wh/kg, 60% de plus que le lithium-ion",
                "lead-acid at 40 Wh/kg highlights the 10x improvement in modern battery tech"
            ]
        }
    },
    {
        "slug": "renewable_lcoe_lazard_2023",
        "domain": "energy",
        "version": "Lazard2023",
        "title": "Renewable Energy LCOE Comparison (Lazard, 2023)",
        "description": "Levelized cost of energy ($/MWh) by source. Utility-scale solar is now the cheapest at $24/MWh, significantly undercutting nuclear ($141/MWh).",
        "source": "Lazard's Levelized Cost of Energy Analysis, v16.0 (2023).",
        "labels": ["Solar utility", "Wind onshore", "Gas combined", "Nuclear"],
        "values": [24, 29, 45, 141],
        "unit": "$/MWh",
        "correct": "Solar utility",
        "semantic_references": {
            "L1_broad": [
                "renewable energy", "energy economics", "electricity",
                "énergie renouvelable", "économie de l'énergie", "électricité"
            ],
            "L2_specific": [
                "levelized cost of energy comparison by source Lazard",
                "coût actualisé de l'énergie par source Lazard",
                "solar and wind cost advantage over nuclear and gas",
                "avantage coût du solaire et éolien sur nucléaire et gaz"
            ],
            "L3_detailed": [
                "utility-scale solar achieves the lowest LCOE at $24/MWh",
                "le solaire utilitaire atteint le LCOE le plus bas à 24$/MWh",
                "nuclear LCOE at $141/MWh is nearly 6x more expensive than solar"
            ]
        }
    },
    # --- Epidemiology (2) ---
    {
        "slug": "covid_vaccine_polack_2020",
        "domain": "epidemiology",
        "version": "Polack2020",
        "title": "COVID-19 Vaccine Efficacy by Subgroup (Polack et al., 2020)",
        "description": "BNT162b2 vaccine efficacy (%) by age group and endpoint. The 16-55 age group shows the highest efficacy at 95.6%, with efficacy somewhat lower for asymptomatic infection (75%).",
        "source": "Polack, F. P. et al. (2020). Safety and Efficacy of BNT162b2. NEJM.",
        "labels": ["16-55 years", ">55 years", "Severe disease", "Asymptomatic"],
        "values": [95.6, 93.7, 88.9, 75],
        "unit": "% efficacy",
        "correct": "16-55 years",
        "semantic_references": {
            "L1_broad": [
                "epidemiology", "vaccination", "COVID-19",
                "épidémiologie", "vaccination", "COVID-19"
            ],
            "L2_specific": [
                "BNT162b2 COVID vaccine efficacy by age group and endpoint",
                "efficacité du vaccin COVID BNT162b2 par groupe d'âge",
                "mRNA vaccine clinical trial results phase 3",
                "résultats essai clinique phase 3 vaccin ARNm"
            ],
            "L3_detailed": [
                "BNT162b2 achieves 95.6% efficacy in the 16-55 age group",
                "le BNT162b2 atteint 95.6% d'efficacité chez les 16-55 ans",
                "asymptomatic infection efficacy drops to 75% suggesting transmission still possible"
            ]
        }
    },
    {
        "slug": "handwashing_aiello_2008",
        "domain": "epidemiology",
        "version": "Aiello2008",
        "title": "Handwashing and Respiratory Infections — Meta-analysis (Aiello et al., 2008)",
        "description": "Risk reduction (%) for respiratory infections by hand hygiene intervention. Soap and water achieves the largest reduction (-24%), slightly outperforming hand sanitizer (-21%).",
        "source": "Aiello, A. E. et al. (2008). Effect of hand hygiene on infectious disease. AJPH.",
        "labels": ["Soap and water", "Hand sanitizer", "Education only", "Control"],
        "values": [24, 21, 10, 0],
        "unit": "% risk reduction",
        "correct": "Soap and water",
        "semantic_references": {
            "L1_broad": [
                "epidemiology", "hygiene", "infection prevention",
                "épidémiologie", "hygiène", "prévention des infections"
            ],
            "L2_specific": [
                "hand hygiene interventions respiratory infection risk reduction",
                "réduction du risque d'infection respiratoire par hygiène des mains",
                "soap versus sanitizer effectiveness for disease prevention",
                "efficacité savon vs gel hydroalcoolique en prévention"
            ],
            "L3_detailed": [
                "soap and water reduces respiratory infection risk by 24%",
                "le lavage au savon réduit le risque d'infection respiratoire de 24%",
                "education alone achieves only 10% reduction highlighting need for behavioral intervention"
            ]
        }
    },
    # --- Ecology / Biology (2) ---
    {
        "slug": "pollinator_decline_potts_2010",
        "domain": "ecology",
        "version": "Potts2010",
        "title": "Pollinator Decline Drivers — Relative Impact (Potts et al., 2010)",
        "description": "Relative contribution (%) of each driver to global pollinator decline. Habitat loss is the dominant driver at 45%, nearly double the impact of pesticides (25%).",
        "source": "Potts, S. G. et al. (2010). Global pollinator declines. Trends in Ecology & Evolution.",
        "labels": ["Habitat loss", "Pesticides", "Climate change", "Invasive species"],
        "values": [45, 25, 15, 10],
        "unit": "% relative impact",
        "correct": "Habitat loss",
        "semantic_references": {
            "L1_broad": [
                "ecology", "biodiversity", "pollinators",
                "écologie", "biodiversité", "pollinisateurs"
            ],
            "L2_specific": [
                "pollinator decline drivers relative contribution analysis",
                "facteurs du déclin des pollinisateurs analyse comparative",
                "habitat loss versus pesticides as pollinator threat",
                "perte d'habitat vs pesticides comme menace pour les pollinisateurs"
            ],
            "L3_detailed": [
                "habitat loss contributes 45% of global pollinator decline",
                "la perte d'habitat contribue à 45% du déclin mondial des pollinisateurs",
                "pesticides account for 25% of decline while climate change contributes 15%"
            ]
        }
    },
    {
        "slug": "coral_recovery_interventions_2020",
        "domain": "ecology",
        "version": "CoralRecovery2020",
        "title": "Coral Reef Recovery Interventions — Cover Increase (%)",
        "description": "Coral cover change (%) by intervention type. Active coral gardening achieves the highest recovery (+25%), while no intervention leads to continued decline (-5%).",
        "source": "Compiled from Boström-Einarsson et al. (2020) & UNEP Coral Reef Reports.",
        "labels": ["Coral gardening", "Marine protected areas", "Pollution control", "No intervention"],
        "values": [25, 15, 8, -5],
        "unit": "% cover change",
        "correct": "Coral gardening",
        "semantic_references": {
            "L1_broad": [
                "marine ecology", "coral reefs", "conservation",
                "écologie marine", "récifs coralliens", "conservation"
            ],
            "L2_specific": [
                "coral reef recovery intervention effectiveness comparison",
                "comparaison d'efficacité des interventions de restauration corallienne",
                "active restoration versus marine protected areas for coral",
                "restauration active vs aires marines protégées pour les coraux"
            ],
            "L3_detailed": [
                "coral gardening achieves 25% coral cover increase vs -5% without intervention",
                "le jardinage corallien augmente la couverture de 25% vs -5% sans intervention",
                "marine protected areas alone achieve 15% recovery highlighting need for active restoration"
            ]
        }
    },
    # --- Transport (1) ---
    {
        "slug": "modal_emissions_itf_2021",
        "domain": "transport",
        "version": "ITF2021",
        "title": "CO₂ Emissions per Passenger-km by Transport Mode (ITF, 2021)",
        "description": "CO₂ emissions (g/passenger-km) by transport mode. Bicycle produces zero direct emissions, while cars emit 170g/pkm — 12x more than trains (14g).",
        "source": "International Transport Forum (2021). Transport CO₂ and the Paris Agreement.",
        "labels": ["Car", "Bus", "Train", "Bicycle"],
        "values": [170, 65, 14, 0],
        "unit": "g CO₂/pkm",
        "correct": "Bicycle",
        "semantic_references": {
            "L1_broad": [
                "transport", "climate", "emissions",
                "transport", "climat", "émissions"
            ],
            "L2_specific": [
                "CO2 emissions per passenger kilometer by transport mode",
                "émissions de CO2 par passager-km selon le mode de transport",
                "modal shift carbon footprint comparison car bus train bicycle",
                "comparaison empreinte carbone voiture bus train vélo"
            ],
            "L3_detailed": [
                "bicycle produces zero direct CO2 emissions per passenger-km",
                "le vélo ne produit aucune émission directe de CO2 par passager-km",
                "cars emit 170g CO2/pkm, 12x more than trains at 14g"
            ]
        }
    },
    # --- Agriculture (1) ---
    {
        "slug": "crop_yield_ponisio_2015",
        "domain": "agriculture",
        "version": "Ponisio2015",
        "title": "Crop Yield by Farming Method — Meta-analysis (Ponisio et al., 2015)",
        "description": "Yield gap (%) relative to conventional farming. Precision farming is the only method exceeding conventional yields (+3%), while organic farming shows a -19% yield gap.",
        "source": "Ponisio, L. C. et al. (2015). Diversification practices reduce the yield gap. Proc. R. Soc. B.",
        "labels": ["Precision farming", "Conservation", "Integrated", "Organic"],
        "values": [3, -5, -8, -19],
        "unit": "% yield gap vs conventional",
        "correct": "Precision farming",
        "semantic_references": {
            "L1_broad": [
                "agriculture", "food production", "farming",
                "agriculture", "production alimentaire", "culture"
            ],
            "L2_specific": [
                "farming method yield comparison organic conventional precision",
                "comparaison de rendement bio conventionnel agriculture de précision",
                "yield gap meta-analysis sustainable farming methods",
                "méta-analyse du déficit de rendement méthodes durables"
            ],
            "L3_detailed": [
                "precision farming is the only method exceeding conventional yields at +3%",
                "l'agriculture de précision est la seule méthode dépassant le conventionnel à +3%",
                "organic farming shows a 19% yield gap but with potential biodiversity benefits"
            ]
        }
    },
    # --- Materials Science (1) ---
    {
        "slug": "concrete_co2_alternatives_2023",
        "domain": "materials",
        "version": "ConcreteCO2_2023",
        "title": "Concrete Alternatives — CO₂ Reduction vs Portland Cement (2023)",
        "description": "CO₂ emissions reduction (%) compared to Portland cement. Geopolymer concrete achieves the largest reduction (-80%), making it the most promising low-carbon alternative.",
        "source": "Compiled from IEA Cement Technology Roadmap & materials science literature.",
        "labels": ["Geopolymer", "LC3", "Fly ash blend", "Standard Portland"],
        "values": [80, 40, 25, 0],
        "unit": "% CO₂ reduction",
        "correct": "Geopolymer",
        "semantic_references": {
            "L1_broad": [
                "materials science", "concrete", "decarbonization",
                "science des matériaux", "béton", "décarbonation"
            ],
            "L2_specific": [
                "low-carbon concrete alternatives CO2 reduction comparison",
                "alternatives au béton portland réduction de CO2",
                "geopolymer cement environmental impact assessment",
                "évaluation de l'impact environnemental du ciment géopolymère"
            ],
            "L3_detailed": [
                "geopolymer concrete reduces CO2 emissions by 80% compared to Portland cement",
                "le béton géopolymère réduit les émissions de CO2 de 80% vs le ciment Portland",
                "LC3 achieves 40% reduction offering a practical near-term alternative"
            ]
        }
    },
]


def generate_bar_chart(paper: dict, out_path: str):
    """Generate horizontal bar chart (VEC style, β≈1.0)."""
    fig, ax = plt.subplots(figsize=(11, 5.6), dpi=150)
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    labels = paper["labels"]
    values = paper["values"]

    # Sort by value descending (highest on top for horizontal bar)
    sorted_pairs = sorted(zip(values, labels), key=lambda x: x[0])
    sorted_values = [p[0] for p in sorted_pairs]
    sorted_labels = [p[1] for p in sorted_pairs]
    n = len(sorted_values)
    colors = [COLORS[i % len(COLORS)] for i in range(n)]

    y_pos = np.arange(n)
    bars = ax.barh(y_pos, sorted_values, color=colors, height=0.6, edgecolor="none")

    # Value labels on bars
    for bar, val in zip(bars, sorted_values):
        x_offset = max(abs(v) for v in values) * 0.02
        if val >= 0:
            ax.text(
                bar.get_width() + x_offset, bar.get_y() + bar.get_height() / 2,
                f"{val}", va="center", ha="left",
                color=TEXT_COLOR, fontsize=11, fontweight="bold"
            )
        else:
            ax.text(
                bar.get_width() - x_offset, bar.get_y() + bar.get_height() / 2,
                f"{val}", va="center", ha="right",
                color=TEXT_COLOR, fontsize=11, fontweight="bold"
            )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(sorted_labels, color=TEXT_COLOR, fontsize=11)
    ax.set_xlabel(paper["unit"], color=TEXT_COLOR, fontsize=10)
    ax.tick_params(axis="x", colors=TEXT_COLOR, labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color(GRID_COLOR)
    ax.spines["left"].set_color(GRID_COLOR)
    ax.xaxis.grid(True, color=GRID_COLOR, linewidth=0.5, alpha=0.5)

    # Title
    ax.set_title(paper["title"], color=TEXT_COLOR, fontsize=13, fontweight="bold", pad=12)

    # Source citation
    fig.text(
        0.5, 0.02, paper["source"], ha="center",
        fontsize=7, color="#64748b", style="italic"
    )

    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    fig.savefig(out_path, dpi=150, facecolor=BG_COLOR, bbox_inches="tight")
    plt.close(fig)


def generate_pie_chart(paper: dict, out_path: str):
    """Generate pie chart (control, β≈0.7 area encoding)."""
    fig, ax = plt.subplots(figsize=(11, 5.6), dpi=150)
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    labels = paper["labels"]
    values = paper["values"]

    # For pie charts, we need positive values. Handle negatives by offsetting.
    has_negative = any(v < 0 for v in values)
    if has_negative:
        # Use absolute values for pie sizing, mark negatives in labels
        pie_values = [abs(v) for v in values]
        pie_labels = [
            f"{l} ({v:+g})" if v != 0 else f"{l} (0)"
            for l, v in zip(labels, values)
        ]
        # Handle zero values — replace with tiny fraction so pie renders
        pie_values = [max(v, 0.01) for v in pie_values]
    else:
        pie_values = values
        pie_labels = [f"{l} ({v})" for l, v in zip(labels, values)]
        # Handle zero values
        pie_values = [max(v, 0.01) for v in pie_values]

    n = len(pie_values)
    colors = [COLORS[i % len(COLORS)] for i in range(n)]

    wedges, texts = ax.pie(
        pie_values,
        colors=colors,
        startangle=90,
        wedgeprops={"edgecolor": BG_COLOR, "linewidth": 2},
    )

    # Legend on the right
    legend_patches = [
        mpatches.Patch(color=colors[i], label=pie_labels[i])
        for i in range(n)
    ]
    ax.legend(
        handles=legend_patches,
        loc="center left",
        bbox_to_anchor=(1.05, 0.5),
        fontsize=10,
        frameon=False,
        labelcolor=TEXT_COLOR,
    )

    # Title
    control_title = paper["title"].split("—")[0].strip() if "—" in paper["title"] else paper["title"].split("(")[0].strip()
    ax.set_title(
        f"{control_title} — Pie chart (control)",
        color=TEXT_COLOR, fontsize=13, fontweight="bold", pad=12
    )

    # Source
    fig.text(
        0.5, 0.02, paper["source"], ha="center",
        fontsize=7, color="#64748b", style="italic"
    )

    plt.tight_layout(rect=[0, 0.05, 0.85, 0.95])
    fig.savefig(out_path, dpi=150, facecolor=BG_COLOR, bbox_inches="tight")
    plt.close(fig)


def generate_json(paper: dict, is_control: bool, out_path: str):
    """Generate sidecar JSON metadata."""
    data = {
        "domain": paper["domain"],
        "version": paper["version"] + ("-pie-control" if is_control else ""),
        "correct_product": paper["correct"],
        "products": paper["labels"],
        "title": paper["title"] if not is_control else paper["title"].split("—")[0].strip() + " — Pie chart (contrôle)" if "—" in paper["title"] else paper["title"] + " — Pie chart (contrôle)",
        "semantic_references": paper["semantic_references"],
    }
    if is_control:
        data["is_control"] = True
    else:
        data["description"] = paper["description"]

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def main():
    generated = []
    for paper in PAPERS:
        slug = paper["slug"]
        print(f"  Generating {slug}...")

        # Bar chart
        bar_path = os.path.join(OUT_DIR, f"{slug}.png")
        generate_bar_chart(paper, bar_path)

        # Bar JSON
        bar_json = os.path.join(OUT_DIR, f"{slug}.json")
        generate_json(paper, is_control=False, out_path=bar_json)

        # Pie chart (control)
        pie_path = os.path.join(OUT_DIR, f"{slug}_control.png")
        generate_pie_chart(paper, pie_path)

        # Pie JSON (control)
        pie_json = os.path.join(OUT_DIR, f"{slug}_control.json")
        generate_json(paper, is_control=True, out_path=pie_json)

        generated.append(slug)

    print(f"\nGenerated {len(generated)} papers × 2 = {len(generated)*2} images + {len(generated)*2} JSONs")
    return generated


if __name__ == "__main__":
    main()
