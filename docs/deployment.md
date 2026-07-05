# Deployment

## HPC Deployment

Use the deploy.sh script for automated HPC deployment:

bash deploy.sh

Options:
- --skip-llm: Skip LLM model download (use API mode)
- --step N: Re-run a specific step
- --from N: Resume from step N

## System Requirements

- Python 3.10+
- Singularity / Apptainer
- Nextflow 23+ (nf-core mode only)
- CUDA-capable GPU (for local model inference)

## Docker Demo

A lightweight Docker image is provided for testing the web interface, workflow planning, and command preview without HPC dependencies:

docker build -t modflowagent:latest .
docker run --rm -it -p 8501:8501 -e LLM_API_KEY=your_key -e LLM_API_BASE_URL=https://api.deepseek.com/v1 -e LLM_API_MODEL=deepseek-chat modflowagent:latest
