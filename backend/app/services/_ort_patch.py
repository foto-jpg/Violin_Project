import os
import sys
import runpy

import onnxruntime as ort

GPU_MEM_LIMIT = int(os.environ.get("OEMER_GPU_MEM_LIMIT_BYTES", 5 * 1024 ** 3))

DEFAULT_CUDA_OPTS = {
    "arena_extend_strategy": "kSameAsRequested",
    "gpu_mem_limit": str(GPU_MEM_LIMIT),
    "cudnn_conv_algo_search": "HEURISTIC",
}


def _inject_opts(providers):
    new_list = []
    for entry in providers:
        if isinstance(entry, tuple) and entry[0] == "CUDAExecutionProvider":
            opts = dict(entry[1] or {})
            for k, v in DEFAULT_CUDA_OPTS.items():
                opts.setdefault(k, v)
            new_list.append(("CUDAExecutionProvider", opts))
        elif entry == "CUDAExecutionProvider":
            new_list.append(("CUDAExecutionProvider", dict(DEFAULT_CUDA_OPTS)))
        else:
            new_list.append(entry)
    return new_list


_orig_init = ort.InferenceSession.__init__


def _patched_init(self, path_or_bytes, sess_options=None, providers=None, provider_options=None, **kw):
    if providers:
        providers = _inject_opts(providers)
    elif "CUDAExecutionProvider" in ort.get_available_providers():
        providers = [
            ("CUDAExecutionProvider", dict(DEFAULT_CUDA_OPTS)),
            "CPUExecutionProvider",
        ]
    return _orig_init(
        self,
        path_or_bytes,
        sess_options=sess_options,
        providers=providers,
        provider_options=provider_options,
        **kw,
    )


ort.InferenceSession.__init__ = _patched_init


def _shrink_oemer_batch():
    import oemer.inference as _inf
    desired = int(os.environ.get("OEMER_BATCH_SIZE", "2"))
    _orig = _inf.inference

    def _wrapped(*a, **kw):
        kw.setdefault("batch_size", desired)
        return _orig(*a, **kw)

    _inf.inference = _wrapped


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python -m app.services._ort_patch <oemer args...>", file=sys.stderr)
        sys.exit(2)
    _shrink_oemer_batch()
    sys.argv = ["oemer"] + sys.argv[1:]
    runpy.run_module("oemer.ete", run_name="__main__")
