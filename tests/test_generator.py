"""Quick smoke test for the generator."""

from pathlib import Path
import tempfile
import shutil

from codegen.config import FeatureConfig
from codegen.generator import generate_files


def test_dry_run():
    cfg = FeatureConfig(feature_name="TestFeature")
    with tempfile.TemporaryDirectory() as tmpdir:
        results = generate_files(cfg, tmpdir, dry_run=True)
        assert len(results) > 0
        assert all("WOULD CREATE" in r for r in results)
        print(f"Dry run produced {len(results)} entries - OK")


def test_generate():
    cfg = FeatureConfig(feature_name="TestFeature")
    with tempfile.TemporaryDirectory() as tmpdir:
        results = generate_files(cfg, tmpdir, dry_run=False)
        created = [r for r in results if r.startswith("CREATED")]
        skipped = [r for r in results if "SKIPPED" in r]
        print(f"Created: {len(created)}, Skipped: {len(skipped)}")
        # Verify at least the key files exist
        expected = [
            "TMT.MyERP6.Domain.Shared/Models/TestFeature.cs",
            "TMT.MyErp6.Application/Features/TestFeatures/Services/TestFeatureQueryService.cs",
            "TMT.MyERP6.HttpApi.Public.Host/PublicControllers/TestFeatureController.cs",
        ]
        for e in expected:
            assert (Path(tmpdir) / e).exists(), f"Missing: {e}"
        print("All expected files exist - OK")


def test_idempotent():
    cfg = FeatureConfig(feature_name="TestFeature")
    with tempfile.TemporaryDirectory() as tmpdir:
        r1 = generate_files(cfg, tmpdir, dry_run=False)
        r2 = generate_files(cfg, tmpdir, dry_run=False)
        created_first = [r for r in r1 if r.startswith("CREATED")]
        skipped_second = [r for r in r2 if "SKIPPED" in r]
        assert len(created_first) == len(skipped_second)
        print(f"Idempotent: {len(created_first)} created first, {len(skipped_second)} skipped second - OK")


if __name__ == "__main__":
    test_dry_run()
    test_generate()
    test_idempotent()
    print("\nAll tests passed.")
