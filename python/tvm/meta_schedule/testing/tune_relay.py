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
# pylint: disable=missing-docstring
import argparse
import json
import logging
from distutils.util import strtobool
from typing import Dict

import numpy as np  # type: ignore
import tvm
from tvm import meta_schedule as ms
from tvm.meta_schedule.testing.custom_builder_runner import run_module_via_rpc
from tvm.meta_schedule.testing.relay_workload import get_network
from tvm.meta_schedule.testing.tune_utils import create_timer, generate_input_data
from tvm.support import describe


def _parse_args():
    args = argparse.ArgumentParser()
    args.add_argument(
        "--workload",
        type=str,
        required=True,
    )
    args.add_argument(
        "--input-shape",
        type=str,
        required=True,
    )
    args.add_argument(
        "--target",
        type=str,
        required=True,
    )
    args.add_argument(
        "--num-trials",
        type=int,
        required=True,
    )
    args.add_argument(
        "--rpc-host",
        type=str,
        required=True,
    )
    args.add_argument(
        "--rpc-port",
        type=int,
        required=True,
    )
    args.add_argument(
        "--rpc-key",
        type=str,
        required=True,
    )
    args.add_argument(
        "--work-dir",
        type=str,
        required=True,
    )
    args.add_argument(
        "--cache-dir",
        type=str,
        default=None,
    )
    args.add_argument(
        "--number",
        type=int,
        default=3,
    )
    args.add_argument(
        "--repeat",
        type=int,
        default=1,
    )
    args.add_argument(
        "--min-repeat-ms",
        type=int,
        default=100,
    )
    args.add_argument(
        "--adaptive-training",
        type=lambda x: bool(strtobool(x)),
        help="example: True / False",
        default=True,
    )
    args.add_argument(
        "--cpu-flush",
        type=lambda x: bool(strtobool(x)),
        help="example: True / False",
        required=True,
    )
    args.add_argument(
        "--backend",
        type=str,
        choices=["graph", "vm"],
        help="example: graph / vm",
        required=True,
    )
    parsed = args.parse_args()
    parsed.target = tvm.target.Target(parsed.target)
    parsed.input_shape = json.loads(parsed.input_shape)
    parsed.rpc_config = ms.runner.RPCConfig(
        tracker_host=parsed.rpc_host,
        tracker_port=parsed.rpc_port,
        tracker_key=parsed.rpc_key,
        session_timeout_sec=600,
    )
    return parsed


logging.basicConfig(
    format="%(asctime)s.%(msecs)03d %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
logging.getLogger("tvm.meta_schedule").setLevel(logging.INFO)
ARGS = _parse_args()


def main():
    describe()
    print(f"Workload: {ARGS.workload}")

    mod, params, (input_name, input_shape, input_dtype) = get_network(
        ARGS.workload,
        ARGS.input_shape,
        cache_dir=ARGS.cache_dir,
    )
    input_info = [
        {
            "name": input_name,
            "shape": input_shape,
            "dtype": input_dtype,
        },
    ]
    input_data: Dict[str, np.ndarray] = {
        item["name"]: generate_input_data(  # type: ignore
            item["shape"],  # type: ignore
            item["dtype"],  # type: ignore
        )
        for item in input_info
    }
    for item in input_info:
        print(f"  input_name : {item['name']}")
        print(f"  input_shape: {item['shape']}")
        print(f"  input_dtype: {item['dtype']}")

    runner = ms.runner.RPCRunner(
        rpc_config=ARGS.rpc_config,
        evaluator_config=ms.runner.EvaluatorConfig(
            number=ARGS.number,
            repeat=ARGS.repeat,
            min_repeat_ms=ARGS.min_repeat_ms,
            enable_cpu_cache_flush=ARGS.cpu_flush,
        ),
        alloc_repeat=1,
    )

    with ms.Profiler() as profiler:
        lib = ms.tune_relay(
            mod=mod,
            target=ARGS.target,
            config=ms.TuneConfig(
                strategy="evolutionary",
                num_trials_per_iter=64,
                max_trials_per_task=ARGS.num_trials,
                max_trials_global=ARGS.num_trials,
                adaptive_training=ARGS.adaptive_training,
            ),
            runner=runner,  # type: ignore
            work_dir=ARGS.work_dir,
            params=params,
            backend=ARGS.backend,
        )

    print("Tuning Time:")
    print(profiler.table())

    run_module_via_rpc(
        rpc_config=ARGS.rpc_config,
        lib=lib,
        dev_type=ARGS.target.kind.name,
        args=input_data,
        continuation=create_timer(ARGS.backend),
        backend=ARGS.backend,
    )


if __name__ == "__main__":
    main()
