# GLANCE Meta-Analysis — 47 GAs across 15 Domains

*Generated: 2026-03-25 06:07*

*Pipeline: batch_analysis.py -> recommender.py (extended)*


## Overall Distribution

- **N:** 47
- **Mean score:** 0.6052 (sigma = 0.0914)
- **Median:** 0.6172
- **Range:** [0.5046, 0.7441]

## By Domain

| Domain | N GAs | Mean Score | sigma | Best GA | Worst GA |
|--------|-------|-----------|-------|---------|----------|
| tech | 2 | 0.6519 | 0.1304 | attention_transformer_2017 | attention_transformer_2017_pie_control |
| policy | 2 | 0.6246 | 0.1510 | oregon_health_experiment_2012 | oregon_health_experiment_2012_pie_contro |
| epidemiology | 4 | 0.6115 | 0.1056 | handwashing_aiello_2008 | covid_vaccine_polack_2020_control |
| materials | 2 | 0.6104 | 0.1296 | concrete_co2_alternatives_2023 | concrete_co2_alternatives_2023_control |
| neuroscience | 4 | 0.6104 | 0.1059 | sleep_memory_walker_2009 | exercise_neuroplasticity_erickson_2011_c |
| climate | 2 | 0.6096 | 0.1281 | drawdown_climate_2017 | drawdown_climate_2017_pie_control |
| education | 2 | 0.6056 | 0.1295 | hattie_visible_learning_2009 | hattie_visible_learning_2009_bubble_cont |
| nutrition | 4 | 0.6020 | 0.1050 | sugar_tax_teng_2019 | predimed_estruch_2018_control |
| psychology | 6 | 0.6003 | 0.1007 | marshmallow_watts_2018 | cbt_depression_cuijpers_2020_control |
| transport | 2 | 0.6002 | 0.1280 | modal_emissions_itf_2021 | modal_emissions_itf_2021_control |
| economics | 4 | 0.5996 | 0.1045 | minimum_wage_card_krueger_1994 | microfinance_banerjee_2015_control |
| agriculture | 2 | 0.5991 | 0.1288 | crop_yield_ponisio_2015 | crop_yield_ponisio_2015_control |
| energy | 4 | 0.5986 | 0.1045 | battery_energy_density_2023 | renewable_lcoe_lazard_2023_control |
| ecology | 4 | 0.5970 | 0.1043 | coral_recovery_interventions_2020 | pollinator_decline_potts_2010_control |
| med | 3 | 0.5874 | 0.0517 | immunomod_v10_wireframe | immunomod_v10_area_control |

## Control vs VEC

| Type | N | Mean Score | sigma | Delta |
|------|---|-----------|-------|-------|
| VEC (length) | 23 | 0.6947 | 0.0218 | -- |
| Control (area) | 23 | 0.5151 | 0.0114 | +0.1796 |
| Mixed/calibration | 1 | 0.6172 | -- | -- |

**Welch's t-test:** t(33) = 35.015, p = 0.0000
**Significance:** p < 0.001 (highly significant)

VEC outperforms controls by +0.1796 points (+34.9%).
This confirms Stevens power law: beta=1.0 (length) produces higher graph scores than beta=0.7 (area).

## By Encoding Channel

| Primary Channel | N | Mean Score | Stevens beta |
|----------------|---|-----------|-------------|
| length | 23 | 0.6947 | 1.0 |
| area | 23 | 0.5151 | 0.7 |
| mixed | 1 | 0.6172 | varies |

## Top 5 Most Common Recommendations

| Recommendation | Frequency | Avg Expected delta S9b |
|---------------|-----------|----------------------|
| Replace area encoding with length (bar chart) | 23 | +25% |
| Improve hierarchy clarity (correct answer positioning) | 2 | +12% |

## Top 5 Highest Scoring GAs

| Rank | GA | Domain | Type | Score |
|------|-----|--------|------|-------|
| 1 | attention_transformer_2017 | tech | VEC | 0.7441 |
| 2 | oregon_health_experiment_2012 | policy | VEC | 0.7314 |
| 3 | handwashing_aiello_2008 | epidemiology | VEC | 0.7047 |
| 4 | sleep_memory_walker_2009 | neuroscience | VEC | 0.7036 |
| 5 | concrete_co2_alternatives_2023 | materials | VEC | 0.7020 |

## Top 5 Lowest Scoring GAs

| Rank | GA | Domain | Type | Score | Weakest Node |
|------|-----|--------|------|-------|-------------|
| 43 | crop_yield_ponisio_2015_control | agriculture | CTRL | 0.5081 | Organic |
| 44 | renewable_lcoe_lazard_2023_control | energy | CTRL | 0.5079 | Nuclear |
| 45 | obedience_milgram_1963_control | psychology | CTRL | 0.5077 | Experimenter absent |
| 46 | cbt_depression_cuijpers_2020_control | psychology | CTRL | 0.5063 | Placebo |
| 47 | pollinator_decline_potts_2010_control | ecology | CTRL | 0.5046 | Invasive species |

## Key Findings

1. **Control GAs (area encoding) score 34.9% lower than VEC GAs (length encoding).** Delta = 0.1796 points. This is consistent with Stevens power law (beta=0.7 vs 1.0).
2. **Tech has the highest average score** (0.6519), driven by hand-crafted graphs.
3. **The most common weakness across all GAs is:** Replace area encoding with length (bar chart) (found in 23/47 GAs, 49%).
4. **GAs with high semantic richness (>0.6) score 0.6166 vs 0.5094 for low richness** — semantic depth correlates with graph quality.
5. **Stevens power law confirmed across ALL 15 testable domains** — VEC (length) outperforms controls (area) in every domain without exception.

## Per-Domain VEC vs Control Consistency

| Domain | VEC Mean | Control Mean | Delta | Consistent? |
|--------|----------|-------------|-------|-------------|
| agriculture | 0.6902 | 0.5081 | +0.1821 | YES |
| climate | 0.7001 | 0.5190 | +0.1811 | YES |
| ecology | 0.6873 | 0.5067 | +0.1805 | YES |
| economics | 0.6901 | 0.5091 | +0.1810 | YES |
| education | 0.6972 | 0.5140 | +0.1831 | YES |
| energy | 0.6891 | 0.5082 | +0.1809 | YES |
| epidemiology | 0.7030 | 0.5201 | +0.1829 | YES |
| materials | 0.7020 | 0.5188 | +0.1833 | YES |
| med | 0.6172 | 0.5277 | +0.0895 | YES |
| neuroscience | 0.7021 | 0.5187 | +0.1835 | YES |
| nutrition | 0.6929 | 0.5110 | +0.1819 | YES |
| policy | 0.7314 | 0.5179 | +0.2136 | YES |
| psychology | 0.6922 | 0.5084 | +0.1838 | YES |
| tech | 0.7441 | 0.5597 | +0.1844 | YES |
| transport | 0.6907 | 0.5097 | +0.1810 | YES |

---
*Generated by batch_analysis.py — 2026-03-25 06:07*