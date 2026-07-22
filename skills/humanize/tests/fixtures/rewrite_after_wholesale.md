# Discussion

We evaluated a convolutional network for pulmonary nodule triage across two hospitals. On the
held-out set the area under the curve reached 0.94 (95% CI: 0.91-0.97), and per-reader
sensitivity rose from 78% to 91% [@smith2024]. Radiologists spent less time on negative cases,
which matters more in screening than in symptomatic imaging.

Prior work anticipated part of this result [@lee2023]. What differs here is the acquisition
spectrum: earlier series drew from teaching repositories, whereas every examination in this
cohort came from consecutive clinical scanning with the vendor protocols in routine use. Class
imbalance was handled by weighted sampling rather than synthetic oversampling, because
oversampling distorted the calibration curve in pilot runs. The false-positive rate settled at
3.2%.

Three constraints bound the interpretation. Both sites share a regional referral pattern, so
case mix is narrower than a community practice would present. Reference standards were assigned
by consensus rather than histology in a minority of cases. Finally, no reader worked under time
pressure,
and reading-room conditions rarely resemble a research protocol. A prospective screening trial
with per-reader randomization would address all three.
