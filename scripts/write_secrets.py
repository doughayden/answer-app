import argparse
import json
import secrets
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Self


DEFAULT_OUTPUT_PATH = Path(".streamlit/secrets/secrets.toml")
COOKIE_SECRET_LENGTH = 42
SECRETS_TOML_TEMPLATE = """[auth]
redirect_uri = "{redirect_uri}"
cookie_secret = "{cookie_secret}"

[auth.google]
client_id = "{client_id}"
client_secret = "{client_secret}"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
client_kwargs = {{ "access_type" = "online", "prompt" = "select_account" }}
"""


@dataclass
class WebConfig:
    """Data class for the 'web' section of OAuth client secrets."""

    client_id: str
    client_secret: str
    redirect_uris: List[str]

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Create a WebConfig instance from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError("Web config must be a dictionary")

        required_fields = ["client_id", "client_secret", "redirect_uris"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        if not isinstance(data["redirect_uris"], list):
            raise ValueError("redirect_uris must be a list")

        return cls(
            client_id=data["client_id"],
            client_secret=data["client_secret"],
            redirect_uris=data["redirect_uris"],
        )


@dataclass
class OAuthClientSecrets:
    """Data class for OAuth client secrets JSON structure."""

    web: WebConfig

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Create an OAuthClientSecrets instance from a dictionary."""
        if not isinstance(data, dict) or "web" not in data:
            raise ValueError(
                "Invalid OAuth client secrets format: missing 'web' section"
            )

        return cls(web=WebConfig.from_dict(data["web"]))


@dataclass
class SecretsTomlData:
    """Data class for the data needed to generate a secrets.toml file."""

    client_id: str
    client_secret: str
    redirect_uri: str
    cookie_secret: str = None

    def __post_init__(self):
        """Initialize default values after initialization."""
        if self.cookie_secret is None:
            self.cookie_secret = secrets.token_urlsafe(COOKIE_SECRET_LENGTH)

    @staticmethod
    def first_non_localhost_uri(uris: List[str]) -> Optional[str]:
        """Return the first URI that doesn't start with 'http://localhost'.

        Uses lazy evaluation with a generator expression.

        Args:
            uris: List of redirect URIs.

        Returns:
            The first non-localhost URI or None if none found.
        """
        return next(
            (uri for uri in uris if not uri.startswith("http://localhost")), None
        )

    @classmethod
    def from_oauth_data(cls, data: OAuthClientSecrets) -> Self:
        """Create a SecretsTomlData instance from OAuth client secrets data.

        Args:
            data: The parsed OAuth client secrets data.

        Returns:
            A new instance with data extracted from the data.

        Raises:
            ValueError: If no non-localhost redirect URI is found.
        """
        redirect_uri = cls.first_non_localhost_uri(data.web.redirect_uris)

        if not redirect_uri:
            raise ValueError("No non-localhost redirect URI in client secrets file")

        return cls(
            client_id=data.web.client_id,
            client_secret=data.web.client_secret,
            redirect_uri=redirect_uri,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for template formatting."""
        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "cookie_secret": self.cookie_secret,
        }


def process_client_secrets(input_path: Path, output_path: Path) -> None:
    """Process client secrets file and write TOML config.

    Args:
        input_path: Path to the client secrets JSON file.
        output_path: Path where the TOML file will be written.

    Raises:
        FileNotFoundError: If the client secrets file does not exist.
        ValueError: If the JSON structure is not as expected or missing required data.
        OSError: If directory creation or file writing fails.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Client secrets file not found at {input_path}")

    # Warn and confirm before overwriting an existing output file.
    if output_path.exists():
        print(
            f"\n\033[93mWARNING: File already exists at {output_path}.\n"
            "Overwriting will generate a new cookie_secret value "
            "and invalidate existing user sessions.\033[0m",
            file=sys.stderr,
        )

        response = input("\nContinue and overwrite the file? [y/N] ").lower()
        if response != "y":
            print("\n❌ Operation cancelled.\n", file=sys.stderr)
            return

    try:
        with input_path.open("r") as f:
            json_data = json.load(f)

        oauth_client_data = OAuthClientSecrets.from_dict(json_data)
        secrets_toml_data = SecretsTomlData.from_oauth_data(oauth_client_data)
        secrets_toml_content = SECRETS_TOML_TEMPLATE.format(
            **secrets_toml_data.to_dict()
        )

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in client secrets file: {e}") from e

    # Create directories if needed.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write output file.
    output_path.write_text(secrets_toml_content)

    print(f"\n\033[92m✅ Success!\n\n{output_path.absolute()}\n\033[0m")

    return


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate Streamlit secrets.toml file from OAuth client secrets JSON."
    )
    parser.add_argument(
        "input_path",
        type=Path,
        help="Path to the OAuth client secrets JSON file.",
    )
    parser.add_argument(
        "-o",
        "--output-path",
        default=DEFAULT_OUTPUT_PATH,
        type=Path,
        help=f"Path where secrets TOML file will be written (default: {DEFAULT_OUTPUT_PATH})",
    )
    return parser.parse_args()


def run() -> None:
    """Generate Streamlit secrets.toml file from OAuth client secrets JSON."""
    args = parse_args()

    # Verify input file exists
    if not args.input_path.exists():
        print(f"Error: Input file not found at {args.input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Processing client secrets file: {args.input_path}")
    try:
        process_client_secrets(input_path=args.input_path, output_path=args.output_path)
    except Exception as e:
        print(f"\033[91mError: {e}\033[0m", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
