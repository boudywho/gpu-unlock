# Experimental RTX 2050 Laptop (GA107, 10de:25ad)

**Status: boot-time unlock and bounded compute/image-generation tests passed on
one RTX 2050 laptop. Suspend/resume and long-term stability remain unvalidated.**

This branch adds only the GeForce RTX 2050 Laptop device `10de:25ad` to the
existing GA10x recipe, with expected chip identity `0x177` (GA107). It does not
bypass chip, firmware, cold-state, power, readback, or reset checks.

## Target machine

- MSI GF63 Thin 11UCX, subsystem `1462:132e`
- RTX 2050, GA107, 4 GiB VRAM, 16 SMs, CUDA capability 8.6, 64-bit memory bus
- VBIOS `94.07.89.00.0f`
- NVIDIA open driver `615.78.08`
- CachyOS normal kernel `7.3.0-4-cachyos`; LTS `6.18.55-2-cachyos-lts`

## Change and rationale

`recipes.c` now maps `GA107(0x25ad)` to the shared `ga10x` family, preserving
its pinned 610.43.03 firmware, SEC2 Booter, selector writes, and validators.
The family diagnostic label is extended to include GA107.

[NVIDIA source](https://download.nvidia.com/XFree86/NVIDIA-kernel-module-source/NVIDIA-kernel-module-source-610.43.03.tar.xz)
defines GA100 architecture as `0x17` and GA107 implementation as `7`, matching
the project's decoded-chip convention `0x177`.

[PR #69](https://github.com/Zagitta/gpu-unlock/pull/69) reports the shared unlock
working on GA107 `25ac` under an older implementation.
[PR #231](https://github.com/Zagitta/gpu-unlock/pull/231/files) proposes the same
GA107 mapping and includes `25ad`, but its measured GPU is a 3050 Mobile.
[PR #245](https://github.com/Zagitta/gpu-unlock/pull/245) reports a GA107 desktop
card working with NVIDIA 615.78.08. None of these is an RTX 2050 hardware test.

## Host validation completed

- Exact-device recipe test first failed on unmodified source, then passed with
  the local mapping. A portable copy is provided in `tests/test_rtx2050_recipe.py`.
- Module builds with `KCFLAGS=-Werror` on both target kernels.
- Use `LLVM=1` for the clang-built normal kernel; GCC for the GCC-built LTS.
- Firmware download hashes checked against the upstream Arch package pins.
- Actual extracted GSP sections and GA10x boot descriptor pass host parser checks.
- Synthetic 4 GiB layout fits the existing reservation calculation; this does
  not verify actual cold VBIOS layout inputs.

Run the host-only recipe check:

```sh
python3 -m unittest discover -s tests -p test_rtx2050_recipe.py -v
```

## Measured hardware results

The experimental module unlocked this exact laptop before NVIDIA 615.78.08
loaded. Logs show SS0 `0x88888888`, SS1 `0x8`, chip `0xb77000a1`, and
`stage=handoff ret=0 state=4 retained=0 ... cleanup=0`, followed by `unlocked`.
The stock driver and desktop initialized normally. No VBIOS was flashed.

### Image generation

Pinned ComfyUI v0.43.0 (`426f5eea52a7ece1dd599fff4cb6cd1f352ddd24`),
PyTorch 2.14.1+cu130, DreamShaper 8 FP16 from CivitAI (version 128713,
SHA256 `879db523c30d3b9017143d56705015e15a2cb5628762c11d086fed9538abd7fd`).
Same checkpoint bytes, prompt, seed 42, 512x512, batch 1, 20 steps,
DPM++ 2M/Karras, CFG 7, FP16 UNet, FP32 VAE and PyTorch attention in both
phases. Reduced-precision matrix reductions disabled. Server node caching
disabled; one warm-up plus three timed generations per run.

| Median | Stock | Unlocked run 1 | Unlocked repeat after 45s idle |
| --- | ---: | ---: | ---: |
| Total seconds/image | 7.998 | 7.219 | 7.295 |
| Sampling-stage seconds | 6.665 | 5.936 | 6.032 |

This is about **9.6-10.8% higher end-to-end throughput**, or **8.8-9.7% less
time per image**, in this workflow. Sampling-stage time includes node setup
and model preparation, not only GPU denoising kernels. All timed same-seed
outputs were pixel-identical within each phase; compared samples were also
exactly RGB-pixel-identical across stock/unlocked phases. This is not a
guarantee for every model or prompt.

### Compute and bounded checks

4096-cubed cuBLAS GEMM, FP32 accumulation, 2s warm-up per mode, median of
five samples of five calls, stock power limits:

| Mode | Stock TFLOPS | Unlocked run 1 | Unlocked repeat |
| --- | ---: | ---: | ---: |
| FP16 | 11.61 | 12.14 | 12.87 |
| BF16 | 12.00 | 18.85 | 17.11 |
| TF32 | 6.89 | 11.27 | 11.12 |
| FP32 control | 3.90 | 3.75 | 3.78 |

BF16 timings varied substantially; these are observed run medians, not a
guaranteed speedup. The all-ones sampled-output checks passed. Separate random
256x256 FP16/BF16/FP32 matrix products were finite and agreed with a CPU FP64
reference within expected low-precision error (relative Frobenius errors
0.000208 / 0.001663 / 0.000000206). Those random checks were run after unlock,
not a saved bitwise pre/post GEMM comparison.

Image tests sampled about 3.5 GiB peak VRAM; first unlocked image run peaked
at 67 C versus 72 C in the initial stock run. Thermal starting conditions
were not locked, so this is not evidence of improved thermal efficiency.
No Xid/AER/unlock-failure lines were found during these bounded tests.
Runtime D3 reports unsupported on this system and suspended-time remained zero;
the 45-second idle check is not validation of power-gating recovery.

## Hardware acceptance criteria

- [x] Separate opt-in experimental boot image; unchanged normal/LTS fallback.
- [x] Unlock runs before NVIDIA binds, and hands off without retained DMA buffers.
- [x] NVIDIA initializes normally; real FP16/BF16 compute works afterward.
- [x] Same-method before/after GEMM with FP32 accumulation and numerical checks.
- [x] Same ComfyUI commit, dependencies, model SHA256, prompt, seed, sampler,
      resolution and precision in image-generation A/B.
- [x] No new Xid/AER/driver failures during the bounded tests.
- [x] Short idle/workload persistence without changing runtime PM.
- [ ] Longer idle, power-gating recovery and battery-life testing.
- [ ] Separately test suspend/resume when physical recovery is available.

Do not interpret a compiled module or an `unlocked` log as a measured speedup.
[Issue #111](https://github.com/Zagitta/gpu-unlock/issues/111) and
[issue #246](https://github.com/Zagitta/gpu-unlock/issues/246) describe laptop
persistence/registration pitfalls. Runtime power-off or GSP reinitialization
can erase the selectors. Do not force live driver unbinding on a running desktop.

These results establish a working boot-time experiment on one laptop, not full
compatibility across RTX 2050 boards. The test entry disables resume re-unlock;
sleep/hibernate are not validated. Normal CachyOS remains the default and
the unchanged normal/LTS boot images remain available as fallbacks.
