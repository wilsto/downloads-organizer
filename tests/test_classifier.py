from organizer.classifier import RegexClassifier, Classification
from organizer.config import ContextConfig


CONTEXTS = {
    "Pro": ContextConfig(
        patterns=["(?i)(powerbi|bisolution|facture|devis)", "(?i)\\.(pptx|xlsx)$"],
        subfolders=["Documents", "Presentations", "Spreadsheets"],
    ),
    "Perso": ContextConfig(
        patterns=["(?i)(photo|img_|carte|passeport|assurance)"],
        subfolders=["Documents", "Images", "Admin"],
    ),
    "Tech": ContextConfig(
        patterns=["(?i)(github|docker|homeassistant|ha-|\\.py$|\\.js$)"],
        subfolders=["Code", "Config", "HomeLab"],
    ),
}

TYPE_MAPPING = {
    "Documents": ["pdf", "docx", "txt"],
    "Images": ["png", "jpg", "webp"],
    "Presentations": ["pptx"],
    "Spreadsheets": ["xlsx", "csv"],
    "Executables": ["exe", "msi"],
    "Archives": ["zip", "rar"],
    "Code": ["py", "js"],
}


def make_classifier() -> RegexClassifier:
    return RegexClassifier(
        contexts=CONTEXTS,
        type_mapping=TYPE_MAPPING,
        default_context="Perso",
        default_type="Autres",
    )


def test_classify_pro_by_keyword():
    c = make_classifier()
    result = c.classify("facture_2025.pdf")
    assert result.context == "Pro"
    assert result.file_type == "Documents"


def test_classify_pro_by_extension():
    c = make_classifier()
    result = c.classify("rapport.pptx")
    assert result.context == "Pro"
    assert result.file_type == "Presentations"


def test_classify_perso():
    c = make_classifier()
    result = c.classify("passeport_scan.pdf")
    assert result.context == "Perso"


def test_classify_tech():
    c = make_classifier()
    result = c.classify("docker-compose.yml.py")
    assert result.context == "Tech"


def test_classify_default_context():
    c = make_classifier()
    result = c.classify("random_file.pdf")
    assert result.context == "Perso"  # default
    assert result.file_type == "Documents"


def test_classify_unknown_extension():
    c = make_classifier()
    result = c.classify("mystery.xyz")
    assert result.file_type == "Autres"


def test_classify_exe():
    c = make_classifier()
    result = c.classify("installer.exe")
    assert result.file_type == "Executables"


def test_classify_case_insensitive():
    c = make_classifier()
    result = c.classify("FACTURE_SERVIER.PDF")
    assert result.context == "Pro"
    assert result.file_type == "Documents"


def test_classification_has_matched_by():
    c = make_classifier()
    result = c.classify("facture.pdf")
    assert isinstance(result, Classification)
    assert result.matched_by == "regex"

    result2 = c.classify("unknown.xyz")
    assert result2.matched_by == "default"
