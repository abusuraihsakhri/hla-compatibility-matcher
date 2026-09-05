"""
Automated Pytest for hla-compatibility-matcher Core HLA Matcher Module.
"""
import sys
from pathlib import Path
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import hla_matcher as m


class TestLookup:
    """Tests for the lookup() function."""

    def test_lookup_returns_expected_keys(self):
        result = m.lookup("A*02:01")
        assert "query" in result
        assert "top_hit" in result
        assert "score" in result
        assert "all" in result

    def test_lookup_hla_allele(self):
        result = m.lookup("A02")
        assert result["top_hit"] == "A*02:01"
        assert result["score"] >= 10

    def test_lookup_drb1_allele(self):
        result = m.lookup("DRB115")
        assert result["top_hit"] == "DRB1*15:01"
        assert result["score"] >= 10

    def test_lookup_no_match(self):
        result = m.lookup("zzzznonexistent")
        assert result["top_hit"] == "no match"
        assert result["score"] == 0

    def test_lookup_empty_string(self):
        result = m.lookup("")
        assert "top_hit" in result
        assert "score" in result

    def test_lookup_case_insensitive(self):
        result_lower = m.lookup("a02")
        result_upper = m.lookup("A02")
        assert result_lower["top_hit"] == result_upper["top_hit"]

    def test_lookup_returns_top_3(self):
        result = m.lookup("A")
        assert len(result["all"]) <= 3


class TestProcessCsv:
    """Tests for the process_csv() function."""

    def test_process_csv_basic(self, tmp_path):
        input_csv = tmp_path / "input.csv"
        input_csv.write_text("hla\nA*02:01\nB*07:02\n")
        output_csv = tmp_path / "output.csv"

        results = m.process_csv(str(input_csv), str(output_csv))

        assert len(results) == 2
        assert results[0]["top_hit"] == "A*02:01"
        assert results[1]["top_hit"] == "B*07:02"
        assert output_csv.exists()

    def test_process_csv_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            m.process_csv("nonexistent_file.csv", "output.csv")

    def test_process_csv_empty_file(self, tmp_path):
        input_csv = tmp_path / "empty.csv"
        input_csv.write_text("hla\n")
        output_csv = tmp_path / "output.csv"

        results = m.process_csv(str(input_csv), str(output_csv))
        assert len(results) == 0

    def test_process_csv_no_headers(self, tmp_path):
        input_csv = tmp_path / "noheaders.csv"
        input_csv.write_text("")
        output_csv = tmp_path / "output.csv"

        with pytest.raises(ValueError, match="no headers"):
            m.process_csv(str(input_csv), str(output_csv))


class TestBuildParser:
    """Tests for the build_parser() function."""

    def test_parser_single_command(self):
        parser = m.build_parser()
        args = parser.parse_args(["single", "A*02:01"])
        assert args.cmd == "single"
        assert args.query == "A*02:01"

    def test_parser_batch_command(self):
        parser = m.build_parser()
        args = parser.parse_args(["batch", "--input", "in.csv", "--output", "out.csv"])
        assert args.cmd == "batch"
        assert args.input == "in.csv"
        assert args.output == "out.csv"


class TestMain:
    """Tests for the main() function."""

    def test_main_single(self, capsys):
        result = m.main(["single", "A*02:01"])
        assert result == 0
        captured = capsys.readouterr()
        assert "A*02:01" in captured.out

    def test_main_batch(self, tmp_path):
        input_csv = tmp_path / "input.csv"
        input_csv.write_text("hla\nA*02:01\n")
        output_csv = tmp_path / "output.csv"

        result = m.main(["batch", "--input", str(input_csv), "--output", str(output_csv)])
        assert result == 0
        assert output_csv.exists()
