from fastapi import APIRouter, HTTPException, Path, status

from app.api.dependencies import AdminUser, DatabaseSession
from app.core.security import generate_api_key, hash_api_key
from app.models import ApiKey, Application
from app.schemas.api_keys import ApiKeyCreate, ApiKeyCreatedResponse

router = APIRouter(prefix="/admin/applications", tags=["admin-api-keys"])


@router.post(
    "/{application_id}/api-keys",
    response_model=ApiKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_api_key(
    api_key_data: ApiKeyCreate,
    session: DatabaseSession,
    admin_user: AdminUser,
    application_id: int = Path(gt=0),
) -> ApiKeyCreatedResponse:
    application = session.get(Application, application_id)
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    plain_api_key = generate_api_key()
    key_prefix = plain_api_key[:12]
    api_key = ApiKey(
        application_id=application.id,
        name=api_key_data.name.strip(),
        key_prefix=key_prefix,
        key_hash=hash_api_key(plain_api_key),
        created_by_user_id=admin_user.id,
    )
    session.add(api_key)
    session.commit()
    session.refresh(api_key)

    return ApiKeyCreatedResponse(
        id=api_key.id,
        application_id=api_key.application_id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        api_key=plain_api_key,
        created_at=api_key.created_at,
    )
