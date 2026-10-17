# Face inference service

Separate FastAPI service for CPU inference with InsightFace and FaceNet.

## Endpoints

- `GET /health`: liveness check; model weights are loaded lazily.
- `POST /embed`: returns InsightFace and FaceNet embeddings for each usable face.
- `POST /recognize`: compares a single-face frame against the enrolled embedding gallery. A match is returned only when both models pass their thresholds and agree on the same student ID.

Every POST endpoint requires the `X-API-Key` header. Set `FACE_INFERENCE_API_KEY` to a long random secret on the service and configure the same value as `FACE_INFERENCE_API_KEY` in the Flask app service. Configure `FACE_INFERENCE_URL` in Flask to this service's base URL.

## Render deployment

Create a Docker web service from this repository, branch `main`, Dockerfile path `inference_service/Dockerfile`, and build context `.`. The model weights download on first inference and are not committed to Git. A 2 GB instance is a practical minimum; 4 GB is safer for loading both models. Free instances can run out of memory or sleep and are not suitable for reliable attendance operation.

## Thresholds and limitations

Defaults are conservative starting points, not validated biometric thresholds. Set `INSIGHTFACE_THRESHOLD` and `FACENET_THRESHOLD` only after evaluating a consented validation set for the deployment environment. This service intentionally rejects frames containing more than one face for attendance matching. A match is not proof of liveness; add presentation-attack/liveness checks before relying on it for high-stakes attendance.

Store biometric embeddings securely, restrict service access, and obtain appropriate consent. Do not use raw face images or embeddings as public logs.
