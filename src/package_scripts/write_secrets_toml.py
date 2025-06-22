import json
import secrets
from pathlib import Path
from typing import Annotated, Self

import click
from pydantic import BaseModel, Field

DEFAULT_SECRETS_DIR: Path = Path(".streamlit/secrets")
DEFAULT_OUTPUT_PATH: Path = DEFAULT_SECRETS_DIR / "secrets.toml"
COOKIE_SECRET_LENGTH: int = 32
SECRETS_TOML_TEMPLATE: str = """[auth]
### Override default serving port 8501 to 8080 in config.toml
redirect_uri = "{redirect_uri}"
cookie_secret = "{cookie_secret}"

[auth.google]
client_id = "{client_id}"
client_secret = "{client_secret}"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
client_kwargs = {{ "access_type" = "online", "prompt" = "select_account" }}

#### Refs
# https://docs.streamlit.io/develop/api-reference/user/st.login
# https://developers.google.com/identity/openid-connect/openid-connect
# https://developers.google.com/identity/protocols/oauth2/web-server
# https://support.google.com/cloud/answer/15549257
"""


class WebConfig(BaseModel):
    """Pydantic model for the 'web' section of OAuth client secrets."""

    client_id: str
    client_secret: str
    redirect_uris: list[str]


class OAuthClientSecrets(BaseModel):
    """Pydantic model for OAuth client secrets JSON structure."""

    web: WebConfig


class SecretsTomlData(BaseModel):
    """Pydantic model for the data needed to generate a secrets.toml file."""

    client_id: Annotated[
        str,
        Field(description="OAuth client ID"),
    ]
    client_secret: Annotated[
        str,
        Field(description="OAuth client secret"),
    ]
    redirect_uri: Annotated[
        str,
        Field(description="localhost redirect URI for OAuth flow"),
    ]
    cookie_secret: Annotated[
        str,
        Field(description="Random secret for cookie encryption"),
    ] = secrets.token_urlsafe(COOKIE_SECRET_LENGTH)

    @staticmethod
    def first_localhost_uri(uris: list[str]) -> str | None:
        """Return the first URI that starts with 'http://localhost'.

        Uses lazy evaluation with a generator expression.

        Args:
            uris: List of redirect URIs.

        Returns:
            The first non-localhost URI or None if none found.
        """
        return next((uri for uri in uris if uri.startswith("http://localhost")), None)

    @classmethod
    def from_oauth_data(cls, data: OAuthClientSecrets) -> Self:
        """Create a SecretsTomlData instance from OAuth client secrets data.

        Args:
            data: The parsed OAuth client secrets data.

        Returns:
            A new instance with data extracted from the JSON.

        Raises:
            ValueError: If no localhost redirect URI is found.
        """
        redirect_uri: str | None = cls.first_localhost_uri(data.web.redirect_uris)

        if not redirect_uri:
            raise ValueError("No localhost redirect URI in client secrets file")

        return cls(
            client_id=data.web.client_id,
            client_secret=data.web.client_secret,
            redirect_uri=redirect_uri,
        )


def find_client_secrets_file(path: Path = DEFAULT_SECRETS_DIR) -> Path:
    """Find client secrets JSON file in the directory, prioritizing 'client_secret' in name.

    Args:
        path: pathlib.Path to the directory containing JSON files.

    Returns:
        pathlib.Path to the first JSON file found in the directory.

    Raises:
        click.ClickException: If no JSON files are found in the directory.
    """
    json_files = sorted(path.glob("*.json"))
    if not json_files:
        raise click.ClickException(f"No JSON files found in {path}")

    # Prioritize files with 'client_secret' in the name.
    for file in json_files:
        if "client_secret" in file.name:
            return file

    # Fall back to first JSON file.
    return json_files[0]


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
        click.secho(
            (
                f"\nWARNING: File already exists at {output_path}.\n"
                "Overwriting will generate a new cookie_secret value "
                "and invalidate existing user sessions."
            ),
            fg="yellow",
            bold=True,
        )

        if not click.confirm("\nContinue and overwrite the file?", default=False):
            click.secho("\n❌ Operation cancelled.\n", bold=True)
            return

    try:
        input_file_content: str = input_path.read_text()
        oauth_client_data = OAuthClientSecrets.model_validate_json(input_file_content)
        secrets_toml_data = SecretsTomlData.from_oauth_data(oauth_client_data)
        secrets_toml_content: str = SECRETS_TOML_TEMPLATE.format(
            **secrets_toml_data.model_dump()
        )

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in client secrets file: {e}") from e

    # Create directories if needed.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write output file.
    output_path.write_text(secrets_toml_content)

    click.secho(
        f"\n✅ Success!\n\n{output_path.absolute()}\n",
        fg="green",
        bold=True,
    )

    return


@click.command(
    help="Generate Streamlit secrets.toml file from OAuth client secrets JSON."
)
@click.option(
    "--input-path",
    "-i",
    type=Path,
    help=f"Path to OAuth client secrets JSON file (defaults to auto-detection in {DEFAULT_SECRETS_DIR}).",
)
@click.option(
    "--output-path",
    "-o",
    default=DEFAULT_OUTPUT_PATH,
    type=Path,
    help=f"Path where secrets TOML file will be written (default: {DEFAULT_OUTPUT_PATH}).",
)
def run(input_path: Path | None, output_path: Path) -> None:
    """Generate Streamlit secrets.toml file from OAuth client secrets JSON."""
    # Find the client secrets JSON file if no input path provided.
    if input_path is None:
        input_path = find_client_secrets_file()
        click.echo(f"Auto-selecting client secrets file: {input_path}")
    else:
        click.echo(f"Processing client secrets file: {input_path}")

    try:
        process_client_secrets(input_path=input_path, output_path=output_path)
    except Exception as e:
        click.secho(f"Error: {e}", fg="red", bold=True)
        raise click.Abort() from e
