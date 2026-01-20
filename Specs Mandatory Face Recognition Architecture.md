Addendum — Mandatory Face Recognition Architecture

Status: Normative / Blocking
Applies to: Face enrollment and face-based attendance
Priority: Critical

1. Prohibited Technologies

The following are strictly forbidden for this project:

Haar Cascade classifiers (any variant)

Eye detection–based alignment

Raw image comparison

Template matching

Histogram / pixel / SSIM similarity

Any “confidence percentage” not derived from a biometric model

Any solution using the above will be rejected.

2. Mandatory Detection Component

Face detection must use a modern deep-learning–based detector.

Required detector:

RetinaFace

No alternative detectors are permitted.

3. Mandatory Recognition Component

Face recognition must be embedding-based using a pretrained deep biometric model.

Required recognizer:

InsightFace (ArcFace)

No alternative recognizers are permitted.

4. Mandatory Identity Representation

Each employee face identity must be represented as a biometric embedding vector.

Raw face images must not be stored permanently.

Only the embedding vector and employee metadata may be persisted.

5. Mandatory Matching Logic

Live face input must be converted into an embedding vector using ArcFace.

Stored employee embeddings must be compared using vector similarity.

The best match must be selected.

Acceptance must be decided using a calibrated similarity threshold.

6. Mandatory Confidence Percentage

The displayed “confidence percentage” must:

Be derived from the biometric similarity score

Be a monotonic mapping of similarity → percentage

Reflect match strength, not image similarity

7. Mandatory Offline Operation

All detection and recognition must run fully offline.

No cloud APIs or external services are permitted.

8. Compliance Rule

Any implementation that:

Uses Haar cascades

Uses image comparison

Does not use RetinaFace + ArcFace

Stores raw face images

Computes confidence from pixel similarity

is considered non-compliant and must be reworked.