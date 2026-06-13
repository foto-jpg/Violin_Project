import os

from loguru import logger

# pynvml is GPU-only - absent on HF Free CPU. Import lazily so this module
# (imported by routes/system.py at startup) still loads on a GPU-less box.
try:
    import pynvml
    _PYNVML_AVAILABLE = True
except ImportError:
    _PYNVML_AVAILABLE = False
    logger.info("pynvml not available - running in CPU-only mode")


def _is_cpu_mode() -> bool:
    """True when all GPU logic should be bypassed (HF Free CPU / no pynvml)."""
    return os.getenv("DISABLE_GPU") == "1" or not _PYNVML_AVAILABLE


def get_freest_gpu() -> int:
    if _is_cpu_mode():
        return -1
    try:
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        if device_count == 0:
            logger.warning("No GPU detected, falling back to CPU")
            return -1

        free_memory_per_device = []
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            free_memory_per_device.append({
                "id": i,
                "free_mb": mem_info.free // (1024 * 1024),
                "total_mb": mem_info.total // (1024 * 1024),
                "gpu_util_pct": util.gpu,
            })

        sorted_gpus = sorted(
            free_memory_per_device,
            key=lambda x: (-x["free_mb"], x["gpu_util_pct"]),
        )
        chosen = sorted_gpus[0]
        logger.info(f"Selected GPU {chosen['id']} ({chosen['free_mb']} MB free)")
        return chosen["id"]
    except Exception as e:
        logger.error(f"GPU selection failed: {e}")
        return -1
    finally:
        try:
            pynvml.nvmlShutdown()
        except Exception:
            pass


def get_all_gpu_status() -> list[dict]:
    if _is_cpu_mode():
        return []
    try:
        pynvml.nvmlInit()
        result = []
        for i in range(pynvml.nvmlDeviceGetCount()):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(handle)
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            result.append({
                "id": i,
                "name": name if isinstance(name, str) else name.decode(),
                "memory_used_mb": mem.used // (1024 ** 2),
                "memory_total_mb": mem.total // (1024 ** 2),
                "memory_free_mb": mem.free // (1024 ** 2),
                "gpu_util_pct": util.gpu,
                "memory_util_pct": util.memory,
            })
        return result
    except Exception as e:
        logger.warning(f"GPU status unavailable: {e}")
        return []
    finally:
        try:
            pynvml.nvmlShutdown()
        except Exception:
            pass
