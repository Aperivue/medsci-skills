# Detection architectures (architecture-zoo)

For "find and localise lesions" questions — boxes / points, a count, and a per-lesion
hit/miss (FROC). Distinct from segmentation (a pixel mask) and classification (a per-image
label): detection localises *instances*. `/model-scaffold --task detection` emits a
torchvision Faster R-CNN repo whose FROC/mAP you compute downstream.

Each card: **paper → core idea → when to use → medical-imaging use → reference impl →
validation/experiment setup.**

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

### YOLO family
- **Papers**: Redmon et al., YOLO, *CVPR* 2016; later YOLOv3+/YOLOX.
- **Core idea**: a single network predicts boxes + classes directly on a grid — real-time.
- **When to use**: speed-critical / interactive settings; usually two-stage detectors are
  preferred for maximal sensitivity on small medical lesions.

### DETR (transformer, set prediction)
- **Paper**: Carion et al., "End-to-End Object Detection with Transformers," *ECCV* 2020.
- **Core idea**: a transformer treats detection as direct **set prediction** (no anchors /
  NMS) via learned object queries + bipartite matching.
- **When to use**: large datasets where an anchor-free, end-to-end pipeline is attractive;
  more data-hungry and slower to converge than CNN detectors.
- **Reference impl**: the official DETR repo; Deformable DETR for faster convergence.

---

## Choosing among these
Default lesion detection → **Faster R-CNN + FPN** (torchvision; `/model-scaffold --task
detection`). Sparse lesions / imbalance → **RetinaNet (focal loss)**. Count + delineate
instances → **Mask R-CNN**. Speed-critical → **YOLO**. Large data, anchor-free → **DETR**.
Always report **FROC / mAP with the IoU criterion stated**, per-lesion with patient-level
clustering disclosed. Record the choice + paper, hand to `/model-scaffold`, validate with
`/model-validation` and `/model-evaluation`.
