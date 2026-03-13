# Developer Guide: Full CUDA-Accelerated Setup on Ubuntu with GTX 1060

This document provides a step-by-step guide to configure a local inference server for this project on a Linux machine (Ubuntu/Debian-based) with an NVIDIA GTX 1060. 

Instead of fighting with Python wrappers (`llama-cpp-python`), we will compile the official, native C++ `llama-server` directly from source. This guarantees maximum performance, lowest VRAM usage, and avoids complex Python environment conflicts with CUDA libraries.

## The Goal

Compile `llama.cpp` with full CUDA backend support (`GGML_CUDA=ON`) tailored specifically for the GTX 1060's Pascal architecture (Compute Capability 6.1).

## Step-by-Step Installation

### Step 1: Install System Build Tools

The compilation process requires `cmake` and essential C/C++ compilers.

```bash
sudo apt-get update
sudo apt-get install build-essential cmake git -y
```

### Step 2: Prepare CUDA Environment (via Conda)

If you already have a full system-wide NVIDIA CUDA Toolkit installed, you can skip this step. However, if you are using Conda, the cleanest way to get the necessary CUDA libraries (like `nvcc` and `libcudart`) without modifying your host OS is to install them into your active environment.

1. Activate your environment:
   ```bash
   conda activate medgemma
   ```
2. Install the CUDA 12.4 Toolkit (compatible with driver version 13.x):
   ```bash
   conda install -c "nvidia/label/cuda-12.4.0" cuda-toolkit -y
   ```

### Step 3: Clone and Compile `llama.cpp`

We will pull the latest source code from the official repository and compile it.

1. **Clone the repository** (do this in the root of your `roentgen-for-docs` project or alongside it):
   ```bash
   git clone https://github.com/ggml-org/llama.cpp
   cd llama.cpp
   ```

2. **Configure the build with CMake:**
   Here we explicitly enable CUDA (`-DGGML_CUDA=ON`). To drastically speed up compilation time, we also tell the compiler to *only* build for the GTX 1060 architecture (`-DCMAKE_CUDA_ARCHITECTURES=61`).
   
   ```bash
   cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=61
   ```

3. **Build the server:**
   Use the `-j` flag to compile using multiple CPU cores (e.g., `-j 8` if you have 8 threads).
   ```bash
   cmake --build build --config Release -j 8
   ```
   *Note: This process usually takes 5-10 minutes.*

### Step 4: Download Models

Ensure you have a `models` directory in your main `roentgen-for-docs` folder. You must have both the main model and the vision projector:
*   Main model: `medgemma-1.5-4b.gguf` (Q4_K_M recommended for 6GB VRAM).
*   Vision projector: `mmproj-model-f16.gguf`.

## Running the Server

Once compiled, the binary will be located in the `build/bin/` directory.

Start the native server, offloading 24 layers to the GPU (`-ngl 24`). The context size (`-c 2048`) is enough for a standard medical image analysis.

```bash
./llama.cpp/build/bin/llama-server \
  -m models/medgemma-1.5-4b.gguf \
  --mmproj models/mmproj-model-f16.gguf \
  -ngl 24 \
  -c 2048 \
  --port 8080 \
  --host 127.0.0.1
```

**Verification:**
1. Watch the terminal output during startup. You should see `ggml_cuda_init: found 1 CUDA devices` and `llm_load_tensors: offloaded 24/28 layers to GPU`.
2. Open a new terminal and run `nvidia-smi`. You should see `llama-server` occupying approximately 3GB of VRAM.

## Connecting the Bot

Finally, tell the Dispatcher API to route requests to your newly compiled C++ server.

Update the `INFERENCE_WORKERS` JSON string in your `.env` (or `src/api/config.py`):
```json
INFERENCE_WORKERS={"local_cpp":{"name":"GTX 1060 (C++)","url":"http://127.0.0.1:8080/v1/chat/completions"}}
```

Restart your Python API Dispatcher. Your bot is now fully hardware-accelerated.
