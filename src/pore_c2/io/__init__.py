from pathlib import Path
from typing import TYPE_CHECKING, Iterable, List, Optional

from pysam import AlignmentFile, AlignmentHeader, FastaFile

from ..log import get_logger
from ..settings import DEFAULT_ALIGN_HEADER
from .aligns import get_aligns
from .reads import ReadIter, ReadWriter, get_reads, get_writer

__all__ = [
    "get_alignment_header",
    "ReadWriter",
    "ReadIter",
    "get_reads",
    "get_writer",
    "get_aligns",
]

logger = get_logger()

if TYPE_CHECKING:
    pass


def find_files(
    root: Path, glob: str = "*.fastq", recursive: bool = True
) -> Iterable[Path]:

    if not root.is_dir():
        yield root
    else:
        if recursive and not glob.startswith("**/"):
            glob = f"**/{glob}"
        for f in root.glob(glob):
            yield (f)


def get_alignment_header(
    *, source_files: Optional[List[Path]] = None, reference_fasta: Optional[Path] = None
) -> AlignmentHeader:
    # TODO: add tests for this
    data = {}
    if source_files:
        bams = [f for f in source_files if f.suffix in (".bam", ".sam", ".cram")]
        if len(bams) == 1:
            source_header = AlignmentFile(str(bams[0]), check_sq=False).header
            data = {**data, **source_header.to_dict()}
        elif len(bams) > 1:
            raise NotImplementedError(f"Too many bams {bams}")
        else:
            pass
    if reference_fasta:
        ff = FastaFile(str(reference_fasta))
        header = AlignmentHeader.from_references(list(ff.references), list(ff.lengths))
        data = {**data, **header.to_dict()}

    if not data:
        header = DEFAULT_ALIGN_HEADER
    else:
        header = AlignmentHeader.from_dict(data)
    return header
