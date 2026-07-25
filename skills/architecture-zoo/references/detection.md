# Detection architectures (architecture-zoo)

For "find and localise lesions" questions — boxes / points, a count, and a per-lesion
hit/miss (FROC). Distinct from segmentation (a pixel mask) and classification (a per-image
label): detection localises *instances*. `/model-scaffold --task detection` emits a
torchvision Faster R-CNN repo whose FROC/mAP you compute downstream.

Each card: **paper → core idea → when to use → medical-imaging use → reference impl →
validation/experiment setup.**

---

## Self-configuring 3-D detection (the default to beat)

### nnDetection
- **Paper**: Baumgartner et al., "nnDetection: A Self-configuring Method for Medical Object
  Detection," *MICCAI* 2021.
- **Core idea**: nnU-Net's philosophy applied to **detection** — auto-configures
  preprocessing, anchors, network topology, and training from the dataset fingerprint for
  **3-D volumetric** lesion detection, with no manual tuning. (First release is 3-D only; no
  2-D / Mask R-CNN.)
- **When to use**: the **default to beat** for 3-D medical lesion detection (nodules,
  aneurysms, focal lesions on CT/MR), exactly as nnU-Net is for segmentation — start here and
  justify any custom detector against it; it removes the anchor/scale tuning a torchvision
  detector needs.
- **Medical-imaging use**: LUNA16-style nodule detection, 3-D lesion / aneurysm detection.
- **Reference impl**: `MIC-DKFZ/nnDetection` (Apache-2.0). Integrate, do not reimplement.
- **Validation setup**: report **FROC** (sensitivity per false-positive-per-scan); its
  internal CV is development-time optimism correction, not external validation
  (`/model-validation` MD3/MD6); keep the patient-level split consistent end to end.

---

## Two-stage detectors (region proposal → classify)

### R-CNN → Fast R-CNN → Faster R-CNN (+ FPN)
- **Papers**: Girshick et al., R-CNN, *CVPR* 2014; Girshick, Fast R-CNN, *ICCV* 2015; Ren
  et al., Faster R-CNN, *NeurIPS* 2015; Lin et al., **FPN**, *CVPR* 2017.
- **Core idea**: Faster R-CNN adds a learned Region Proposal Network (end-to-end); FPN adds
  a multi-scale feature pyramid so small and large lesions are both detected.
- **When to use**: the **default two-stage detector** for medical lesion detection — strong,
  well-understood, good on small objects with FPN; favour accuracy over real-time speed.
- **Medical-imaging use**: nodule / lesion / aneurysm detection on CT / MR / mammography
  (ResNet-FPN backbone).
- **Reference impl**: torchvision `fasterrcnn_resnet50_fpn`; MONAI detection (RetinaNet).
- **Validation setup**: report **FROC** (sensitivity per false-positive-per-scan) or **mAP
  with the IoU match criterion stated**; per-lesion analysis with patient-level clustering
  disclosed; not patient-level accuracy (`/model-validation` MD6).

### Mask R-CNN (detect + segment instances)
- **Paper**: He et al., Mask R-CNN, *ICCV* 2017.
- **Core idea**: a mask head on Faster R-CNN → per-instance box + class + mask.
- **When to use**: **count + localise + delineate** separate lesions (instance-level), not a
  single semantic mask (that is `segmentation.md`).
- **Reference impl**: torchvision `maskrcnn_resnet50_fpn`.
- **Validation setup**: detection metrics for the boxes + per-instance Dice for the masks.

## One-stage / query-based detectors (faster, end-to-end)

### RetinaNet (focal loss)
- **Paper**: Lin et al., "Focal Loss for Dense Object Detection," *ICCV* 2017.
- **Core idea**: a one-stage dense detector with **focal loss** to handle the extreme
  foreground/background imbalance — relevant when lesions are sparse.
- **When to use**: faster than two-stage, strong under heavy class imbalance.
- **Reference impl**: torchvision `retinanet_resnet50_fpn`; MONAI detection.

### YOLO family (incl. modern Ultralytics)
- **Papers**: Redmon et al., YOLO, *CVPR* 2016; YOLOv3+/YOLOX; **YOLOv8 / YOLOv11**
  (Ultralytics, 2023–24) are the current widely-used releases.
- **Core idea**: a single network predicts boxes + classes directly on a grid — real-time.
- **When to use**: speed-critical / interactive settings; for maximal sensitivity on small
  medical lesions, two-stage detectors or **nnDetection** (3-D) are usually preferred.
- **Licence — check before commercial use**: **Ultralytics YOLOv8/v11 are AGPL-3.0** (strong
  copyleft — a deployed derivative must itself be open-sourced, or you buy Ultralytics'
  commercial licence). If that is a problem, prefer an Apache/MIT detector — **RT-DETR**
  (real-time DETR), torchvision Faster R-CNN, or MONAI RetinaNet.

### DETR / RT-DETR (transformer, set prediction)
- **Papers**: Carion et al., "End-to-End Object Detection with Transformers," *ECCV* 2020;
  **RT-DETR** (Zhao et al., *CVPR* 2024) — a real-time, permissively licensed variant.
- **Core idea**: a transformer treats detection as direct **set prediction** (no anchors /
  NMS) via learned object queries + bipartite matching; RT-DETR makes it real-time.
- **When to use**: large datasets where an anchor-free, end-to-end pipeline is attractive;
  more data-hungry and slower to converge than CNN detectors. **RT-DETR (Apache-2.0)** is the
  permissively licensed real-time alternative to Ultralytics YOLO's AGPL.
- **Reference impl**: the official DETR repo; Deformable DETR for faster convergence; RT-DETR.

---

## Choosing among these
**3-D volumetric lesion detection → nnDetection** (self-configuring, the default to beat).
2-D lesion detection → **Faster R-CNN + FPN** (torchvision; `/model-scaffold --task
detection`). Sparse lesions / imbalance → **RetinaNet (focal loss)**. Count + delineate
instances → **Mask R-CNN**. Speed-critical → **YOLO** (mind the **AGPL-3.0** licence) or
**RT-DETR** (Apache-2.0). Large data, anchor-free → **DETR**.
Always report **FROC / mAP with the IoU criterion stated**, per-lesion with patient-level
clustering disclosed. Record the choice + paper, hand to `/model-scaffold`, validate with
`/model-validation` and `/model-evaluation`.
