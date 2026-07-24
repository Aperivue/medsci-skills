# Challenge — the provenance conflict a licence check cannot see

You have chosen an architecture and found a concrete implementation: a public repository, well
cited, permissively licensed, whose task matches yours and whose code runs on your hardware. You
plan to report an internal validation on a public benchmark and an external validation on your
own cohort.

Every check a careful person performs by hand passes. The licence is real and permissive. The
paper is peer-reviewed and highly cited. The task matches. The code executes.

**The one fact that decides how your internal number should be read is not in any of those
places.** If the method was developed, tuned, or competed against the benchmark family you are
about to evaluate it on, that arm is not an independent test of it — however scrupulously you
held out your own split. It reads like validation and is closer to a training-set score, and
nothing in the repository will tell you, because the conflict lives in the relationship between
two facts that sit in different documents.

## Task

Write a **model dossier** for the artifact — source and version pin, licence and the file it was
read from, intended use, whether weights are pretrained and on what, the model's task versus the
study's, its reported validation, what it was developed on, and your evaluation arms — then run
the gate over it:

```bash
python3 ../check_model_provenance.py --dossier fixture/dossier_defect.json --strict
```

## What the fixtures show

- `dossier_defect.json` — facts that **contradict each other**: an arm on the benchmark the model
  was developed on, that same arm inside the pretraining corpus, a non-commercial licence under
  commercial intent, a mismatched task, no pin, no reported validation, unverified hardware.
- `dossier_unstated.json` — facts that are **absent**: no licence, pretrained weights of unknown
  provenance, no pin. A different failure and the more common one; an unstated licence is not a
  permissive licence.
- `dossier_clean.json` — everything stated and consistent. It still records
  `developed_on: ExampleBench`, and **nothing fires**, because no evaluation arm uses
  ExampleBench. Being developed on a benchmark is not a defect; evaluating on it is.

## Verify

```bash
bash verify.sh
```

Deterministic and network-free: no repository is fetched and no licence is resolved online. An
unstated fact is a finding, never a value the gate guesses at.
