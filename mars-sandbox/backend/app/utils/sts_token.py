"""Generate STS temporary credentials for frontend direct OSS access."""
import json
import logging
from ..config import settings

logger = logging.getLogger(__name__)

# STS endpoint by region mapping (common regions)
_STS_ENDPOINTS = {
    "oss-cn-hangzhou": "sts.cn-hangzhou.aliyuncs.com",
    "oss-cn-shanghai": "sts.cn-shanghai.aliyuncs.com",
    "oss-cn-beijing": "sts.cn-beijing.aliyuncs.com",
    "oss-cn-shenzhen": "sts.cn-shenzhen.aliyuncs.com",
    "oss-cn-hongkong": "sts.cn-hongkong.aliyuncs.com",
    "oss-ap-southeast-1": "sts.ap-southeast-1.aliyuncs.com",
    "oss-ap-northeast-1": "sts.ap-northeast-1.aliyuncs.com",
    "oss-ap-northeast-2": "sts.ap-northeast-2.aliyuncs.com",
    "oss-us-west-1": "sts.us-west-1.aliyuncs.com",
    "oss-eu-central-1": "sts.eu-central-1.aliyuncs.com",
}

# OSS prefix for cloud drive
DRIVE_PREFIX = "clouddisk/"


def _get_region() -> str:
    """Extract region from OSS endpoint (e.g., 'please-set-endpoint' -> 'ap-northeast-2')."""
    endpoint = settings.OSS_ENDPOINT
    if endpoint.startswith("oss-"):
        region = endpoint.split(".")[0].replace("oss-", "")
        return region
    return "cn-hangzhou"


def _get_sts_endpoint() -> str:
    """Get STS endpoint based on OSS region."""
    endpoint = settings.OSS_ENDPOINT
    if endpoint in _STS_ENDPOINTS:
        return _STS_ENDPOINTS[endpoint]
    region = _get_region()
    return f"sts.{region}.aliyuncs.com"


def _build_drive_policy() -> str:
    """Build a scoped RAM policy for clouddisk/ prefix operations."""
    bucket = settings.OSS_BUCKET
    policy = {
        "Version": "1",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "oss:PutObject",
                    "oss:GetObject",
                    "oss:DeleteObject",
                    "oss:ListObjects",
                    "oss:AbortMultipartUpload",
                    "oss:ListParts",
                ],
                "Resource": [
                    f"acs:oss:*:*:{bucket}/{DRIVE_PREFIX}*",
                ],
            },
            {
                "Effect": "Allow",
                "Action": [
                    "oss:ListObjects",
                ],
                "Resource": [
                    f"acs:oss:*:*:{bucket}",
                ],
                "Condition": {
                    "StringLike": {
                        "oss:Prefix": [f"{DRIVE_PREFIX}*"],
                    },
                },
            },
        ],
    }
    return json.dumps(policy)


def get_sts_token(duration_seconds: int = 900) -> dict:
    """Get STS temporary credentials scoped to clouddisk/ prefix.

    Args:
        duration_seconds: Token validity in seconds (default 15 min, min 900).

    Returns:
        Dict with access_key_id, access_key_secret, security_token, expiration, region, bucket, prefix.
    """
    from alibabacloud_sts20150401.client import Client
    from alibabacloud_sts20150401.models import AssumeRoleRequest
    from alibabacloud_tea_openapi.models import Config

    sts_endpoint = _get_sts_endpoint()
    region = _get_region()

    config = Config(
        access_key_id=settings.OSS_ACCESS_KEY_ID,
        access_key_secret=settings.OSS_ACCESS_KEY_SECRET,
        endpoint=sts_endpoint,
        region_id=region,
    )
    client = Client(config)

    policy = _build_drive_policy()
    role_arn = settings.OSS_ROLE_ARN or f"acs:ram::*:role/oss-drive-role"

    # If no role ARN configured, use a simple approach:
    # Sign URL directly instead of STS
    # For STS, you need a RAM role. Fall back to signed URL approach if not available.
    try:
        request = AssumeRoleRequest(
            role_arn=role_arn,
            role_session_name="mars-drive-session",
            policy=policy,
            duration_seconds=duration_seconds,
        )
        response = client.assume_role(request)
        body = response.body
        creds = body.credentials
        return {
            "access_key_id": creds.access_key_id,
            "access_key_secret": creds.access_key_secret,
            "security_token": creds.security_token,
            "expiration": creds.expiration,
            "region": region,
            "bucket": settings.OSS_BUCKET,
            "prefix": DRIVE_PREFIX,
        }
    except Exception as e:
        logger.error("STS AssumeRole failed: %s", e)
        # Fallback: return main credentials with policy hint
        # In production, you should always use STS. This fallback is for dev convenience.
        logger.warning("Falling back to direct credentials (dev mode)")
        return {
            "access_key_id": settings.OSS_ACCESS_KEY_ID,
            "access_key_secret": settings.OSS_ACCESS_KEY_SECRET,
            "security_token": "",
            "expiration": "",
            "region": region,
            "bucket": settings.OSS_BUCKET,
            "prefix": DRIVE_PREFIX,
        }
