from unittest.mock import MagicMock, patch
import pytest


def _make_mock_nvml(gpus: list[dict]):
    mock = MagicMock()
    mock.nvmlDeviceGetCount.return_value = len(gpus)

    def get_handle(i):
        return f"handle_{i}"

    def get_mem_info(handle):
        idx = int(handle.split("_")[1])
        info = MagicMock()
        info.free = gpus[idx]["free_mb"] * 1024 * 1024
        info.total = gpus[idx]["total_mb"] * 1024 * 1024
        info.used = (gpus[idx]["total_mb"] - gpus[idx]["free_mb"]) * 1024 * 1024
        return info

    def get_util(handle):
        idx = int(handle.split("_")[1])
        util = MagicMock()
        util.gpu = gpus[idx]["gpu_util"]
        util.memory = 0
        return util

    def get_name(handle):
        idx = int(handle.split("_")[1])
        return f"GPU_{idx}"

    mock.nvmlDeviceGetHandleByIndex.side_effect = get_handle
    mock.nvmlDeviceGetMemoryInfo.side_effect = get_mem_info
    mock.nvmlDeviceGetUtilizationRates.side_effect = get_util
    mock.nvmlDeviceGetName.side_effect = get_name
    return mock


def test_selects_gpu_with_most_free_memory():
    gpus = [
        {"free_mb": 4096, "total_mb": 8192, "gpu_util": 50},
        {"free_mb": 7000, "total_mb": 8192, "gpu_util": 10},
    ]
    mock_nvml = _make_mock_nvml(gpus)
    with patch.dict("sys.modules", {"pynvml": mock_nvml}):
        from importlib import import_module, reload
        import app.services.gpu_selector as gs
        reload(gs)
        result = gs.get_freest_gpu()
    assert result == 1


def test_tiebreak_by_lower_utilization():
    gpus = [
        {"free_mb": 8000, "total_mb": 8192, "gpu_util": 80},
        {"free_mb": 8000, "total_mb": 8192, "gpu_util": 5},
    ]
    mock_nvml = _make_mock_nvml(gpus)
    with patch.dict("sys.modules", {"pynvml": mock_nvml}):
        from importlib import reload
        import app.services.gpu_selector as gs
        reload(gs)
        result = gs.get_freest_gpu()
    assert result == 1


def test_returns_minus_one_when_no_gpus():
    mock_nvml = MagicMock()
    mock_nvml.nvmlDeviceGetCount.return_value = 0
    with patch.dict("sys.modules", {"pynvml": mock_nvml}):
        from importlib import reload
        import app.services.gpu_selector as gs
        reload(gs)
        result = gs.get_freest_gpu()
    assert result == -1


def test_returns_minus_one_on_nvml_error():
    mock_nvml = MagicMock()
    mock_nvml.nvmlInit.side_effect = Exception("NVML init failed")
    with patch.dict("sys.modules", {"pynvml": mock_nvml}):
        from importlib import reload
        import app.services.gpu_selector as gs
        reload(gs)
        result = gs.get_freest_gpu()
    assert result == -1


def test_get_all_gpu_status_returns_list():
    gpus = [{"free_mb": 6000, "total_mb": 8192, "gpu_util": 20}]
    mock_nvml = _make_mock_nvml(gpus)
    with patch.dict("sys.modules", {"pynvml": mock_nvml}):
        from importlib import reload
        import app.services.gpu_selector as gs
        reload(gs)
        status = gs.get_all_gpu_status()
    assert isinstance(status, list)
    assert status[0]["id"] == 0
    assert "memory_free_mb" in status[0]
