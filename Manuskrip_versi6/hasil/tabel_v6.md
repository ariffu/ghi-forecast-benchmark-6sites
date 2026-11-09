### TABEL1

| Station | WMO ID | Latitude | Longitude | Elevation (m a.s.l.) | Logger GHI in 2025 (%) | Measured GHI in 2025 (%) |
|----------------|--------|----------:|-----------:|---------:|----------:|----------:|
| Banten | 96733 | 6.261°S | 106.751°E | 27 | 77.6 | 97.4 |
| Bengkulu | 96255 | 3.865°S | 102.312°E | 9 | 99.8 | 99.9 |
| Jambi | 96191 | 1.601°S | 103.494°E | 24 | 88.9 | 93.7 |
| Yogyakarta | 96851 | 7.731°S | 110.354°E | 182 | 98.5 | 100.0 |
| West Kalimantan | 96583 | 0.075°N | 109.191°E | 2 | 92.4 | 94.3 |
| Central Java | 96835 | 6.985°S | 110.381°E | 6 | 98.0 | 98.6 |

### TABEL3

| Station | Smart persistence R² | Ridge R² | CatBoost R² | CatBoost RMSE (W m⁻²) | Skill score vs smart persistence | Skill score vs CP reference | Spread of eight architectures | Most accurate architecture |
|---------------|---------:|-------:|--------:|---------:|---------:|---------:|---------:|-----------|
| Banten | 0.727 | 0.816 | 0.846 | 98.2 | 0.249 | 0.133 | 0.007 | CatBoost |
| Bengkulu | 0.838 | 0.887 | 0.909 | 89.5 | 0.251 | 0.155 | 0.005 | CatBoost |
| Jambi | 0.739 | 0.835 | 0.878 | 89.7 | 0.317 | 0.214 | 0.006 | CatBoost |
| Yogyakarta | 0.735 | 0.836 | 0.869 | 102.9 | 0.298 | 0.177 | 0.008 | CatBoost |
| West Kalimantan | 0.805 | 0.863 | 0.898 | 98.1 | 0.277 | 0.185 | 0.003 | Transformer-hybrid |
| Central Java | 0.843 | 0.883 | 0.903 | 89.4 | 0.215 | 0.140 | 0.006 | CatBoost |

### TABEL4

| Station | CLP | 95% CI | AWS | SYNOP cloud | AWS on top of CLP | SYNOP cloud on top of CLP | CLP, CatBoost |
|---------------|--------:|--------------|--------:|--------:|---------:|---------:|---------:|
| Banten | +0.017* | [0.013, 0.021] | +0.003* | +0.001 | +0.005* | +0.000 | +0.017* |
| Bengkulu | +0.015* | [0.012, 0.018] | −0.002* | −0.002* | +0.000 | +0.000 | +0.016* |
| Jambi | +0.029* | [0.024, 0.033] | +0.001 | +0.003* | +0.000 | +0.000 | +0.028* |
| Yogyakarta | +0.024* | [0.019, 0.028] | +0.003* | +0.003* | +0.001* | +0.000 | +0.024* |
| West Kalimantan | +0.019* | [0.016, 0.023] | +0.004* | +0.002* | +0.002* | +0.000 | +0.019* |
| Central Java | +0.012* | [0.009, 0.016] | +0.002* | +0.000 | +0.000 | +0.000 | +0.013* |

### ESM_R2

| Station | Smart persistence | Ridge | LightGBM | CatBoost | XGBoost | MLP | LSTM | Transformer | LSTM-hybrid | Transformer-hybrid | Spread |
|------------------|---------:|------:|--------:|--------:|--------:|------:|------:|---------:|--------:|---------:|------:|
| *R²* | | | | | | | | | | | |
| Banten | 0.727 | 0.816 | 0.845 | **0.846** | 0.846 | 0.845 | 0.839 | 0.842 | 0.841 | 0.845 | 0.007 |
| Bengkulu | 0.838 | 0.887 | 0.908 | **0.909** | 0.906 | 0.906 | 0.904 | 0.905 | 0.907 | 0.906 | 0.005 |
| Jambi | 0.739 | 0.835 | 0.877 | **0.878** | 0.876 | 0.872 | 0.872 | 0.872 | 0.873 | 0.873 | 0.006 |
| Yogyakarta | 0.735 | 0.836 | 0.869 | **0.869** | 0.869 | 0.868 | 0.861 | 0.863 | 0.867 | 0.868 | 0.008 |
| West Kalimantan | 0.805 | 0.863 | 0.897 | 0.898 | 0.898 | 0.895 | 0.895 | 0.896 | 0.896 | **0.898** | 0.003 |
| Central Java | 0.843 | 0.883 | 0.901 | **0.903** | 0.902 | 0.901 | 0.898 | 0.899 | 0.900 | 0.900 | 0.006 |
| *Skill score* | | | | | | | | | | | |
| Banten | — | 0.179 | 0.245 | **0.249** | 0.248 | 0.245 | 0.232 | 0.238 | 0.236 | 0.247 | 0.016 |
| Bengkulu | — | 0.164 | 0.245 | **0.251** | 0.238 | 0.240 | 0.232 | 0.237 | 0.242 | 0.239 | 0.020 |
| Jambi | — | 0.206 | 0.314 | **0.317** | 0.312 | 0.300 | 0.301 | 0.300 | 0.302 | 0.304 | 0.017 |
| Yogyakarta | — | 0.213 | 0.297 | **0.298** | 0.298 | 0.294 | 0.277 | 0.281 | 0.292 | 0.296 | 0.021 |
| West Kalimantan | — | 0.163 | 0.273 | 0.277 | 0.275 | 0.267 | 0.267 | 0.271 | 0.271 | **0.279** | 0.012 |
| Central Java | — | 0.137 | 0.208 | **0.215** | 0.209 | 0.207 | 0.193 | 0.197 | 0.204 | 0.203 | 0.023 |

### ESM_GALAT

| Station | Smart persistence | Ridge | LightGBM | CatBoost | XGBoost | MLP | LSTM | Transformer | LSTM-hybrid | Transformer-hybrid |
|------------------|---------:|------:|--------:|--------:|--------:|------:|------:|---------:|--------:|---------:|
| *RMSE (W m⁻²)* | | | | | | | | | | |
| Banten | 130.8 | 107.3 | 98.7 | **98.2** | 98.4 | 98.7 | 100.4 | 99.6 | 99.9 | 98.5 |
| Bengkulu | 119.6 | 100.0 | 90.3 | **89.5** | 91.1 | 90.9 | 91.9 | 91.3 | 90.7 | 91.0 |
| Jambi | 131.2 | 104.2 | 90.0 | **89.7** | 90.3 | 91.9 | 91.7 | 91.8 | 91.6 | 91.3 |
| Yogyakarta | 146.7 | 115.5 | 103.2 | **102.9** | 103.0 | 103.6 | 106.0 | 105.4 | 103.9 | 103.3 |
| West Kalimantan | 135.6 | 113.5 | 98.6 | 98.1 | 98.2 | 99.4 | 99.3 | 98.8 | 98.8 | **97.8** |
| Central Java | 113.9 | 98.3 | 90.2 | **89.4** | 90.1 | 90.4 | 92.0 | 91.5 | 90.7 | 90.7 |
| *MAE (W m⁻²)* | | | | | | | | | | |
| Banten | 84.7 | 77.5 | 66.7 | 66.8 | 66.7 | **66.4** | 68.1 | 67.9 | 67.8 | 67.0 |
| Bengkulu | 75.1 | 70.4 | 59.8 | **59.6** | 60.4 | 60.4 | 61.6 | 60.4 | 60.7 | 59.9 |
| Jambi | 86.1 | 77.3 | **62.3** | 62.5 | 62.7 | 63.8 | 63.1 | 63.4 | 63.6 | 63.4 |
| Yogyakarta | 94.9 | 84.4 | 70.5 | 70.8 | **70.5** | 70.5 | 72.2 | 71.9 | 71.1 | 70.6 |
| West Kalimantan | 83.6 | 82.1 | 67.0 | 66.7 | 66.7 | 67.0 | 67.4 | 67.1 | 67.2 | **66.4** |
| Central Java | 71.0 | 68.6 | 59.3 | **59.1** | 59.4 | 59.4 | 61.1 | 60.4 | 60.0 | 59.7 |
| *Residual R²* | | | | | | | | | | |
| Banten | — | 0.322 | 0.426 | **0.432** | 0.431 | 0.427 | 0.407 | 0.416 | 0.413 | 0.428 |
| Bengkulu | — | 0.301 | 0.430 | **0.439** | 0.420 | 0.422 | 0.410 | 0.417 | 0.425 | 0.421 |
| Jambi | — | 0.369 | 0.530 | **0.533** | 0.526 | 0.510 | 0.512 | 0.510 | 0.512 | 0.515 |
| Yogyakarta | — | 0.376 | 0.502 | **0.504** | 0.504 | 0.498 | 0.475 | 0.480 | 0.495 | 0.501 |
| West Kalimantan | — | 0.299 | 0.471 | 0.476 | 0.475 | 0.462 | 0.463 | 0.469 | 0.469 | **0.480** |
| Central Java | — | 0.253 | 0.371 | **0.382** | 0.372 | 0.369 | 0.346 | 0.353 | 0.364 | 0.363 |

### ESM_SEED

| Station | MLP | LSTM | Transformer | LSTM-hybrid | Transformer-hybrid | Spread, seed 42 | Spread, seed means | Spread, range over seeds |
|---------------|-------------:|-------------:|-------------:|-------------:|-------------:|-------:|-------:|-------------:|
| Banten | 0.8448 ± 0.0015 | 0.8394 ± 0.0008 | 0.8417 ± 0.0009 | 0.8410 ± 0.0020 | 0.8452 ± 0.0016 | 0.0074 | 0.0068 | 0.0066–0.0082 |
| Bengkulu | 0.9062 ± 0.0009 | 0.9042 ± 0.0020 | 0.9054 ± 0.0017 | 0.9067 ± 0.0020 | 0.9060 ± 0.0010 | 0.0051 | 0.0048 | 0.0043–0.0088 |
| Jambi | 0.8719 ± 0.0004 | 0.8724 ± 0.0007 | 0.8721 ± 0.0018 | 0.8726 ± 0.0013 | 0.8734 ± 0.0018 | 0.0057 | 0.0061 | 0.0057–0.0088 |
| Yogyakarta | 0.8677 ± 0.0009 | 0.8615 ± 0.0011 | 0.8630 ± 0.0023 | 0.8669 ± 0.0002 | 0.8684 ± 0.0021 | 0.0073 | 0.0079 | 0.0067–0.0097 |
| West Kalimantan | 0.8951 ± 0.0008 | 0.8952 ± 0.0010 | 0.8964 ± 0.0006 | 0.8964 ± 0.0008 | 0.8985 ± 0.0009 | 0.0030 | 0.0034 | 0.0029–0.0053 |
| Central Java | 0.9011 ± 0.0008 | 0.8976 ± 0.0010 | 0.8986 ± 0.0014 | 0.9003 ± 0.0010 | 0.9003 ± 0.0020 | 0.0047 | 0.0056 | 0.0047–0.0072 |

### ESM_UJI

| Architecture | Runs | Significantly more accurate | Not different | Significantly less accurate | Mean ΔR² |
|----------------|------:|------------:|----------:|------------:|---------:|
| CatBoost | 30 | 17 | 13 | 0 | +0.0012 |
| XGBoost | 30 | 5 | 20 | 5 | +0.0000 |
| MLP | 30 | 0 | 23 | 7 | −0.0016 |
| LSTM | 30 | 0 | 6 | 24 | −0.0043 |
| Transformer | 30 | 0 | 15 | 15 | −0.0032 |
| LSTM-hybrid | 30 | 1 | 21 | 8 | −0.0020 |
| Transformer-hybrid | 30 | 2 | 21 | 7 | −0.0008 |

### ESM_KONV

| Station | Correlation of corrections, median (min) | Correlation of errors, median (min) | RMS difference between forecasts, median (W m⁻²) | Mean of eight, ΔR² [95% CI] | Stacking, ΔR² [95% CI] | Remaining error removed by stacking (%) | Remaining error removed by CLP (%) |
|-------------|----------:|----------:|---------:|------------------|------------------|---------:|---------:|
| Banten | 0.95 (0.93) | 0.96 (0.94) | 29.9 | +0.0026 [+0.0010, +0.0042] | +0.0025 [+0.0007, +0.0041] | 1.6 | 9.7 |
| Bengkulu | 0.93 (0.90) | 0.94 (0.91) | 31.9 | +0.0023 [+0.0013, +0.0033] | +0.0023 [+0.0013, +0.0033] | 2.5 | 13.7 |
| Jambi | 0.96 (0.94) | 0.95 (0.93) | 28.5 | +0.0018 [+0.0003, +0.0032] | +0.0016 [+0.0002, +0.0029] | 1.3 | 19.1 |
| Yogyakarta | 0.96 (0.94) | 0.96 (0.93) | 30.9 | +0.0031 [+0.0016, +0.0046] | +0.0035 [+0.0019, +0.0051] | 2.7 | 15.5 |
| West Kalimantan | 0.94 (0.92) | 0.95 (0.92) | 31.8 | +0.0030 [+0.0013, +0.0047] | +0.0036 [+0.0021, +0.0052] | 3.5 | 15.6 |
| Central Java | 0.94 (0.91) | 0.96 (0.94) | 26.6 | +0.0008 [−0.0003, +0.0021] | +0.0016 [+0.0006, +0.0025] | 1.7 | 11.3 |

### ESM_CB

| Station | CLP | AWS | SYNOP cloud | AWS on top of CLP | SYNOP cloud on top of CLP |
|----------------|------------------|------------------|------------------|------------------|------------------|
| Banten | +0.0167 [+0.0122, +0.0211]* | +0.0034 [+0.0011, +0.0057]* | +0.0012 [−0.0003, +0.0026] | +0.0040 [+0.0011, +0.0067]* | +0.0005 [−0.0004, +0.0015] |
| Bengkulu | +0.0161 [+0.0130, +0.0193]* | −0.0005 [−0.0020, +0.0011] | −0.0007 [−0.0022, +0.0007] | +0.0004 [−0.0007, +0.0015] | −0.0005 [−0.0013, +0.0004] |
| Jambi | +0.0280 [+0.0239, +0.0323]* | −0.0002 [−0.0018, +0.0014] | +0.0015 [+0.0000, +0.0031] | −0.0001 [−0.0014, +0.0012] | −0.0002 [−0.0010, +0.0005] |
| Yogyakarta | +0.0240 [+0.0196, +0.0281]* | +0.0014 [−0.0008, +0.0035] | +0.0026 [+0.0003, +0.0048]* | +0.0011 [−0.0004, +0.0026] | −0.0006 [−0.0017, +0.0005] |
| West Kalimantan | +0.0195 [+0.0159, +0.0233]* | +0.0032 [+0.0011, +0.0050]* | +0.0020 [+0.0010, +0.0029]* | +0.0026 [+0.0008, +0.0042]* | +0.0002 [−0.0004, +0.0008] |
| Central Java | +0.0133 [+0.0103, +0.0167]* | +0.0012 [−0.0001, +0.0025] | +0.0010 [−0.0003, +0.0022] | +0.0007 [−0.0004, +0.0018] | −0.0005 [−0.0011, +0.0002] |

### ESM_KELAS

| Class | Share of forecasts (%) | Share of squared error (%) | Skill score vs smart persistence | RMSE reduction by CLP (%) | Stations with a significant reduction / increase |
|----------------------|---------:|---------:|-----------:|-----------:|-----------:|
| Clear ($k_t$ > 0.65) | 30–48 | 36–55 | 0.25 to 0.37 | 3.5 to 6.2 | 6 / 0 |
| Partly cloudy (0.30 < $k_t$ ≤ 0.65) | 34–44 | 36–48 | 0.13 to 0.26 | 5.7 to 11.6 | 6 / 0 |
| Overcast ($k_t$ ≤ 0.30) | 19–28 | 9–19 | 0.19 to 0.36 | 5.4 to 18.7 | 6 / 0 |
| 06–10 WIB | 30–34 | 19–28 | 0.23 to 0.32 | 4.1 to 8.2 | 6 / 0 |
| 10–14 WIB | 35–36 | 59–71 | 0.22 to 0.34 | 4.9 to 11.2 | 6 / 0 |
| 14–18 WIB | 30–34 | 8–18 | 0.20 to 0.27 | 4.6 to 11.0 | 6 / 0 |
| Stable (lowest third) | 33 | 7–9 | −3.74 to −2.78 | −8.3 to 1.8 | 0 / 2 |
| Moderate | 33 | 18–21 | −0.55 to −0.23 | −6.1 to 4.2 | 1 / 1 |
| Changing (highest third) | 33 | 69–76 | 0.30 to 0.40 | 7.1 to 12.3 | 6 / 0 |

### ESM_CLPKELAS

| Station | Clear | Partly cloudy | Overcast | Stable | Moderate | Changing | All |
|--------------|------------|------------|------------|------------|------------|------------|------------|
| Banten | 3.7 [2.0, 5.4] | 5.7 [4.1, 7.3] | 5.4 [2.5, 8.0] | −4.4 [−7.7, −0.8] | −1.2 [−3.6, 1.2] | 7.1 [5.9, 8.3] | 4.9 [3.7, 6.2] |
| Bengkulu | 4.4 [2.5, 6.3] | 8.5 [6.5, 10.6] | 15.2 [11.7, 18.7] | −2.6 [−5.9, 0.6] | −1.4 [−4.6, 1.6] | 9.7 [8.3, 11.1] | 7.1 [5.7, 8.6] |
| Jambi | 6.2 [4.7, 7.6] | 10.7 [9.1, 12.4] | 18.7 [15.2, 22.1] | 1.8 [−1.4, 4.8] | 4.2 [1.8, 6.4] | 12.3 [11.0, 13.6] | 10.0 [8.7, 11.3] |
| Yogyakarta | 5.5 [3.5, 7.3] | 9.8 [8.1, 11.5] | 11.2 [7.8, 14.5] | −1.5 [−4.6, 1.5] | 2.3 [−0.3, 4.9] | 10.6 [9.0, 11.9] | 8.1 [6.5, 9.4] |
| West Kalimantan | 4.0 [2.2, 5.8] | 11.6 [9.8, 13.5] | 16.5 [12.8, 20.2] | −8.3 [−12.1, −4.9] | −6.1 [−8.5, −3.6] | 12.0 [10.6, 13.5] | 8.1 [6.7, 9.6] |
| Central Java | 3.5 [2.4, 4.7] | 7.9 [5.9, 10.0] | 7.8 [1.8, 13.3] | 0.3 [−3.3, 3.8] | −2.6 [−5.9, 0.6] | 7.8 [6.4, 9.3] | 5.8 [4.3, 7.4] |

### ESM_ROBUST

| Station | ΔR²(CLP): missing retrievals masked → stored values | Box statistics added to core + CLP | Box statistics added to all 44 predictors | ΔR²(CLP): adopted timing → 10 min later (loss) |
|------------|----------------|------------------|------------------|-----------------|
| Banten | +0.0169 → +0.0166 | +0.0002 [−0.0008, +0.0013] | +0.0002 [−0.0013, +0.0016] | +0.0169 → +0.0140 (17%) |
| Bengkulu | +0.0148 → +0.0150 | +0.0015 [+0.0004, +0.0025] | +0.0023 [+0.0012, +0.0034] | +0.0148 → +0.0127 (14%) |
| Jambi | +0.0287 → +0.0286 | +0.0006 [−0.0004, +0.0016] | +0.0005 [−0.0005, +0.0015] | +0.0287 → +0.0233 (19%) |
| Yogyakarta | +0.0240 → +0.0241 | +0.0000 [−0.0011, +0.0010] | −0.0001 [−0.0010, +0.0008] | +0.0240 → +0.0213 (11%) |
| West Kalimantan | +0.0193 → +0.0184 | +0.0002 [−0.0005, +0.0008] | +0.0001 [−0.0006, +0.0008] | +0.0193 → +0.0163 (16%) |
| Central Java | +0.0124 → +0.0120 | −0.0005 [−0.0013, +0.0003] | +0.0001 [−0.0008, +0.0009] | +0.0124 → +0.0102 (18%) |

### ESM_PRED

| Group | Predictor | Description | Origin | Availability (%) |
|--------------|------------------------|----------------------------------|---------|--------:|
| Core | `ghi_wm2` | GHI (pyranometer) | measured | 100 |
| Core | `dhi_wm2` | diffuse horizontal irradiance | measured or modelled | 100 |
| Core | `dni_wm2` | direct normal irradiance | measured or modelled | 100 |
| Core | `reflected_wm2` | reflected irradiance | measured | 100 |
| Core | `decl_noaa_deg` | solar declination | model | 100 |
| Core | `eot_min` | equation of time | model | 100 |
| Core | `clear_sky_ghi` | clear-sky GHI at t (slot mean) | model | 100 |
| Core | `kt` | clear-sky index $k_c$ = GHI / clear-sky GHI | derived | 100 |
| Core | `clear_sky_ghi_h1` | clear-sky GHI at t + 1 h (slot mean) | model | 100 |
| Core | `kt_delta_10m` | change in $k_c$ over 10 min | derived | 100 |
| Core | `kt_delta_20m` | change in $k_c$ over 20 min | derived | 99 |
| Core | `kt_delta_30m` | change in $k_c$ over 30 min | derived | 97–98 |
| Core | `kt_delta_60m` | change in $k_c$ over 60 min | derived | 93 |
| Core | `kt_roll_30m_mean` | 30-min mean of $k_c$ | derived | 100 |
| Core | `kt_roll_30m_std` | 30-min standard deviation of $k_c$ | derived | 100 |
| Core | `kt_roll_60m_mean` | 60-min mean of $k_c$ | derived | 100 |
| Core | `kt_roll_60m_std` | 60-min standard deviation of $k_c$ | derived | 100 |
| Core | `kt_std_3h` | 3-h standard deviation of $k_c$ | derived | 100 |
| Satellite cloud (CLP) | `clp_cot` | cloud optical thickness (COT) | measured | 90–92 |
| Satellite cloud (CLP) | `clp_cth_km` | cloud-top height (CTH) | measured | 90–92 |
| Satellite cloud (CLP) | `clp_cer_um` | cloud effective radius | measured | 81–86 |
| Satellite cloud (CLP) | `clp_cloud_present_int` | cloud flag (mean COT ≥ 1) | derived | 90–92 |
| Satellite cloud (CLP) | `clp_cot_delta_60m` | change in COT over 60 min | derived | 79–82 |
| Satellite cloud (CLP) | `clp_cot_roll_180m_mean` | 3-h mean of COT | derived | 95–96 |
| Satellite cloud (CLP) | `clp_cth_lag_60m` | CTH 60 min earlier | derived | 84–85 |
| Satellite cloud (CLP) | `clp_cth_roll_180m_mean` | 3-h mean of CTH | derived | 95–96 |
| Satellite cloud (CLP) | `clp_cloud_frac` | cloud fraction (share of box pixels with a COT retrieval) | measured | 91–92 |
| SYNOP | `synop_visibility_km` | visibility | measured | 91–100 |
| SYNOP | `synop_cloud_cover_oktas` | total cloud cover N (okta) | measured | 91–100 |
| SYNOP | `synop_cl` | low-cloud type (CL) | measured | 91–100 |
| SYNOP | `synop_cm` | middle-cloud type (CM) | measured | 91–100 |
| SYNOP | `synop_ch` | high-cloud type (CH) | measured | 81–94 |
| SYNOP | `synop_present_weather_ww` | present weather (ww) | measured | 91–100 |
| Surface meteorology (AWS) | `aws_temp_c` | air temperature | measured | 100 |
| Surface meteorology (AWS) | `aws_rh_pct` | relative humidity | measured | 100 |
| Surface meteorology (AWS) | `aws_pressure_hpa` | station pressure | measured | 100 |
| Surface meteorology (AWS) | `aws_wind_speed_ms` | wind speed | measured | 100 |
| Surface meteorology (AWS) | `aws_wind_dir_sin` | wind direction (sine; 0 when calm) | measured | 100 |
| Surface meteorology (AWS) | `aws_wind_dir_cos` | wind direction (cosine; 0 when calm) | measured | 100 |
| Surface meteorology (AWS) | `aws_rain_mm` | 10-min rainfall | measured | 98–100 |
| Surface meteorology (AWS) | `aws_temp_delta_60m` | change in air temperature over 60 min | derived | 100 |
| Surface meteorology (AWS) | `aws_rh_delta_60m` | change in relative humidity over 60 min | derived | 100 |
| Surface meteorology (AWS) | `aws_pressure_delta_60m` | change in pressure over 60 min | derived | 100 |
| Surface meteorology (AWS) | `aws_rain_sum_180m` | 3-h rainfall | derived | 99–100 |

### ESM_SINTETIS

| Model | Signal only in the 44 predictors | Signal only in the 2-h window | Equal information |
|------------------------------|------------:|------------:|------------:|
| Known ceiling (noise-free signal) | 0.9781 | 0.9774 | 0.9739 |
| Ceiling without the scenario-specific signal | 0.8789 | 0.8096 | 0.9739 |
| LightGBM, 44 predictors | 0.9767 | 0.8648 | 0.9733 |
| LightGBM, 44 predictors + window | 0.9768 | 0.9619 | 0.9733 |
| BiLSTM, 2-h window | 0.8856 | 0.9630 | 0.9731 |
| BiLSTM-hybrid, window + 44 predictors | 0.9626 | 0.9611 | 0.9730 |

### ESM_TUNING

| Model | Selected setting | Validation R²: default → tuned | Configurations better than default on validation | Test R²: default → tuned | ΔR² [95% CI] |
|--------|------------------------------|------------|---------:|------------|----------------|
| LightGBM | learning rate 0.013, 127 leaves, min. 50 samples per leaf, row/column subsampling 0.60/0.67, L1 0.19, L2 6.8 | 0.9202 → 0.9219 | 22 of 29 | 0.9075 → 0.9087 | +0.0012 [+0.0003, +0.0020] |
| LSTM | 2 layers × 64 units, dropout 0.30, head 32, learning rate 2.5 × 10⁻³, batch 256 | 0.9141 → 0.9171 | 25 of 29 | 0.9042 → 0.9045 | +0.0004; ensemble +0.0007 [−0.0003, +0.0018] |

### ESM_BANTEN

| Year | Logger (%) | Portal (%) | Database (%) | AWS-based estimate (%) |
|------|---------:|---------:|---------:|---------:|
| 2022 | 70.8 | 0.3 | 28.9 | 0.1 |
| 2023 | 99.0 | 0.7 | 0.1 | 0.2 |
| 2024 | 99.7 | 0.0 | 0.3 | 0.0 |
| 2025 | 77.6 | 19.0 | 0.9 | 2.5 |

| Against the logger, hourly-mean target | Correlation | RMSE (W m⁻²) | Absolute bias (W m⁻²) |
|--------------------|---------:|---------:|---------:|
| Portal | 0.990 | 33.1 | 0.1 |
| AWS-based estimate | 0.988 | 36.2 | 0.0 |

| Evaluation sample | Origins | Smart persistence R² | CatBoost R² | RMSE (W m⁻²) | Skill | CLP, LightGBM |
|--------------------|---------:|---------:|---------:|---------:|---------:|---------:|
| All origins (main results) | 24,670 | 0.727 | 0.846 | 98.2 | 0.249 | +0.017 |
| Logger and portal | 23,760 | 0.729 | 0.846 | 98.4 | 0.248 | +0.016 |
| Logger only | 19,175 | 0.726 | 0.847 | 98.3 | 0.252 | +0.016 |

### ESM_ENAM

| Station | Logger 2022 (%) | Logger 2023 (%) | Logger 2024 (%) | Logger 2025 (%) | Measured 2025 (%) |
|--------------------|---------:|---------:|---------:|---------:|---------:|
| Banten | 70.8 | 99.0 | 99.7 | 77.6 | 97.4 |
| Bengkulu | 95.6 | 99.0 | 99.8 | 99.8 | 99.9 |
| Jambi | 92.3 | 99.8 | 77.3 | 88.9 | 93.7 |
| Yogyakarta | 58.0 | 100.0 | 99.8 | 98.5 | 100.0 |
| West Kalimantan | 2.6 | 78.6 | 81.7 | 92.4 | 94.3 |
| Central Java | 41.9 | 81.8 | 98.9 | 98.0 | 98.6 |

| Station | Origins, all | Origins, logger only | CatBoost R², all | CatBoost R², logger only | RMSE, all (W m⁻²) | RMSE, logger only (W m⁻²) | CLP, all | CLP, logger only |
|--------------------|---------:|---------:|---------:|---------:|---------:|---------:|---------:|---------:|
| Banten | 24,670 | 19,175 | 0.846 | 0.847 | 98.2 | 98.3 | +0.017 | +0.015 |
| Bengkulu | 24,714 | 24,627 | 0.909 | 0.909 | 89.5 | 89.6 | +0.016 | +0.016 |
| Jambi | 24,758 | 21,741 | 0.878 | 0.880 | 89.7 | 89.8 | +0.028 | +0.027 |
| Yogyakarta | 24,750 | 24,356 | 0.869 | 0.869 | 102.9 | 103.0 | +0.024 | +0.024 |
| West Kalimantan | 24,724 | 22,482 | 0.898 | 0.900 | 98.1 | 97.9 | +0.019 | +0.019 |
| Central Java | 24,730 | 24,173 | 0.903 | 0.905 | 89.4 | 88.8 | +0.013 | +0.014 |