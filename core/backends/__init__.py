"""Ergo GPU backends.

Each backend is a vendor-specific module that consumes a GPUPlan
(from ir_gpu.py) and an IRModule, and emits:
  1. Device code in the target IR (NVVM, SPIR-V, RVV, etc.)
  2. Host launch code (C99) for the target runtime API.

The kernel extraction pass (ir_gpu.py) is vendor-neutral and shared
by all backends.

Backends register themselves in BACKENDS so the driver can look them
up by name.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..ir import IRModule
    from ..ir_gpu import GPUPlan


class KernelBackend:
    """Base interface for GPU kernel backends.

    Subclasses must implement generate() and generate_host_launches().
    """

    # Human-readable name for diagnostics
    name: str = "unknown"

    # File extension for emitted device code
    device_ext: str = ".ll"

    def __init__(self, module: 'IRModule', plan: 'GPUPlan',
                 gpu_fast_math: bool = False):
        self.module = module
        self.plan = plan
        self.gpu_fast_math = gpu_fast_math
        self._f32_warned: set = set()  # kernel ids already warned about
                                       # f32 transcendental evaluation

    def generate(self) -> str:
        """Emit device code (IR text) for all extracted kernels."""
        raise NotImplementedError

    def generate_host_launches(self) -> str:
        """Emit C99 host code for kernel launches via the target runtime."""
        raise NotImplementedError


# Registry: target name -> backend class
BACKENDS: dict[str, type[KernelBackend]] = {}


def register_backend(target_name: str, cls: type[KernelBackend]):
    """Register a backend class under a target name."""
    BACKENDS[target_name] = cls


def get_backend(target_name: str) -> type[KernelBackend]:
    """Look up a backend by target name. Raises KeyError if not found."""
    if target_name not in BACKENDS:
        available = ", ".join(sorted(BACKENDS.keys())) or "(none)"
        raise KeyError(
            f"Unknown target '{target_name}'. Available: {available}")
    return BACKENDS[target_name]
