# Frequency-Based Quality Index for Contactless Respiratory Volume Analysis

Python research code for assessing the quality of contactless respiratory signals using frequency-domain **Respiration-to-Noise Ratio (RNR)** indices, with utilities for Intel RealSense acquisition and depth-derived respiration extraction.

Associated paper: **[Development and Validation of a Frequency-Based Quality Index for Contactless Respiratory Volume Analysis](https://doi.org/10.1109/JSEN.2025.3645915)** — Antonio Nocera, Linda Senigagliesi, Gianluca Ciattaglia, Michela Raimondi, and Ennio Gambi, *IEEE Sensors Journal*.

## Why assess respiratory signal quality?

Depth cameras can recover breathing-related torso motion without contact sensors, but sensor noise, body sway, and occlusions can corrupt the waveform. **Respiration-to-Noise Ratio (RNR)** estimates signal quality from its power spectral density (PSD), supporting the comparison of extraction methods and identification of unreliable recording segments.

The paper contributes:

- A comparison of harmonic, fixed-band, and peak-based frequency-domain indices against known SNR.
- A theoretical analysis of their saturation limits and usable SNR ranges.
- An evaluation of harmonic count, frequency bandwidth, and observation duration.
- Validation with Gaussian noise, measured RealSense noise, and real breathing recordings.

## Method and parameter choices

For the integrated harmonic and fixed-band indices:

$$
\mathrm{RNR}=10\log_{10}\left(\frac{\sum_k S_{xx}(f_k)M(f_k)}{\sum_k S_{xx}(f_k)[1-M(f_k)]}\right).
$$

Here, `M` selects the frequencies attributed to respiration. Frequencies outside the mask form the noise-power estimate. Higher RNR indicates greater spectral concentration in the selected respiratory bands.

| Paper notation | Frequency selection | Repository API |
| --- | --- | --- |
| RNRh | Bands around the estimated respiratory fundamental and its harmonics | `RNRh(..., integration=True)` |
| RNRf | A fixed interval, evaluated as 0–1 Hz and 0.1–0.7 Hz in the paper | `RNRfixed_window(f, Sxx, f1, f2)` |
| RNRp | Respiratory peak versus the sum of the remaining spectral bins | `RNRh(..., integration=False, peak_sum=True)` |
| RNR′p | Respiratory peak versus the mean of the remaining spectral bins | `RNRh(..., integration=False, peak_mean=True)` |

**λ in the paper corresponds to `df` in the code: it is a half-width.** For example, `df=0.05` selects a band extending approximately ±0.05 Hz around each harmonic. The study evaluates λ = 0.05, 0.1, 0.2, and 0.4 Hz and one, two, or three harmonics, counting the fundamental as the first harmonic.

### Choosing a bandwidth

| Goal | Finding from the paper | Practical implication |
| --- | --- | --- |
| Detect quality changes with camera distance or arm occlusions | λ = 0.4 Hz showed the greatest sensitivity in the tested recordings | Consider a wider mask when these disturbances are the main concern. |
| Detect low-frequency body sway | λ = 0.05 Hz best distinguished sitting from standing in the Kinect recordings | A narrower mask can classify sway outside the respiratory peak as noise. |
| Select harmonic count | Adding harmonics had a limited effect compared with mask width | Select bandwidth first, then assess whether additional harmonics help. |
| Choose observation duration | Shorter observations increased variability in the RNR–SNR error | Balance temporal responsiveness against spectral stability. |

These findings guide parameter selection for the tested conditions; they do not establish a universal default or rejection threshold. A wider mask can include body motion in the estimated respiratory power.

### Interpretation and limits

RNR approximates SNR only over a parameter-dependent range. At very low SNR, noise dominates both parts of the mask; at very high SNR, respiratory energy outside the mask limits the index. Section IV-A derives these saturation limits.

For white noise, the low-SNR limit is approximately `10 * log10(m / (B - m))`, where `m` is the mask bandwidth and `B` is the analyzed one-sided spectral bandwidth. The high-SNR limit depends on the fraction of respiratory power captured by the mask. Sampling rate, analyzed bandwidth, and mask choice therefore affect the numerical result.

RNR assesses waveform quality; depth displacement is not automatically calibrated respiratory volume in liters. The estimated spectral peak is also not an independent reference measurement of respiratory rate.

## Validation reported in the paper

| Experiment | Data and protocol | What it evaluates |
| --- | --- | --- |
| Added Gaussian noise | Public motion-capture data: 11 subjects, 52 free-breathing trials, 16 torso markers; SNR from −30 to 27 dB in 3 dB steps | Agreement between RNR and known SNR; bandwidth, harmonics, and observation duration. |
| Added camera noise | Temporal noise recorded from a static wall at 0.5–3.5 m with an Intel RealSense D455, then added to reference respiratory signals | Reliability with noise measured from the target sensor. |
| Real breathing recordings | Five RealSense volunteers, 1–3 m, 12–20 breaths/min, 120 s at 15 fps and 640 × 480; public Kinect V2 recordings from 19 subjects at 1–4 m | Sensitivity to distance, ROI, posture, motion, and occlusions. |

For the pseudo-simulated experiments, reference motion signals were filtered with a fourth-order 0.08–0.8 Hz Butterworth bandpass, averaged across markers, and converted into 30 Hz realizations. The main analysis used 120 s windows with a 60 s step, with shorter observations also assessed. These preprocessing steps construct the reference signals **before noise is added**; applying a narrow respiratory bandpass to a noisy test signal would change the noise power and the meaning of its RNR.

Across the defined usable SNR ranges, the evaluated indices achieved **MAE < 2 dB**, **RMSE < 3 dB**, and **Pearson correlation of 0.97–0.99**. These results do not apply uniformly across the entire −30 to 27 dB sweep. Real recordings assess sensitivity to expected quality changes because their true SNR is unknown. The paper recommends an approximately 2 m operating distance for the D455 to remain in the region of strong RNR–SNR correspondence under the tested conditions.

Reference datasets are described in:

- Shafiq and Veluvolu, *Multimodal chest surface motion data for respiratory and cardiovascular monitoring applications*, Scientific Data, 2017 — paper reference [15].
- Kempfle and Van Laerhoven, *Breathing In-Depth: A Parametrization Study on RGB-D Respiration Extraction Methods*, 2021 — paper reference [7].

The results above belong to the published study. The quick-start example below illustrates the API using a synthetic waveform.

## Repository contents

| File | Purpose |
| --- | --- |
| `RNRfunctions.py` | Fixed-band and harmonic RNR indices, spectral band-power calculations, and filtering utilities. |
| `FUNCTIONS_depth_derived_respiration.py` | Torso, chest, and abdomen ROI extraction; mean/median depth signals; invalid-value handling and interpolation. |
| `skeleton_functions.py` | YOLO pose-keypoint extraction and skeleton visualization. |
| `RECORD_FUNCTIONS.py` | RealSense RGB/depth recording, camera intrinsics, and optional pose extraction. |
| `main_RECORD.py` | Configurable recording example. |

The repository provides individual processing components. It does not currently include datasets, a complete reproduction script for the paper, a requirements file, or Kinect acquisition code.

## Installation

Clone the repository and install the dependencies needed for your workflow:

```bash
git clone https://github.com/TLCunivpm/Frequency-based-Quality-Index-for-Contactless-Respiratory-Volume-Analysis.git
cd Frequency-based-Quality-Index-for-Contactless-Respiratory-Volume-Analysis

# Quality-index calculations only
python -m pip install numpy scipy matplotlib

# Additional dependencies for depth/pose processing and camera acquisition
python -m pip install opencv-python ultralytics pyrealsense2 pandas
```

Camera acquisition requires a compatible Intel RealSense device and working RealSense SDK support. Pose extraction uses a YOLO pose model such as `yolo11n-pose.pt`; its weights must be available locally or downloadable. Package versions are not pinned in the repository.

## Quick start: calculate RNR

Run this example from the repository directory. It generates a synthetic respiratory waveform and computes its harmonic RNR without requiring a camera or dataset.

```python
import numpy as np
from scipy.signal import periodogram
from RNRfunctions import RNRh

fs = 15.0  # Sampling frequency in Hz
t = np.arange(0, 120, 1 / fs)
rng = np.random.default_rng(42)
signal = np.sin(2 * np.pi * 0.25 * t) + 0.3 * rng.standard_normal(t.size)

f, psd = periodogram(signal, fs=fs, detrend="constant", scaling="density")
rnr_db, respiratory_power, noise_power, f_resp, mask, bandwidth = RNRh(
    f, psd, df=0.05, n_harmonics=1, integration=True
)

print(f"Respiratory frequency: {f_resp:.3f} Hz")
print(f"Respiratory rate: {60 * f_resp:.1f} breaths/min")
print(f"RNR: {rnr_db:.2f} dB")
```

Expected output for this example:

```text
Respiratory frequency: 0.250 Hz
Respiratory rate: 15.0 breaths/min
RNR: 7.52 dB
```

## API details and implementation notes

`RNRh` returns:

```python
rnr_db, respiratory_power, noise_power, f_resp, mask, mask_bandwidth = RNRh(
    f, psd, df=0.05, n_harmonics=1, integration=True
)
```

`f_resp` is in Hz and `mask_bandwidth` is in Hz. Power estimates use the units implied by the supplied PSD. `RNRfixed_window` returns four values: RNR, respiratory power, noise power, and interval width.

Use a finite, one-sided PSD on a uniformly spaced frequency grid and the actual signal sampling rate. Check for missing values before computing the PSD. Zero power or empty selections can produce undefined results.

Important details of the current implementation:

- The executable peak search uses **0.1 < f < 1 Hz**; the paper describes a 0–1 Hz search, while some code docstrings mention 0.1–0.7 Hz.
- Frequency-mask boundaries use strict inequalities, so boundary bins are excluded.
- In the peak-based branches, the peak index is calculated within a restricted spectrum but reused to exclude a bin from the full spectrum. Review this indexing before reproducing RNRp or RNR′p results.
- Peak-mode flags are independent. Use only the intended mode and set `integration=False` for a peak-based calculation. The returned `mask` is populated by the integration branch.
- RNR′p depends on spectral bin count through the mean-noise denominator; its values should not be compared directly with integrated RNR values.

The quick start uses the integrated harmonic branch. It is a usage demonstration, not a reproduction of the full experimental pipeline.

## Record RGB-D data

1. Connect the RealSense camera.
2. Edit `main_RECORD.py`: set a valid `root_folder` and fill in `subject_name`, `distance`, `light_conditions`, `subjectpose`, and `BPM`.
3. Adjust acquisition settings if needed, then run:

```bash
python main_RECORD.py
```

The supplied call requests **640 × 480 RGB/depth frames at 15 fps**, for **1,800 frames** (approximately two minutes). Press **q** or **Esc** to stop early.

The recorder saves:

| Output | Content |
| --- | --- |
| `color_data.npy` | Color frames in OpenCV BGR channel order. |
| `depth_data.npy` | Depth frames aligned to color, scaled to meters. |
| `depth_intrinsics_dict.pickle` | Camera intrinsic parameters. |

The optional `record_YOLO(...)` function also saves keypoints and an FPS vector. Current recording and image-saving paths use Windows-style separators; adapt those paths for Linux/macOS.

## Extract a depth-derived respiratory signal

Given aligned `depth_data` and `color_data` arrays from the recorder:

```python
from FUNCTIONS_depth_derived_respiration import extract_resp_ROI_video

signals = extract_resp_ROI_video(
    depth_data,
    color_data,
    model="yolo11n-pose.pt",
    type=["torso", "chest", "abdomen"],
    show=False,
)

chest_mean = signals["chest"][:, 0]
chest_median = signals["chest"][:, 1]
```

Each ROI returns an array of shape `(n_frames, 2)`, containing mean and median depth. The video function detects shoulder/hip keypoints in the **first frame** and keeps the ROI fixed, assuming a static or quasi-static subject. It requires a valid first-frame pose detection. Invalid ROIs can yield NaNs; inspect and handle missing values before spectral analysis, and use the actual sampling frequency of your signal.

These outputs describe depth variation associated with breathing; they are not automatically calibrated into liters.

## Citation

If you use this code or the method in your research, please cite:

> A. Nocera, L. Senigagliesi, G. Ciattaglia, M. Raimondi, and E. Gambi, “Development and Validation of a Frequency-Based Quality Index for Contactless Respiratory Volume Analysis,” *IEEE Sensors Journal*, vol. 26, no. 3, pp. 5062–5076, 2026. doi: [10.1109/JSEN.2025.3645915](https://doi.org/10.1109/JSEN.2025.3645915).

```bibtex
@article{nocera2026frequency,
  author  = {Nocera, Antonio and Senigagliesi, Linda and Ciattaglia, Gianluca and Raimondi, Michela and Gambi, Ennio},
  title   = {Development and Validation of a Frequency-Based Quality Index for Contactless Respiratory Volume Analysis},
  journal = {IEEE Sensors Journal},
  year    = {2026},
  volume  = {26},
  number  = {3},
  pages   = {5062--5076},
  doi     = {10.1109/JSEN.2025.3645915}
}
```

## License

No license file is currently included in the repository. Contact the maintainers for clarification of reuse terms.
