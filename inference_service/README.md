# Face inference service

Separate FastAPI service for CPU face recognition using InsightFace only.

## Endpoints

- `GET /health`: liveness check; model weights are loaded lazily.
- `POST /embed`: returns one InsightFace embedding for each usable face.
- `POST /recognize`: compares a single-face frame against the enrolled embedding gallery. A match is returned when the best InsightFace cosine similarity meets the configured threshold.

Every POST endpoint requires the `X-API-Key` header. Set `FACE_INFERENCE_API_KEY` to a long random secret on the service and configure the same value as `FACE_INFERENCE_API_KEY` in the Flask app service. Configure `FACE_INFERENCE_URL` in Flask to this service's base URL.

## Render deployment

Create a Docker web service from this repository, branch `main`, Dockerfile path `inference_service/Dockerfile`, and build context `.`. The model weights download on first inference and are not committed to Git. The service uses the smaller `buffalo_s` model by default and loads only one recognition model to reduce memory use. Free instances may still sleep or run out of memory; verify the service with real frames before relying on it for attendance.

## Thresholds and limitations

Defaults are conservative starting points, not validated biometric thresholds. Set `INSIGHTFACE_THRESHOLD` only after evaluating a consented validation set for the deployment environment. This service intentionally rejects frames containing more than one face for attendance matching. A match is not proof of liveness; add presentation-attack/liveness checks before relying on it for high-stakes attendance.

Store biometric embeddings securely, restrict service access, and obtain appropriate consent. Do not use raw face images or embeddings as public logs.
