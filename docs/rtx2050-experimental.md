# Experimental RTX 2050 Laptop (GA107, 10de:25ad)

**Status: source port and host builds tested; hardware unlock NOT yet validated.**

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

## Hardware acceptance criteria (pending)

- [ ] Separate opt-in experimental boot image; unchanged normal/LTS fallback.
- [ ] Unlock runs before NVIDIA binds, and hands off without retained DMA buffers.
- [ ] NVIDIA initializes normally; real FP16/BF16 compute works afterward.
- [ ] Same-method before/after GEMM with FP32 accumulation and numerical checks.
- [ ] Same ComfyUI commit, dependencies, model SHA256, prompt, seed, sampler,
      resolution and precision in image-generation A/B.
- [ ] No new Xid/AER/driver failures during the bounded tests.
- [ ] Check idle persistence; evaluate power/battery cost of any runtime-PM change.
- [ ] Separately test suspend/resume when physical recovery is available.

Do not interpret a compiled module or an `unlocked` log as a measured speedup.
[Issue #111](https://github.com/Zagitta/gpu-unlock/issues/111) and
[issue #246](https://github.com/Zagitta/gpu-unlock/issues/246) describe laptop
persistence/registration pitfalls. Runtime power-off or GSP reinitialization
can erase the selectors. Do not force live driver unbinding on a running desktop.

No image-generation speedup or full RTX 2050 compatibility is claimed by this
branch until the pending hardware criteria have actually been exercised.
