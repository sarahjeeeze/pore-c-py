import shutil
from collections import Counter
from pathlib import Path

import pysam
import pytest
from typer.testing import CliRunner

from pore_c2.cli import (
    app,
    create_test_data,
    digest_concatemers,
    process_monomer_alignments,
)
from pore_c2.testing import Scenario
from pore_c2.utils import pysam_verbosity


@pytest.mark.parametrize("command", ["index", "align", "merge"])
def test_help(runner: CliRunner, command: str):
    result = runner.invoke(app, [command, "--help"])
    # print(result.stdout)
    assert result.exit_code == 0


def test_index_cli(runner, scenario: Scenario, tmp_path):
    prefix = Path(tmp_path / "test_digest")
    result = runner.invoke(
        app,
        [
            "index",
            str(scenario.reference_fasta),
            str(scenario.enzyme),
            "--prefix",
            str(prefix),
        ],
    )
    assert result.exit_code == 0


@pytest.mark.parametrize("suffix", [".bam", ".fastq"])
def test_digest_concatemers(default_scenario: Scenario, tmp_path, suffix):
    output_file = tmp_path / f"read_fragments{suffix}"
    digest_concatemers(
        default_scenario.concatemer_fastq,
        default_scenario.enzyme,
        output_file,
    )
    expected = dict(
        default_scenario.concatemer_metadata.select(
            ["concatemer_id", "num_segments"]
        ).rows()
    )
    observed = Counter()
    if suffix == ".fastq":
        for rec in pysam.FastxFile(output_file):
            tags = {_.split(":", 1)[0]: _ for _ in rec.comment.split("\t")}
            concatemer_id = tags["MI"].split(":")[-1]
            observed[concatemer_id] += 1
    elif suffix == ".bam":
        with pysam_verbosity(0):
            af = pysam.AlignmentFile(output_file, check_sq=False)
        for rec in af:
            concatemer_id = rec.get_tag("MI")
            observed[concatemer_id] += 1
    assert len(observed) == len(expected)


def test_create_test_data(tmp_path):
    scenario: Scenario = create_test_data(tmp_path, seed=421)
    existing_files = scenario.fc.existing()
    for k in ["reference_fasta", "concatemer_fastq"]:
        assert existing_files[k].exists() is True


@pytest.mark.skipif(shutil.which("minimap2") is None, reason="minimap2 is not in path")
def test_process_monomer_alignments(name_sorted_bam, tmp_path):
    prefix = tmp_path / "processed"
    monomer_bam = tmp_path / "processed.ns.bam"
    pe_bam = tmp_path / "processed.pe.bam"
    writer = process_monomer_alignments(name_sorted_bam, prefix, paired_end=True)

    writer.close()
    monomer_bam.exists()

    with pysam_verbosity(0):
        input_aligns = len([a for a in pysam.AlignmentFile(str(name_sorted_bam))])

    with pysam_verbosity(0):
        num_aligns = len([a for a in pysam.AlignmentFile(str(monomer_bam))])
    assert num_aligns == sum(writer.ns_writer.counter.values())
    assert num_aligns == input_aligns

    with pysam_verbosity(0):
        num_aligns = len([a for a in pysam.AlignmentFile(str(pe_bam))])
    assert num_aligns == sum(writer.pe_writer.counter.values())
    assert writer.pe_writer.counter["primary"] > 0


# TODO: this might be redundant
def test_digest_cli(runner, scenario: Scenario, tmp_path):
    output_fastq = Path(tmp_path / "monomers.fastq")
    result = runner.invoke(
        app,
        [
            "utils",
            "digest-concatemers",
            str(scenario.concatemer_fastq),
            str(scenario.enzyme),
            str(output_fastq),
        ],
    )
    assert result.exit_code == 0
