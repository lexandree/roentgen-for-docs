#!/bin/bash
# Initialize conda properly within the script
source "$(conda info --base)/etc/profile.d/conda.sh"

# Activate the build environment containing CUDA toolkit 12.4
conda activate build_cu124

echo "Starting hardware-accelerated MedGemma Native C++ server..."
echo "Configuration: -c 6144 (Safe for GTX 1060 VRAM) | -np 3 (Slots) | GBNF Grammar"

./llama_cpp_matrix/build_build_cu124/bin/llama-server \
  -m models/medgemma-1.5-4b.gguf \
  --mmproj models/mmproj-model-f16.gguf \
  -c 6144 \
  -np 3 \
  -ngl 24 \
  --port 8002 \
  --host 127.0.0.1 \
  --chat-template-file src/api/templates/medgemma.jinja \
  --cache-reuse 1
