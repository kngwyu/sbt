import nox

SOURCES = ["src/sbtcher", "tests"]


@nox.session(reuse_venv=True)
def lint(session: nox.Session) -> None:
    session.install("-r", "requirements/lint.txt")
    session.run("flake8", *SOURCES)
    session.run("black", *SOURCES)
    session.run("isort", *SOURCES)


@nox.session(reuse_venv=True, python=["3.7", "3.8", "3.9", "3.10"])
def tests(session: nox.Session) -> None:
    session.install("pytest")
    session.install("-e", ".")
    session.run("pytest", "tests", *session.posargs)
