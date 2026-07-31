# Demo 5 - across-cohort segmentation results

Bootstrap: 10000 resamples, seed 20260725. Metric CIs are median [2.5-97.5 pct].
Accuracy is not reported (target ~0.2-0.4% of volume). Dice/HD95 on scored cases only.

## Per-arm summary (Dice, HD95, Delta-Dice from internal)

| arm | n scored | Dice median [95% CI] | n with HD95 | HD95 mm median [95% CI] | dDice vs internal |
|---|---:|---|---:|---|---|
| rung1 MSD held-out (internal) | 9 | 0.9595 [0.9367-0.9734] | 9 | 1.7846 [1.5898-2.5000] |  |
| rung2 AMOS CT (external) | 298 | 0.8932 [0.8633-0.9108] | 270 | 5.6784 [4.8546-8.4253] | -0.0662 [-0.0996--0.0416] |
| rung3 AMOS MRI (modality shift) | 59 | 0.0152 [0.0000-0.0626] | 40 | 70.0457 [45.6939-129.6796] | -0.9443 [-0.9715--0.8813] |

## Target-free cases (§4 - never a silent zero)

- rung1 MSD held-out (internal): none
- rung2 AMOS CT (external): 2 target-free; 2 predicted a (false) organ ['amos_0057', 'amos_0115']
- rung3 AMOS MRI (modality shift): 1 target-free; 0 predicted a (false) organ 

## Pre-specified subgroups (§7 - identical cut-points across arms)

Volume edges [100.0, 250.0] mL; slice-thickness edges [2.0, 5.0] mm (fixed, recorded).

### rung1 MSD held-out (internal)
- **Spleen volume (gt_ml)**
    - small (<100 mL): n=1, Dice 0.9367 [0.9367-0.9367]
    - normal (100-250 mL): n=4, Dice 0.9517 [0.9205-0.9668]
    - enlarged (>=250 mL): n=4, Dice 0.9725 [0.9549-0.9803]
- **Slice thickness (spacing_z)**
    - thin (<2 mm): n=3, Dice 0.9595 [0.9549-0.9668]
    - mid (2-5 mm): n=2, Dice 0.9403 [0.9367-0.9439]
    - thick (>=5 mm): n=4, Dice 0.9725 [0.9205-0.9803]

### rung2 AMOS CT (external)
- **Spleen volume (gt_ml)**
    - small (<100 mL): n=37, Dice 0.8157 [0.0549-0.9031]
    - normal (100-250 mL): n=194, Dice 0.9114 [0.8940-0.9254]
    - enlarged (>=250 mL): n=67, Dice 0.7694 [0.6134-0.8681]
- **Slice thickness (spacing_z)**
    - thin (<2 mm): n=5, Dice 0.9219 [0.8584-0.9368]
    - mid (2-5 mm): n=74, Dice 0.9292 [0.8888-0.9412]
    - thick (>=5 mm): n=219, Dice 0.8752 [0.8310-0.8974]

### rung3 AMOS MRI (modality shift)
- **Spleen volume (gt_ml)**
    - small (<100 mL): n=7, Dice 0.0000 [0.0000-0.2402]
    - normal (100-250 mL): n=41, Dice 0.0343 [0.0000-0.2717]
    - enlarged (>=250 mL): n=11, Dice 0.0000 [0.0000-0.0401]
- **Slice thickness (spacing_z)**
    - thin (<2 mm): n=26, Dice 0.0057 [0.0000-0.1021]
    - mid (2-5 mm): n=33, Dice 0.0343 [0.0000-0.2717]
    - thick (>=5 mm): n=0, Dice n/a
