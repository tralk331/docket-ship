"""Run with: python -m unittest discover -s tests"""
import contextlib
import importlib.util
import io
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("docket-ship", ROOT / "docket_ship.py")
ds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ds)


def run(root, *argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = ds.main(["--root", str(root), *argv])
    return code, out.getvalue()


class ProjectTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "src").mkdir()
        (self.root / "src" / "orders.ts").write_text(
            "export const governOrder = () => 'pending_review'\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            ds.main(["--root", str(self.root), "init"])

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def write(self, rel, text):
        path = self.root / "docs" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def spec(self, body, status="active", slug="orders"):
        self.write("spec/%s.md" % slug, "---\nid: %s\ntype: spec\ntitle: Orders\nstatus: %s\n"
                   "summary: Orders.\n---\n\n%s\n" % (slug, status, body))

    def decision(self, n, status="accepted", affects="[orders]", supersedes="[]", by=""):
        self.write("decisions/D-%04d-d.md" % n,
                   "---\nid: D-%04d\ntype: decision\ntitle: Decision %d\nstatus: %s\n"
                   "date: 2026-11-12\nsummary: S.\naffects: %s\nsupersedes: %s\nsuperseded_by: %s\n"
                   "---\n\n## Context\n" % (n, n, status, affects, supersedes, by))

    def ticket(self, n, status="open", specs="[orders]"):
        self.write("work/T-%04d-t.md" % n,
                   "---\nid: T-%04d\ntype: ticket\ntitle: Ticket %d\nstatus: %s\nsummary: S.\n"
                   "specs: %s\n---\n" % (n, n, status, specs))

    def check(self):
        run(self.root, "index")
        return run(self.root, "check")

    # --- tests -------------------------------------------------------------

    def test_init_produces_a_clean_project(self):
        code, out = run(self.root, "check")
        self.assertEqual(code, 0, out)
        self.assertIn("0 errors, 0 warnings", out)
        self.assertIn("code: [src]", (self.root / "docket-ship.cfg").read_text(encoding="utf-8"))

    def test_consistent_docs_pass(self):
        self.spec("Orders are governed by `governOrder`. [D-0001]")
        self.decision(1)
        self.ticket(1)
        code, out = self.check()
        self.assertEqual(code, 0, out)
        self.assertIn("0 errors, 0 warnings", out)

    def test_header_problems_are_errors(self):
        self.write("spec/orders.md", "---\nid: orders\ntype: spec\nthis is not a header\n---\n")
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("cannot parse header line", out)
        self.assertIn("missing required header 'title'", out)

    def test_spec_citing_superseded_decision_is_an_error(self):
        self.spec("Payments are taken up front. [D-0001]")
        self.decision(1, status="superseded", by="D-0002")
        self.decision(2, supersedes="[D-0001]")
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("cites superseded D-0001 (superseded by D-0002)", out)
        self.assertIn("D-0002 affects this spec but is not cited in it", out)

    def test_supersede_command_links_both_sides_and_lists_stale_paragraphs(self):
        self.spec("Payments are taken up front. [D-0001]")
        self.decision(1)
        self.decision(2, status="accepted")
        run(self.root, "index")
        code, out = run(self.root, "supersede", "D-0001", "D-0002")
        self.assertEqual(code, 0, out)
        self.assertIn("docs/spec/orders.md:9: Payments are taken up front. [D-0001]", out)
        old = (self.root / "docs/decisions/D-0001-d.md").read_text(encoding="utf-8")
        new = (self.root / "docs/decisions/D-0002-d.md").read_text(encoding="utf-8")
        self.assertIn("status: superseded", old)
        self.assertIn("superseded_by: D-0002", old)
        self.assertIn("supersedes: [D-0001]", new)
        code, out = run(self.root, "check")
        self.assertIn("cites superseded D-0001", out)  # the spec still needs its update

    def test_accepted_decision_with_unmarked_predecessor(self):
        self.spec("[D-0002]")
        self.decision(1, affects="[]")
        self.decision(2, supersedes="[D-0001]")
        code, out = self.check()
        self.assertIn("run: docket-ship supersede D-0001 D-0002", out)

    def test_missing_symbol_is_flagged(self):
        # The taskwyre case: a spec naming a field that no longer exists.
        self.spec("The card shows `sellerTier`, set by `governOrder`. [D-0001]")
        self.decision(1)
        code, out = self.check()
        self.assertEqual(code, 0, out)  # warnings only
        self.assertIn("names sellerTier, which is not found in the code", out)
        self.assertNotIn("governOrder", out)

    def test_missing_symbol_mentions_open_tickets(self):
        self.spec("Refunds use `refundOrder`. [D-0001]")
        self.decision(1)
        self.ticket(1)
        _, out = self.check()
        self.assertIn("may describe planned work", out)

    def test_missing_path_is_flagged(self):
        self.spec("See `src/orders.ts` and `src/gone.ts`. [D-0001]")
        self.decision(1)
        _, out = self.check()
        self.assertIn("names path src/gone.ts", out)
        self.assertNotIn("src/orders.ts,", out)

    def test_history_phrases_warn_unless_ignored(self):
        self.spec("Orders are not built yet. [D-0001]\n"
                  "Refunds are not built yet. <!-- docket-ship:ignore -->")
        self.decision(1)
        _, out = self.check()
        self.assertEqual(out.count("reads as status or history"), 1)

    def test_fenced_code_is_skipped(self):
        self.spec("[D-0001]\n\n```\nnot yet D-9999 `missingThing`\n```")
        self.decision(1)
        code, out = self.check()
        self.assertEqual(code, 0, out)
        self.assertIn("0 warnings", out)

    def test_dangling_references(self):
        self.spec("See [missing](./nope.md) and D-0042.")
        self.ticket(1, specs="[payments]")
        _, out = self.check()
        self.assertIn("broken link: ./nope.md", out)
        self.assertIn("cites D-0042, which does not exist", out)
        self.assertIn("'specs' lists payments, which is not a known spec", out)

    def test_backticked_ids_are_examples_not_citations(self):
        self.spec("[D-0001] In another project this would be `D-0042`.")
        self.decision(1)
        code, out = self.check()
        self.assertEqual(code, 0, out)

    def test_from_finds_the_project_and_fix_rewrites_the_index(self):
        self.spec("Text.")  # the index is now stale
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ds.main(["--from", str(self.root / "docs/spec/orders.md"), "check", "--fix"])
        self.assertEqual(code, 0, out.getvalue())
        self.assertIn("0 errors", out.getvalue())

    def test_outside_a_project_exits_3(self):
        empty = Path(tempfile.mkdtemp())
        try:
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                code = ds.main(["--from", str(empty), "check"])
            self.assertEqual(code, 3)
            self.assertIn("no docket-ship.cfg", err.getvalue())
        finally:
            shutil.rmtree(empty, ignore_errors=True)

    def test_stale_index_is_an_error(self):
        self.spec("Text.")
        code, out = run(self.root, "check")
        self.assertEqual(code, 1)
        self.assertIn("INDEX.md:1: error: out of date", out)

    def test_conventions_drift_warns(self):
        (self.root / "docs/CONVENTIONS.md").write_text("edited", encoding="utf-8")
        _, out = run(self.root, "check")
        self.assertIn("differs from this docket-ship's version", out)

    def test_new_assigns_sequential_ids(self):
        run(self.root, "new", "decision", "First choice")
        run(self.root, "new", "decision", "Second choice", "--affects", "orders")
        names = sorted(p.name for p in (self.root / "docs/decisions").glob("*.md"))
        self.assertEqual(names, ["D-0001-first-choice.md", "D-0002-second-choice.md"])
        text = (self.root / "docs/decisions/D-0002-second-choice.md").read_text(encoding="utf-8")
        self.assertIn("affects: [orders]", text)
        self.assertIn("status: proposed", text)

    def test_index_lists_open_tickets_per_spec(self):
        self.spec("[D-0001]")
        self.decision(1)
        self.ticket(1)
        self.ticket(2, status="done")
        run(self.root, "index")
        index = (self.root / "docs/INDEX.md").read_text(encoding="utf-8")
        self.assertIn("· open: T-0001", index)
        self.assertNotIn("T-0002-t.md", index)
        self.assertIn("1 closed", index)

    def test_refs_finds_header_and_body_references(self):
        self.spec("Uses [D-0001].")
        self.decision(1)
        self.ticket(1)
        self.write("work/T-0002-x.md", "---\nid: T-0002\ntype: ticket\ntitle: X\nstatus: open\n"
                   "summary: S.\ndecisions: [D-0001]\n---\n")
        _, out = run(self.root, "refs", "D-0001")
        self.assertIn("docs/spec/orders.md:9: Uses [D-0001].", out)
        self.assertIn("docs/work/T-0002-x.md:1: decisions: D-0001", out)


class ParserTest(unittest.TestCase):
    def test_values(self):
        self.assertEqual(ds.parse_value("[a, b ,c]"), ["a", "b", "c"])
        self.assertEqual(ds.parse_value("[]"), [])
        self.assertEqual(ds.parse_value("draft   # comment"), "draft")
        self.assertEqual(ds.parse_value('"a: b # c"'), "a: b # c")

    def test_slugify_breaks_at_words(self):
        slug = ds.slugify("Specs describe the accepted design; build status lives in tickets")
        self.assertEqual(slug, "specs-describe-the-accepted-design-build-status")

    def test_distinctive_names(self):
        for name in ("sellerTier", "GigForm", "SELLER_TRANSITIONS", "pending_review"):
            self.assertTrue(ds.is_distinctive(name), name)
        for name in ("draft", "Gig", "id", "JSON"):
            self.assertFalse(ds.is_distinctive(name), name)


if __name__ == "__main__":
    unittest.main()
