
import pytest
from imoveis_web_multi import extract_matricula_number

@pytest.mark.parametrize("input_text, expected", [
    ("MATRÍCULA Nº 5000", "5000"),
    ("Referente a matrícula n° 12345 do cartório", "12345"),
    ("MATRICULA 999", "999"),
    ("Texto sem número relevante", ""),
    ("CNM: 120456.2.0012345-88", "12345"), # Test CNM extraction logic if present
])
def test_extract_matricula_number(input_text, expected):
    result = extract_matricula_number(input_text)
    assert result == expected
