# Developer Guide: Full CUDA-Accelerated Setup on Ubuntu with GTX 1060

This document provides a step-by-step guide to configure a development environment for this project on a Linux machine (Ubuntu/Debian-based) with an NVIDIA GTX 1060. It covers all necessary steps to compile `llama-cpp-python` with full CUDA support for GPU acceleration.

This process was validated on a system with a GTX 1060, an NVIDIA Driver supporting CUDA 13.0, and a fresh Conda installation.

## The Goal

The primary challenge is to compile `llama-cpp-python` from source to ensure it can offload model layers to the GPU. This requires a specific version of the CUDA Toolkit and a compatible C++/C compiler, all managed within a self-contained Conda environment to avoid system-wide conflicts.

## Step-by-Step Installation

### Step 1: Install System-Level Build Tools

The compilation process requires essential build tools like `gcc`, `g++`, and `make`.

1.  Open a terminal and update your package lists:
    ```bash
    sudo apt-get update
    ```

2.  Install the `build-essential` package:
    ```bash
    sudo apt-get install build-essential
    ```
    This provides the necessary C/C++ compilers that will be used by CMake and `pip`.

### Step 2: Create and Configure the Conda Environment (Multi-Step)

This is the most critical part. We will create a Conda environment in stages to avoid known dependency conflicts (specifically with the `gdb` package in `conda-forge`).

1.  **Clean up any previous attempts.** If a `medgemma` environment exists, remove it completely to ensure a fresh start.
    ```bash
    conda deactivate
    # The -rf flag is crucial for cleaning up after failed installations
    rm -rf /path/to/your/miniconda3/envs/medgemma 
    ```

2.  **Create a base environment** with only Python and the specific CUDA Toolkit required by the NVIDIA driver. We use CUDA 11.8 for its broad compatibility and stability with the GTX 1060 architecture.
    ```bash
    conda create -n medgemma -c nvidia python=3.12 'cuda-toolkit=11.8' -y
    ```

3.  **Activate the new environment.**
    ```bash
    conda activate medgemma
    ```

4.  **Install the compatible C/C++ compilers** into the active environment. CUDA Toolkit 11.8 is not compatible with GCC versions newer than 11. We install GCC 11 from `conda-forge` to satisfy this requirement.
    ```bash
    conda install -c conda-forge 'gcc_linux-64=11' 'gxx_linux-64=11' -y
    ```

### Step 3: Install Python Dependencies and Compile `llama-cpp-python`

1.  **Install base Python packages** using `pip`.
    ```bash
    pip install fastapi uvicorn pydantic pydantic-settings aiosqlite google-api-python-client apscheduler python-multipart transformers accelerate Pillow
    ```

2.  **Fix potential dependency conflicts.** A common warning involves `sympy`. Manually install the version required by PyTorch for a clean setup (this step is optional but recommended).
    ```bash
    pip install sympy==1.13.1
    ```

3.  **Compile and install `llama-cpp-python` with CUDA support.** This is the final and longest step. The environment variables tell the installer to build the library from source using the CUDA backend (`GGML_CUDA`).
    
    *   First, ensure any old version is gone:
        ```bash
        pip uninstall llama-cpp-python -y
        ```
    *   Then, run the compilation command. We explicitly set the CUDA architecture to `61` (which corresponds to the GTX 1060's Pascal architecture) to prevent "no kernel image available" errors.
        ```bash
        CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=61" FORCE_CMAKE=1 pip install --no-cache-dir llama-cpp-python
        ```
        This process will take a significant amount of time (potentially 30-60 minutes) as it compiles the entire C++/CUDA library from scratch, using all available CPU cores. **Do not interrupt it.**

## Step 4: Final Setup and Verification

1.  **Create a `models` directory** in the root of the project.
    ```bash
    mkdir -p models
    ```

2.  **Download the models.** Since MedGemma 1.5 is a multimodal model (LLaVA architecture), you must download **two** files and place them inside the `models` directory:
    *   The main quantized model: `medgemma-1.5-4b.gguf` (e.g., Q4_K_M or Q6_K version).
    *   The vision projector model: `mmproj-model-f16.gguf`.

3.  **Run the Worker.** You can now launch the API worker. It will load both the model and the projector, offloading layers to your GTX 1060.
    ```bash
    python -m src.api.worker
    ```

The worker is now ready to receive inference requests from the dispatcher.
