from fastapi import Depends, HTTPException, status

from app.security.dependencies import get_current_user


def require_role(required_role_id: int):

    def role_checker(current_user=Depends(get_current_user)):

        if current_user["role_id"] != required_role_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action"
            )

        return current_user

    return role_checker


def require_any_role(allowed_role_ids: list[int]):

    def role_checker(current_user=Depends(get_current_user)):

        if current_user["role_id"] not in allowed_role_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action"
            )

        return current_user

    return role_checker
