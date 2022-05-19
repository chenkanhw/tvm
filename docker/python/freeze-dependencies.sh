#!/bin/bash -eux
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


# Build base images (one per Python architecture) used in building the remaining TVM docker images.
set -eux

cd "$(dirname "$0")/../.."

# NOTE: working dir inside docker is repo root.
docker/bash.sh -i "${BUILD_TAG}.ci_py_deps:latest" python3 docker/python/freeze_deps.py \
               --ci-constraints=docker/python/ci-constraints.txt \
               --gen-requirements-py=python/gen_requirements.py \
               --template-pyproject-toml=pyproject.toml \
               --output-base=docker/python/build
