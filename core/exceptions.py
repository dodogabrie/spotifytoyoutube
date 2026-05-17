class TransferError(Exception):
    """Base class for all transfer-related errors."""


class AuthError(TransferError):
    pass


class SpotifyError(TransferError):
    pass


class YTMusicError(TransferError):
    pass


class MatchError(TransferError):
    pass


class TransferAborted(TransferError):
    pass
