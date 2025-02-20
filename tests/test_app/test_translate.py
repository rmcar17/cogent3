from unittest import TestCase

import pytest
from cogent3 import DNA, make_aligned_seqs, make_unaligned_seqs
from cogent3.app.composable import NotCompleted
from cogent3.app.translate import (
    best_frame,
    get_code,
    get_fourfold_degenerate_sets,
    select_translatable,
    translate_frames,
    translate_seqs,
)


class TestTranslatable(TestCase):
    """testing translation functions"""

    def test_best_frame(self):
        """correctly identify best frame with/without allowing rc"""
        make_seq = DNA.make_seq
        seq = make_seq(seq="ATGCTAACATAAA", name="fake1")
        f = best_frame(seq)
        self.assertEqual(f, 1)
        f = best_frame(seq, require_stop=True)
        self.assertEqual(f, 1)

        # a challenging seq, translatable in 1 and 3 frames, ending on stop in
        # frame 1. Should return frame 1 irrespective of require_stop
        seq = make_seq(seq="ATGTTACGGACGATGCTGAAGTCGAAGATCCACCGCGCCACGGTGACCTGCTGA")
        f = best_frame(seq)
        self.assertEqual(f, 1)

        # a rc seq
        f = best_frame(seq)
        seq = make_seq(
            seq="AATATAAATGCCAGCTCATTACAGCATGAGAACAGCAGTTTATTACTTCATAAAGTCATA",
            name="fake2",
        )
        f = best_frame(seq, allow_rc=True)
        self.assertEqual(f, 1)
        with self.assertRaises(ValueError):
            f = best_frame(seq, allow_rc=True, require_stop=True)

        rc = seq.rc()
        f = best_frame(rc, allow_rc=True)
        self.assertEqual(f, -1)

    def test_select_translatable(self):
        """correctly get translatable seqs"""
        data = {
            "a": "AATATAAATGCCAGCTCATTACAGCATGAGAACAGCAGTTTATTACTTCATAAAGTCATA",
            "rc": "TATGACTTTATGAAGTAATAAACTGCTGTTCTCATGCTGTAATGAGCTGGCATTTATATT",
        }
        seqs = make_unaligned_seqs(data=data, moltype=DNA)
        trans = select_translatable(allow_rc=False)
        tr = trans(seqs)  # pylint: disable=not-callable
        ex = data.copy()
        ex.pop("rc")
        self.assertEqual(tr.to_dict(), ex)
        trans = select_translatable(allow_rc=True)
        tr = trans(seqs)  # pylint: disable=not-callable
        ex = data.copy()
        ex["rc"] = data["a"]
        self.assertEqual(tr.to_dict(), ex)

        # if seqs not translatable returns NotCompletedResult
        data = dict(a="TAATTGATTAA", b="GCAGTTTATTA")
        seqs = make_unaligned_seqs(data=data, moltype=DNA)
        got = select_translatable(allow_rc=False)(seqs)  # pylint: disable=not-callable
        self.assertTrue(type(got), NotCompleted)

    def test_translate_frames(self):
        """returns translated sequences"""
        seq = DNA.make_seq(seq="ATGCTGACATAAA", name="fake1")
        tr = translate_frames(seq)
        self.assertEqual(tr, ["MLT*", "C*HK", "ADI"])
        # with the bacterial nuclear and plant plastid code
        tr = translate_frames(seq, gc="Euplotid Nuclear")
        self.assertEqual(tr, ["MLT*", "CCHK", "ADI"])


class TestTranslate(TestCase):
    def test_translate_seqcoll(self):
        """correctly translate a sequence collection"""
        seqs = dict(a="ATGAGG", b="ATGTAA")
        seqs = make_unaligned_seqs(seqs, moltype="dna")
        # trim terminal stops
        translater = translate_seqs()
        aa = translater(seqs)  # pylint: disable=not-callable
        self.assertEqual(aa.to_dict(), dict(a="MR", b="M"))
        self.assertEqual(aa.moltype.label, "protein")
        # don't trim terminal stops, returns NotCompleted
        translater = translate_seqs(trim_terminal_stop=False)
        aa = translater(seqs)  # pylint: disable=not-callable
        self.assertIsInstance(aa, NotCompleted)

    def test_translate_aln(self):
        """correctly translates alignments"""
        data = dict(a="ATGAGGCCC", b="ATGTTT---")
        # an array alignment
        aln = make_aligned_seqs(data)
        translater = translate_seqs()
        aa = translater(aln)  # pylint: disable=not-callable
        self.assertEqual(aa.to_dict(), dict(a="MRP", b="MF-"))
        self.assertEqual(aa.moltype.label, "protein")
        self.assertIsInstance(aa, type(aln))
        # Alignment
        aln = aln.to_type(array_align=True)
        aa = translater(aln)  # pylint: disable=not-callable
        self.assertEqual(aa.to_dict(), dict(a="MRP", b="MF-"))
        self.assertEqual(aa.moltype.label, "protein")
        self.assertIsInstance(aa, type(aln))


class TestFourFoldDegen(TestCase):
    def test_get_fourfold_degenerate_sets(self):
        """correctly identify 4-fold degenerate codons"""
        # using straight characters
        expect = set()
        for di in "GC", "GG", "CT", "CC", "TC", "CG", "AC", "GT":
            expect.update([frozenset(di + n for n in "ACGT")])

        for i in range(1, 3):
            got = get_fourfold_degenerate_sets(get_code(i), as_indices=False)
            self.assertEqual(got, expect)

        with self.assertRaises(AssertionError):
            # as_indices requires an alphabet
            get_fourfold_degenerate_sets(get_code(1), as_indices=True)

        expect = set()
        for di in "GC", "GG", "CT", "CC", "TC", "CG", "AC", "GT":
            codons = list(
                map(
                    lambda x: tuple(DNA.alphabet.to_indices(x)),
                    [di + n for n in "ACGT"],
                )
            )
            expect.update([frozenset(codons)])

        for i in range(1, 3):
            got = get_fourfold_degenerate_sets(
                get_code(i), alphabet=DNA.alphabet, as_indices=True
            )
            self.assertEqual(got, expect)


@pytest.fixture(params=(None, 0, 1, 2))
def framed_seqs(DATA_DIR, request):
    # sample sequences with terminating stop codon
    # using valid values for frame
    data = {
        "NineBande": "GCAAGGCGCCAACAGAGCAGATGGGCTGAAAGTAAGGAAACATGTAATGATAGGCAGACTTAA",
        "Mouse": "GCAGTGAGCCAGCAGAGCAGATGGGCTGCAAGTAAAGGAACATGTAACGACAGGCAGGTTTAA",
        "Human": "GCAAGGAGCCAACATAACAGATGGGCTGGAAGTAAGGAAACATGTAATGATAGGCGGACTTAA",
        "HowlerMon": "GCAAGGAGCCAACATAACAGATGGGCTGAAAGTGAGGAAACATGTAATGATAGGCAGACTTAA",
        "DogFaced": "GCAAGGAGCCAGCAGAACAGATGGGTTGAAACTAAGGAAACATGTAATGATAGGCAGACTTAA",
    }
    prefix = "A" * (request.param or 0)
    frame = None if request.param is None else request.param + 1
    for k, s in data.items():
        data[k] = prefix + s
    return make_unaligned_seqs(data=data, moltype="dna", info={"frame": frame})


def test_select_translatable_with_frame_terminal_stop(framed_seqs):
    frame = framed_seqs.info.frame
    sl = slice(None, None) if frame is None else slice(frame - 1, None)
    expect = {s.name: str(s[sl]) for s in framed_seqs.seqs}
    app = select_translatable(frame=frame, trim_terminal_stop=False)
    got = app(framed_seqs)  # pylint: disable=not-callable
    assert got.to_dict() == expect


def test_select_translatable_with_frame_no_stop(framed_seqs):
    frame = framed_seqs.info.frame
    sl = slice(None, -3) if frame is None else slice(frame - 1, -3)
    expect = {s.name: str(s[sl]) for s in framed_seqs.seqs}
    app = select_translatable(frame=frame, trim_terminal_stop=True)
    got = app(framed_seqs)  # pylint: disable=not-callable
    assert got.to_dict() == expect


def test_select_trabnslatable_exclude_internal_stop():
    aln = make_unaligned_seqs(
        {
            "internal_stop": "AATTAAATGTGA",
            "s2": "TATGACTAA",
        }
    )
    app = select_translatable(frame=1)
    result = app(aln)  # pylint: disable=not-callable
    expect = {"s2": "TATGAC"}
    assert result.to_dict() == expect


@pytest.mark.parametrize("frame", (-1, 0, 4))
def test_select_translatable_invalid_frame(frame):
    with pytest.raises(AssertionError):
        _ = select_translatable(frame=frame)
