#!/usr/bin/env python3
"""Compile and exercise the actual recipe lookup without accessing GPU hardware."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / 'kernel' / 'gpu_unlock'
SOURCE = r'''
#include <stdio.h>
#include <string.h>
#include "recipes.h"
int main(void)
{
    const struct gu_card *reference = gu_card_find(0x2504);
    const struct gu_card *target = gu_card_find(0x25ad);
    if (!reference || reference->chip != 0x176)
        return fprintf(stderr, "GA106 reference recipe missing\n"), 1;
    if (!target)
        return fprintf(stderr, "RTX 2050 25ad recipe missing\n"), 1;
    if (target->chip != 0x177 || target->family != reference->family ||
        target->family->fwsec_version != 3 ||
        strcmp(target->family->booter->file,
               "gpu-unlock/610.43.03/booter_load_ga102.bin"))
        return fprintf(stderr, "Wrong GA107 chip or firmware family\n"), 1;
    if (gu_card_find(0xffff))
        return fprintf(stderr, "Unknown device must remain unsupported\n"), 1;
    puts("RTX 2050 25ad -> GA107 177, shared GA10x recipe; existing lookup preserved");
    return 0;
}
'''

class RTX2050RecipeTest(unittest.TestCase):
    def test_exact_device_routes_to_ga107(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'test.c'
            binary = Path(directory) / 'test'
            source.write_text(SOURCE)
            subprocess.run([
                os.environ.get('CC', 'cc'), '-std=c11', '-Wall', '-Wextra',
                '-Werror', '-Wno-missing-field-initializers',
                '-Wno-unused-const-variable', '-I', str(KERNEL),
                str(source), str(KERNEL / 'recipes.c'), '-o', str(binary),
            ], check=True)
            result = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

if __name__ == '__main__':
    unittest.main()
