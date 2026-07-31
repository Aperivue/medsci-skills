# Friction — every point that needed engineering knowledge

A medical-AI researcher and an agent claiming "clinicians need no engineer" is self-serving unless
the record shows where it was false. This file is that record. It is deliberately the least
flattering document in the demo.

Site-specific detail (host names, paths, scheduler configuration, institution) is removed: it would
not run anywhere else and it is not the lesson. What survives is the class of problem and what it
cost.

## The pattern under most of it

**Every failure below was silent, or looked like success.** That is not a coincidence — it is what
makes them expensive for someone without an engineer to ask. A clinician's error signal is "the
command printed something red". Four of these printed nothing, and two printed a *result*.

---

## 1. Getting onto the hardware at all

SSH key setup, scheduler basics, reading a 36-page cluster manual, and `pip install` behaviour on a
shared login node. **Roughly a day, before any imaging code was written.** None of it is clinical
knowledge and none of it transfers to another site — which is exactly why it is logged here as
friction rather than turned into tooling. A skill that encoded one lab's job-submission conventions
would be a liability somewhere else.

## 2. "The GPU runs" ≠ "the stack runs on this GPU" — twice, in opposite directions

The demo deliberately used the oldest idle GPUs available (Pascal generation, compute capability
6.1) as a courtesy to the lab.

- A naive support check said the GPU was **unsupported**: `torch.cuda.get_arch_list()` does not list
  `sm_61` for the installed build. It runs anyway, via CUDA minor-version forward compatibility. A
  clinician reading that list would have concluded, wrongly, that they needed different hardware.
- Then the inverse: nnU-Net v2 enables `torch.compile` by default, which pulls in a compiler that
  **refuses** compute capability < 7.0. The job died after 41 seconds reporting *"background workers
  are no longer alive"* — a message that names neither the GPU nor the compiler. Fix: one
  environment variable (`nnUNet_compile=f`). Finding it required knowing that the message was a
  symptom of a worker crash, not a worker problem.

## 3. The scheduler returns a job ID identically on success and on doom

Three separate jobs cost a day each before this became the working rule: **a submitted job is not a
running job.** Verify the queue and the log, not the submission. Two contributing site facts —
container images being node-local, and one node having no route to the container registry — both
manifested only as jobs that were accepted and then quietly did nothing.

## 4. Absolute symlinks are invisible inside a container

The inference inputs were built with absolute symlink targets. The prediction container bind-mounts
the project tree at a different path, so inside the container every link dangled. nnU-Net reported
**"There are 0 cases in the source folder"** and **exited 0**. `set -euo pipefail` does not catch a
tool that succeeds at doing nothing.

The tell was that the job's own `ls` printed 9 cases on the host while the container saw 0. A
clinician sees a correct `ls` and a green job.

Fix: relative symlinks, which resolve identically on the host and inside the mount — and the builder
script patched so a re-run cannot regress.

## 5. A job's environment is not the environment you tested in — three times

`import nibabel` failed on the compute node with `ModuleNotFoundError: typing_extensions`. On the
login node the same import worked, so `pip install --user` reported "already satisfied" and did
nothing: the package was present in a **system** path that the compute nodes do not have, while they
read the per-user path. The same shape recurred for `packaging` weeks later, and it killed the third
rung's evaluation **after** its predictions had already been computed on a GPU.

Two fixes, one for the instance and one for the family:

1. Force the package into the per-user path every node reads (`--force-reinstall --no-deps`).
2. **Decouple the cheap stage from the expensive one.** Scoring never needed a GPU; it was bound to
   the prediction job only out of convenience, and that is what turned a missing module into a lost
   GPU run. Evaluation now runs as its own CPU-only job with a **dependency probe that fails in one
   second, before the first case is scored.**

That second fix is the generalisable one: *a pipeline that couples a cheap stage to an expensive one
makes the cheap stage's failure expensive.*

## 6. The schedule was arithmetic, not preference

nnU-Net's default is 1000 epochs. Measured epoch time on this hardware was 360–417 s → ~4.2 days per
fold, ~21 days for five folds. That is not a judgement call about training length; it is a number
that makes the default impossible and has to be **measured before it can be disclosed**. Knowing to
measure it first is engineering knowledge.

## 7. The finding itself required reading a file nobody was told to read

Rung 3's collapse is explained by one field in `plans.json` — the normalisation scheme, fixed at
fingerprint time and carried with the checkpoint. Diagnosing it required knowing that such a file
exists, that the normaliser travels with the model rather than being chosen per input, and that an
intensity clip is where a cross-modality run dies rather than in the network.

The clinician did everything the literature tells them to do: checked the licence, checked the
citations, honoured a patient-level held-out split, validated on a genuinely external cohort. None of
those steps looks at that field.

---

## What this cost, and what it says

Nine days wall-clock; roughly 50 GPU-hours; four failures that produced no error, one that produced a
plausible result. The parts a clinician could do alone were the *scientific* parts — the design, the
pre-specified evaluation plan, the disclosure decisions, the refusal to score a target-free case as
zero. The parts that needed an engineer were, without exception, **infrastructure and silent
failure**.

So the honest answer to the demo's question is not yes and not no: a clinician can carry the study,
and will lose days to things that announce nothing. The tooling worth building is the tooling that
makes silent failures loud — which is what the deterministic gates in this repository are for, and
[the gap this demo found](README.md#rung-3-is-the-finding-a-silent-normaliser-not-mri-is-hard) is one
they did not yet cover.
