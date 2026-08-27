"""One retry policy, one user agent, one error format — over two deliberate transports.

~keep The transports are NOT an accident to be cleaned up. Keep both.

curl is the path consumers actually take. Fixtures are materialised in CI by
xberg-io/actions/fetch-test-documents, whose scripts/fetch.sh downloads with curl. verify_corpus
exists to prove the bucket still serves that path, so if it fetched with urllib instead, CI would
stay green while asserting something about a TLS stack, proxy handling and redirect policy that no
consumer uses. fetch_corpus is the local counterpart of that same action and matches it for the
same reason.

urllib is right for the provenance fetchers. They pull from eleven third-party hosts, where real
exception types are worth having, no `curl` binary is required on a contributor's machine, and
1,483 requests do not each pay for a subprocess.

What WAS accidental is everything around them: five call sites, two of which retried three times
with no delay at all, two of which did not retry, and five unexplained timeouts. That is what this
module unifies.
"""

import subprocess
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

USER_AGENT = "xberg-test-documents"

# ~keep Each timeout is the wall clock ONE transfer is allowed, and each number comes from the
# largest object that source actually serves rather than from taste.
BUCKET_OBJECT_TIMEOUT_SECONDS = 120
"""storage.googleapis.com. Largest pinned object is 62.1 MiB, so this is a ~0.5 MiB/s floor."""

BUCKET_HEAD_TIMEOUT_SECONDS = 60
"""The same host with no response body. Bounds a whole 64-URL batch on one reused connection."""

SHARD_TIMEOUT_SECONDS = 300
"""The one URL that needs it: the govdocs1 zip, from which 267 regression members are taken.

~keep Every other regression entry is a direct file. This value exists for a single request that
pulls a whole multi-hundred-MB archive, which is why it is five times the others and why raising
the rest to match would be cargo-culting.
"""

SOURCE_FILE_TIMEOUT_SECONDS = 120
"""Third-party single files (gutenberg, arxiv, ebi.ac.uk, zenodo, archive.org, ctan, nasa, w3c).

Largest observed is 56.8 MiB, so this is the same ~0.5 MiB/s floor as the bucket.
"""


class HttpError(RuntimeError):
    """A transfer that failed every attempt, carrying the last reason."""

    def __init__(self, url: str, reason: str) -> None:
        super().__init__(f"{url}: {reason}")
        self.url = url
        self.reason = reason


class CredentialError(HttpError):
    """No usable credential. Deliberately NOT retryable.

    ~keep A missing or expired ADC login fails identically on every attempt, so retrying it turns
    one clear error into three subprocesses and three seconds of backoff PER OBJECT — thousands of
    gcloud invocations before the run finally prints the same message it could have printed at the
    start. get() re-raises this instead of counting it as a transient failure.
    """


@dataclass(frozen=True)
class RetryPolicy:
    """~keep The backoff is the point.

    Before this, three call sites ran `for _ in range(3)` with no sleep, so all three attempts
    left within milliseconds of each other — which is not a retry policy, it is the same request
    sent three times into the same transient failure. The other two call sites did not retry at
    all, and they are the ones CI depends on.
    """

    attempts: int = 3
    first_backoff_seconds: float = 1.0
    backoff_factor: float = 2.0

    def delay_before(self, attempt: int) -> float:
        """Seconds to wait before `attempt` (1-based). Zero before the first."""
        if attempt <= 1:
            return 0.0
        return self.first_backoff_seconds * (self.backoff_factor ** (attempt - 2))


DEFAULT_RETRY = RetryPolicy()


# ~keep Access tokens from a workload-identity federation exchange last one hour and cannot be
# extended without an org policy change. The full private corpus is 15.26 GB, which on a slow
# runner can outlive a single token, so a credential minted once at startup would turn into a 401
# somewhere in the middle of a long fetch. Acquiring per batch instead keeps a long transfer
# working and costs one subprocess per batch, which is noise next to the bytes being moved.
ACCESS_TOKEN_MAX_AGE_SECONDS = 30 * 60


class AdcCredential:
    """An Application Default Credentials bearer token, refreshed as it ages.

    ~keep Deliberately shells out to `gcloud auth application-default print-access-token` rather than importing
    google.auth. This package is stdlib-only because consumers run it on a bare checkout with
    nothing installed, and the CI path (google-github-actions/auth with WIF) populates ADC exactly
    the same way a local `gcloud auth application-default login` does — so one code path serves both.
    """

    def __init__(
        self,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._run = runner
        self._clock = clock
        self._token: str | None = None
        self._failure: CredentialError | None = None
        self._acquired_at = 0.0
        # ~keep token() is called from every worker thread. Without this the first batch of --jobs
        # threads all miss the cache at once and stampede gcloud with N identical subprocesses.
        self._lock = threading.Lock()

    def token(self) -> str:
        with self._lock:
            if self._failure is not None:
                raise self._failure
            if self._token is None or self._clock() - self._acquired_at >= ACCESS_TOKEN_MAX_AGE_SECONDS:
                try:
                    self._token = self._acquire()
                except CredentialError as error:
                    self._failure = error
                    raise
                # ~keep Stamped AFTER acquiring, not before: gcloud can take a second or two, and
                # dating the token from before that shortens its usable life by exactly that much.
                self._acquired_at = self._clock()
            return self._token

    def _acquire(self) -> str:
        result = self._run(
            ["gcloud", "auth", "application-default", "print-access-token"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise CredentialError(
                "gcloud auth application-default print-access-token",
                "could not obtain an access token. Run `gcloud auth application-default login`, or "
                f"check the workload-identity setup in CI: {result.stderr.strip()}",
            )
        token = result.stdout.strip()
        if not token or '"' in token or any(character.isspace() for character in token):
            raise CredentialError(
                "gcloud auth application-default print-access-token",
                "gcloud returned an invalid access token",
            )
        return token

    def curl_config(self) -> str:
        """Return an stdin-only curl config so the bearer token never enters process arguments."""
        return f'header = "Authorization: Bearer {self.token()}"\n'


@dataclass(frozen=True)
class HeadResult:
    url: str
    status: int | None
    content_length: int | None


class Transport(Protocol):
    def fetch(self, url: str, *, timeout: float) -> bytes: ...


class UrllibTransport:
    """Anonymous HTTPS through the stdlib. Used by the provenance fetchers."""

    def fetch(self, url: str, *, timeout: float) -> bytes:
        # ~keep S310 is about attacker-controlled schemes. Every URL here comes from a manifest
        # committed to this repo, and every response is verified against a pinned sha256 before it
        # is written, so a substituted body is caught even if a scheme were somehow smuggled in.
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            data: bytes = response.read()
            return data


class CurlTransport:
    """Anonymous HTTPS through curl, matching what the CI action does.

    ~keep `runner` is an injected seam, not a patched global: it keeps the transport testable with
    a plain value, works under bare `python3 -m unittest`, and cannot leak between tests.
    """

    def __init__(
        self,
        runner: Callable[..., subprocess.CompletedProcess[Any]] = subprocess.run,
        credential: "AdcCredential | None" = None,
    ) -> None:
        self._run = runner
        # ~keep None means anonymous, which stays the default: the public bucket is served without
        # credentials and that is the path this repo's CI proves still works.
        self._credential = credential

    def _auth_config(self, *, text: bool) -> tuple[list[str], str | bytes | None]:
        if self._credential is None:
            return [], None
        config = self._credential.curl_config()
        return ["--config", "-"], config if text else config.encode()

    def fetch(self, url: str, *, timeout: float) -> bytes:
        auth_args, auth_input = self._auth_config(text=False)
        result = self._run(
            ["curl", "-sS", "--fail", "--max-time", str(int(timeout)), *auth_args, url],
            capture_output=True,
            input=auth_input,
            check=False,
        )
        if result.returncode != 0:
            raise HttpError(url, f"download failed: {result.stderr.decode().strip()}")
        payload: bytes = result.stdout
        return payload

    def head_many(self, urls: Sequence[str], *, timeout: float) -> list[HeadResult]:
        """HEAD a batch of URLs in one curl invocation.

        ~keep Batching is deliberately NOT on the Transport protocol. urllib cannot do it, and
        pretending otherwise would be a fake abstraction. One curl process per batch rather than
        per object because process startup dominates a HEAD request, and curl reuses the
        connection across URLs given in a single invocation.
        """
        auth_args, auth_input = self._auth_config(text=True)
        command = ["curl", "-sS", "--head", "--max-time", str(int(timeout)), *auth_args]
        command += ["-w", "%{http_code} %header{content-length} %{url_effective}\n"]
        for url in urls:
            # ~keep -o must repeat per URL; curl applies a single -o to the first transfer only and
            # dumps every later response to stdout, which corrupts the write-out lines we parse.
            command += ["-o", "/dev/null", url]

        result = self._run(command, capture_output=True, input=auth_input, text=True, check=False)
        if result.returncode != 0:
            raise HttpError(f"a batch of {len(urls)}", f"curl failed: {result.stderr.strip()}")

        seen: dict[str, HeadResult] = {}
        for line in result.stdout.splitlines():
            fields = line.split()
            if len(fields) != 3:
                continue
            status, content_length, url = fields
            seen[url] = HeadResult(
                url=url,
                status=int(status) if status.isdigit() else None,
                content_length=int(content_length) if content_length.isdigit() else None,
            )
        return [seen.get(url, HeadResult(url=url, status=None, content_length=None)) for url in urls]


def get(
    url: str,
    *,
    timeout: float,
    transport: Transport,
    retry: RetryPolicy = DEFAULT_RETRY,
    sleep: Callable[[float], None] = time.sleep,
) -> bytes:
    """Fetch `url`, retrying transport failures with backoff.

    Raises HttpError carrying the LAST reason. `sleep` is injectable so tests can assert the
    backoff schedule without spending it.
    """
    last_reason = ""
    for attempt in range(1, retry.attempts + 1):
        delay = retry.delay_before(attempt)
        if delay:
            sleep(delay)
        try:
            return transport.fetch(url, timeout=timeout)
        except CredentialError:
            # ~keep Fails identically every time; retrying multiplies one message by attempts x objects.
            raise
        except Exception as error:  # noqa: BLE001 - a transport can fail in any way; that is what retrying is for
            last_reason = error.reason if isinstance(error, HttpError) else f"{type(error).__name__}: {error}"
    raise HttpError(url, last_reason)
