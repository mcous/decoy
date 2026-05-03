import warnings

from ...warnings import DecoyWarning
from .values import CallSite


def warn(warning: DecoyWarning, site: CallSite | None = None) -> None:
    """Issue a warning, pointing at the captured call site if available."""
    if site is not None:
        warnings.warn_explicit(
            warning,
            category=None,
            filename=site.filename,
            lineno=site.lineno,
            module=site.module,
        )
    else:
        warnings.warn(warning, stacklevel=4)
