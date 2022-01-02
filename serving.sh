#!/bin/bash
export TF_XLA_FLAGS=--tf_xla_auto_jit=1

if [ "$2" ]; then
    echo "Using user provided path to models"
    PATH_TO_MODELS="$2"
    echo "$PATH_TO_MODELS"
else
    echo "Using default path to models"
    # path to models
    PATH_TO_MODELS=/mnt/SSD/Temp/MLsas/models/
    echo "$PATH_TO_MODELS"
fi

if [[ "$1" == "cpu" ]]; then
    echo "Running on CPU"
    docker run --name tf_serving \
        -d \
        --restart always \
        --privileged \
        --cpus 6 \
        --memory 5g \
        --shm-size=1g \
        --ulimit memlock=-1 \
        --ulimit stack=67108864 \
        -p 8500:8500 \
        -p 8501:8501 \
        -v "$PATH_TO_MODELS:/models" \
        tensorflow/serving:2.7.0-gpu \
        --model_config_file=/models/models.config \
        --enable_batching=true \
        --batching_parameters_file=/models/batching.config

else
    echo "Running on GPU"
    docker run --name tf_serving \
        -d \
        --restart always \
        --privileged \
        --cpus="1.5" \
        --gpus all \
        --memory 5g \
        --shm-size=1g \
        --ulimit memlock=1024 \
        --ulimit stack=67108864 \
        -p 8500:8500 \
        -p 8501:8501 \
        -v "$PATH_TO_MODELS:/models" \
        tensorflow/serving:2.7.0-gpu \
        --model_config_file=/models/models.config \
        --grpc_channel_arguments=grpc.max_concurrent_streams=1000 \
        --per_process_gpu_memory_fraction=0.35 \
        --enable_batching=true \
        --batching_parameters_file=/models/batching.config \
        --tensorflow_session_parallelism=2

fi
