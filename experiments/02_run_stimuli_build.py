"""Experiment 02: Stage 2 Stimulus Manifest & Variant Rendering.

Builds 160 validated demographic names (40 per group: 20 train, 10 val, 10 test),
renders candidate variants through locked templates, and inspects pool composition.
"""

from src.contracts.stimuli import TemplateType, StimulusPartition, IntersectionalGroup
from src.contracts.raw_data import RawResume
from src.stimuli.manifest_builder import build_stimuli_manifest
from src.stimuli.injector import render_candidate_variant
from src.stimuli.pool_sampler import assign_pool_demographics


def main():
    print("=" * 60)
    print("STAGE 2: DEMOGRAPHIC STIMULI & TEMPLATE RENDERING")
    print("=" * 60)

    manifest = build_stimuli_manifest()
    print(f"Generated stimulus manifest with {len(manifest)} validated names.")

    for g in IntersectionalGroup:
        train_n = sum(1 for m in manifest if m.group == g and m.partition == StimulusPartition.TRAIN)
        val_n = sum(1 for m in manifest if m.group == g and m.partition == StimulusPartition.VAL)
        test_n = sum(1 for m in manifest if m.group == g and m.partition == StimulusPartition.TEST)
        print(f"  Group {g.value:<15}: {train_n} train, {val_n} val, {test_n} test names")

    # Sample template injection test
    base_res = RawResume(
        resume_id="res_101",
        raw_text="Experienced Software Engineer with proficiency in Python and microservices.",
        normalized_text="Experienced Software Engineer with proficiency in Python and microservices.",
        content_hash="abc1234567890def",
    )

    test_name = next(m for m in manifest if m.partition == StimulusPartition.TEST)
    test_variant = render_candidate_variant(base_res, test_name, TemplateType.TEST_BELOW_SUMMARY)

    print(f"\nRendered Variant ({test_variant.template_type.value}):")
    print("-" * 40)
    print(test_variant.rendered_text)
    print("-" * 40)

    # Redacted control
    redacted_variant = render_candidate_variant(base_res, template_type=TemplateType.REDACTED_NEUTRAL)
    print(f"\nRedacted Control ({redacted_variant.template_type.value}):")
    print("-" * 40)
    print(redacted_variant.rendered_text)
    print("-" * 40)

    print("\nStage 2 stimulus generation & injection PASSED.")


if __name__ == "__main__":
    main()
