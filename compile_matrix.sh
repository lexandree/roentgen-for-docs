#!/bin/bash
set -e

# Configuration
REPO_URL="https://github.com/ggml-org/llama.cpp.git"
BUILD_DIR="llama_cpp_matrix"
ARCH="61"

# The testing matrix
# Format: "CondaEnvName CudaVersion GCCVersion CudaChannel"
declare -a MATRIX=(
    "build_cu124 12.4.0 12 nvidia/label/cuda-12.4.0"
    "build_cu121 12.1.1 11 nvidia/label/cuda-12.1.1"
    "build_cu118 11.8.0 11 nvidia"
)

echo "======================================================"
echo " Starting llama.cpp Compilation Matrix for GTX 1060"
echo "======================================================"

# 1. Prepare fresh source directory
if [ -d "$BUILD_DIR" ]; then
    echo "Cleaning up previous source directory ($BUILD_DIR)..."
    rm -rf "$BUILD_DIR"
fi
echo "Cloning latest llama.cpp..."
git clone --quiet "$REPO_URL" "$BUILD_DIR"

# Ensure conda is available in the script
source "$(conda info --base)/etc/profile.d/conda.sh" || {
    echo "Error: Conda initialization failed. Make sure conda is installed and accessible."
    exit 1
}

# 2. Iterate through the matrix
for config in "${MATRIX[@]}"; do
    read -r env_name cuda_ver gcc_ver cuda_channel <<< "$config"
    echo -e "\n------------------------------------------------------"
    echo " Testing Environment: $env_name"
    echo " CUDA: $cuda_ver | GCC: $gcc_ver | Channel: $cuda_channel"
    echo "------------------------------------------------------"
    
    # 2.1 Remove old environment if it exists
    if conda info --envs | grep -q "^$env_name "; then
        echo "Removing existing conda environment '$env_name'..."
        conda remove -n "$env_name" --all -y --quiet
    fi

    # 2.2 Create environment
    echo "Creating isolated conda environment..."
    if ! conda create -n "$env_name" -c "$cuda_channel" -c conda-forge \
        "cuda-toolkit=$cuda_ver" "gcc_linux-64=$gcc_ver" "gxx_linux-64=$gcc_ver" cmake ninja -y --quiet; then
        echo "❌ [FAILED] Failed to create environment $env_name. Skipping."
        continue
    fi

    # 2.3 Activate and configure build
    conda activate "$env_name"
    
    cd "$BUILD_DIR"
    
    # Clean previous build artifacts
    rm -rf "build_$env_name"
    
    echo "Configuring CMake for CUDA $cuda_ver..."
    if ! cmake -B "build_$env_name" -G Ninja \
        -DGGML_CUDA=ON \
        -DCMAKE_CUDA_ARCHITECTURES="$ARCH" \
        -DCMAKE_C_COMPILER="$CONDA_PREFIX/bin/x86_64-conda-linux-gnu-gcc" \
        -DCMAKE_CXX_COMPILER="$CONDA_PREFIX/bin/x86_64-conda-linux-gnu-g++" > /dev/null 2>&1; then
        
        echo "❌ [FAILED] CMake configuration failed for $env_name."
        cd ..
        conda deactivate
        continue
    fi
    
    # 2.4 Compile
    echo "Compiling (this may take a few minutes)..."
    if ! cmake --build "build_$env_name" --config Release -j "$(nproc)" > /dev/null 2>&1; then
        echo "❌ [FAILED] Compilation failed for $env_name."
        cd ..
        conda deactivate
        continue
    fi

    # 2.5 Success!
    echo "✅ [SUCCESS] Compiled successfully in $env_name!"
    echo "Binary located at: $BUILD_DIR/build_$env_name/bin/llama-server"
    
    # We found a working build, we can stop here or continue testing the rest.
    # Let's break after the first successful build to save time.
    echo "Stopping matrix test as we have a successful build."
    cd ..
    conda deactivate
    exit 0

done

echo -e "\n======================================================"
echo " ❌ All matrix configurations failed."
echo " Check the output above for specific error messages."
echo "======================================================"
