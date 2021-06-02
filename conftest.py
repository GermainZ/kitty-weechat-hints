import glob
from os.path import splitext


def pytest_generate_tests(metafunc):
    if (
        "input_text" in metafunc.fixturenames
        and "expected_urls" in metafunc.fixturenames
    ):
        inputs = []
        ids = []
        for path in glob.glob("tests/*.test"):
            with open(path) as input_file:
                input_text = input_file.read()
            base = splitext(path)[0]
            with open(f"{base}.result") as expected_file:
                expected_urls = expected_file.read().splitlines()
            inputs.append((input_text, expected_urls))
            ids.append(base)
        metafunc.parametrize(("input_text", "expected_urls"), inputs, ids=ids)
