import google.auth
import google.auth.transport.requests
from google.auth import impersonated_credentials


def get_impersonated_id_token(
    target_principal: str, target_scopes: list, audience: str
) -> str:
    """Use Service Account Impersonation to generate a token for authorized requests.
    Caller must have the “Service Account Token Creator” role on the target service account.
    Args:
        target_principal: The Service Account email address to impersonate.
        target_scopes: List of auth scopes for the Service Account.
        audience: the URI of the Google Cloud resource to access with impersonation.
    Returns: Open ID Connect ID Token-based service account credentials bearer token
    that can be used in HTTP headers to make authenticated requests.
    refs:
    https://cloud.google.com/docs/authentication/get-id-token#impersonation
    https://cloud.google.com/iam/docs/create-short-lived-credentials-direct#user-credentials_1
    https://stackoverflow.com/questions/74411491/python-equivalent-for-gcloud-auth-print-identity-token-command
    https://googleapis.dev/python/google-auth/latest/reference/google.auth.impersonated_credentials.html
    """
    # Get ADC for the caller (a Google user account).
    creds, project = google.auth.default()

    # Create impersonated credentials.
    target_creds = impersonated_credentials.Credentials(
        source_credentials=creds,
        target_principal=target_principal,
        target_scopes=target_scopes,
    )

    # Use impersonated creds to fetch and refresh an access token.
    request = google.auth.transport.requests.Request()
    id_creds = impersonated_credentials.IDTokenCredentials(
        target_credentials=target_creds, target_audience=audience, include_email=True
    )
    id_creds.refresh(request)

    return id_creds.token
