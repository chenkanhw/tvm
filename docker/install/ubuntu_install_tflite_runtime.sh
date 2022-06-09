#!/bin/bash
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

set -e
set -u
set -o pipefail

# The tflite version should have matched versions to the tensorflow
# version installed from pip in ubuntu_install_tensorflow.sh
TENSORFLOW_VERSION=$(python3 -c "import tensorflow; print(tensorflow.__version__)" 2> /dev/null)

# Download, build and install flatbuffers
git clone --branch=v1.12.0 --depth=1 --recursive https://github.com/google/flatbuffers.git
cd flatbuffers
cmake -G "Unix Makefiles" -DCMAKE_BUILD_TYPE=Release
make install -j8
cd ..

# Build the TFLite static library, necessary for building with TFLite ON.
# The library is built at:
# tensorflow/tensorflow/lite/tools/make/gen/*/lib/libtensorflow-lite.a.
git clone https://github.com/tensorflow/tensorflow --branch=v${TENSORFLOW_VERSION} --depth 1
./tensorflow/tensorflow/lite/tools/make/download_dependencies.sh
./tensorflow/tensorflow/lite/tools/make/build_lib.sh
