# SimpleOCR vLLM Deployment Guide

## Quick Start

### 1. Install vLLM Server

```bash
# Install vLLM (requires Python 3.8+, CUDA 11.8+ for GPU)
pip install vllm>=0.8.5

# For CPU-only (slower, not recommended for production)
pip install vllm-cpu
```

### 2. Start vLLM Server

```bash
# GPU deployment (recommended)
vllm serve Qwen/Qwen3-0.6B \
  --host 0.0.0.0 \
  --port 8000 \
  --dtype auto \
  --max-model-len 4096

# CPU deployment (for testing only)
vllm serve Qwen/Qwen3-0.6B \
  --device cpu \
  --port 8000
```

### 3. Configure SimpleOCR

Create or update `.env`:

```bash
# Enable AI extraction
VLLM_ENABLED=true
VLLM_SERVER_URL=http://localhost:8000
VLLM_MODEL_NAME=Qwen/Qwen3-0.6B

# Performance tuning
VLLM_TIMEOUT=30
VLLM_MAX_RETRIES=3
VLLM_MAX_TOKENS=512
VLLM_TEMPERATURE=0.1

# Extraction settings
AI_USE_FALLBACK=true
AI_MIN_CONFIDENCE=0.5
```

### 4. Install SimpleOCR Dependencies

```bash
# Install all dependencies including AI modules
pip install -r requirements.txt
```

### 5. Run SimpleOCR

```bash
# With AI extraction
python main.py --use-ai --max-emails 10

# With custom vLLM server
python main.py --use-ai --vllm-url http://remote-server:8000
```

## System Requirements

### Minimum Requirements
- **CPU**: 4+ cores
- **RAM**: 8GB
- **GPU**: 2GB VRAM (or CPU for testing)
- **Disk**: 5GB (for model cache)
- **Python**: 3.8+

### Recommended for Production
- **CPU**: 8+ cores
- **RAM**: 16GB
- **GPU**: NVIDIA GPU with 4GB+ VRAM
- **Disk**: 10GB SSD
- **Python**: 3.10+

## Performance Optimization

### vLLM Server Settings

```bash
# High-throughput configuration
vllm serve Qwen/Qwen3-0.6B \
  --max-model-len 4096 \
  --max-num-seqs 256 \
  --gpu-memory-utilization 0.9 \
  --dtype bfloat16 \
  --enable-prefix-caching

# Low-latency configuration
vllm serve Qwen/Qwen3-0.6B \
  --max-model-len 2048 \
  --max-num-seqs 32 \
  --gpu-memory-utilization 0.7
```

### SimpleOCR Optimization

```bash
# Adjust timeout for slower systems
VLLM_TIMEOUT=60

# Reduce max tokens for faster responses
VLLM_MAX_TOKENS=256

# Increase temperature for more creative extraction
VLLM_TEMPERATURE=0.3
```

## Troubleshooting

### vLLM Server Issues

**Server won't start:**
```bash
# Check CUDA installation
nvidia-smi

# Check vLLM installation
python -c "import vllm; print(vllm.__version__)"

# Try CPU mode
vllm serve Qwen/Qwen3-0.6B --device cpu
```

**Out of memory errors:**
```bash
# Reduce GPU memory utilization
vllm serve Qwen/Qwen3-0.6B --gpu-memory-utilization 0.5

# Reduce max sequence length
vllm serve Qwen/Qwen3-0.6B --max-model-len 2048
```

### SimpleOCR Connection Issues

**Connection refused:**
```bash
# Check server is running
curl http://localhost:8000/health

# Test with explicit URL
python main.py --use-ai --vllm-url http://127.0.0.1:8000
```

**Timeout errors:**
```bash
# Increase timeout in .env
VLLM_TIMEOUT=60
```

## Docker Deployment

### Dockerfile for vLLM Server

```dockerfile
FROM vllm/vllm-openai:latest

ENV MODEL_NAME=Qwen/Qwen3-0.6B
ENV PORT=8000

CMD ["--host", "0.0.0.0", "--port", "8000", "--model", "Qwen/Qwen3-0.6B"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  vllm:
    image: vllm/vllm-openai:latest
    ports:
      - "8000:8000"
    environment:
      - MODEL_NAME=Qwen/Qwen3-0.6B
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

## Production Deployment

### Recommended Architecture

```
Internet → Load Balancer → SimpleOCR (3 instances)
                             ↓
                        vLLM Server Pool (2 instances)
                             ↓
                        GPU Cluster
```

### Monitoring

```bash
# Monitor vLLM server
curl http://localhost:8000/metrics

# Check SimpleOCR logs
tail -f simpleocr.log
```

### Scaling

- **Horizontal**: Run multiple vLLM servers with load balancer
- **Vertical**: Use larger GPU (8GB+ VRAM) for better throughput
- **Batch**: Process receipts in batches for efficiency

## Security

1. **Network Isolation**: Run vLLM on internal network
2. **Authentication**: Add API key authentication to vLLM
3. **Encryption**: Use HTTPS/TLS for production
4. **Rate Limiting**: Implement rate limiting on vLLM endpoints

## Cost Estimation

### Cloud Deployment (AWS)
- **vLLM Server**: g4dn.xlarge (~$0.50/hour)
- **SimpleOCR**: t3.medium (~$0.04/hour)
- **Total**: ~$400/month (24/7)

### On-Premise
- **Hardware**: $2,000-5,000 (one-time)
- **Power**: ~$50/month
- **Total**: ~$50/month + amortized hardware

## Support

For issues:
1. Check vLLM documentation: https://docs.vllm.ai/
2. Check SimpleOCR logs
3. Test with regex fallback: `python main.py` (without --use-ai)

